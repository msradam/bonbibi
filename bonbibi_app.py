"""Bonbibi's UI backend: a small FastAPI app that owns the run pipeline
(GPU flood frames -> routes -> Granite narration with the GPU looping)
and serves the accessible console UI plus the offline map assets.

Runs ON the Pi:

    /root/demo-venv/bin/uvicorn bonbibi_app:app --host 0.0.0.0 --port 8500

Narration needs a resident llama-server (model loads once, guidance
streams immediately; --jinja enables Granite's chat template so route
facts pass as grounded documents via chat_template_kwargs):

    GGML_VK_VISIBLE_DEVICES=99 llama-server -m granite-4.0-1b-Q4_0.gguf \
        -ngl 0 -t 4 -c 4096 --jinja --host 127.0.0.1 --port 8081

The UI polls GET /api/state; the map (static/map.html) polls
static/live/state.json exactly as before. One run at a time.
"""

import glob
import json
import urllib.request
import os
import re
import subprocess
import threading
import time

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel

RES = "/root/v3d-research"
SZ = 256
GRID = 16
LIVE = f"{RES}/static/live"
UI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")
VKFLOOD_ENV = {"STRIP": "2", "FUSED": "1", "FLUX_SPV": "fused2s.spv"}
LLAMA_BIN = f"{RES}/llama.cpp/build-vulkan/bin/llama-completion"
TIME_RE = re.compile(r"time=([0-9.]+)s")
CELL_RE = re.compile(r"\(r(\d+),c(\d+)\)")

app = FastAPI(title="Bonbibi")
os.makedirs(LIVE, exist_ok=True)

RUN: dict = {"running": False, "phase": "idle", "done": False}
_lock = threading.Lock()


class RunParams(BaseModel):
    dem: str
    rain: float = 0.003
    steps: int = 400
    frames: int = 5


def dem_bbox(dem_path: str):
    with open(dem_path) as f:
        _, la0, la1, lo0, lo1 = f.readline().split()
    return float(la0), float(la1), float(lo0), float(lo1)


def run_flood(steps: int, rain: float, dem: str, dump: str | None = None) -> str:
    env = {**os.environ, **VKFLOOD_ENV, "DEM": dem, "RAIN": str(rain)}
    if dump:
        env["DUMP_FULL"] = dump
    p = subprocess.run(
        ["./vkflood2", str(SZ), str(steps), "sim"],
        cwd=RES,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return p.stdout


def band_coverage(water: np.ndarray) -> dict:
    n = water.size
    return {
        "shallow_pct": round(
            100.0 * np.count_nonzero((water >= 0.05) & (water < 0.5)) / n, 1
        ),
        "vehicle_pct": round(
            100.0 * np.count_nonzero((water >= 0.5) & (water < 2.0)) / n, 1
        ),
        "deep_pct": round(100.0 * np.count_nonzero(water >= 2.0) / n, 1),
        "max_depth_m": round(float(water.max()), 2),
    }


def publish(bbox, water: np.ndarray | None, routes: dict | None):
    la0, la1, lo0, lo1 = bbox
    state = {
        "v": time.time_ns(),
        "flood": water is not None,
        "corners": [[lo0, la1], [lo1, la1], [lo1, la0], [lo0, la0]],
        "routes": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"profile": name},
                    "geometry": {"type": "LineString", "coordinates": coords},
                }
                for name, coords in (routes or {}).items()
                if coords
            ],
        },
    }
    if water is not None:
        rgba = np.zeros((*water.shape, 4), dtype=np.uint8)
        rgba[(water >= 0.05) & (water < 0.5)] = (66, 165, 245, 110)
        rgba[(water >= 0.5) & (water < 2.0)] = (30, 90, 200, 165)
        rgba[water >= 2.0] = (69, 39, 160, 205)
        Image.fromarray(rgba).save(f"{LIVE}/depth.png.tmp", format="PNG")
        os.replace(f"{LIVE}/depth.png.tmp", f"{LIVE}/depth.png")
    with open(f"{LIVE}/state.json.tmp", "w") as f:
        json.dump(state, f)
    os.replace(f"{LIVE}/state.json.tmp", f"{LIVE}/state.json")


def route(threshold: float, bbox):
    p = subprocess.run(
        ["python3", "route.py", str(threshold)],
        cwd=RES,
        capture_output=True,
        text=True,
        timeout=60,
    )
    out = p.stdout.strip()
    summary = out.splitlines()[0] if out else "(no route output)"
    la0, la1, lo0, lo1 = bbox
    coords = [
        [
            lo0 + (lo1 - lo0) * (int(c) + 0.5) / GRID,
            la1 - (la1 - la0) * (int(r) + 0.5) / GRID,
        ]
        for r, c in CELL_RE.findall(out)
    ]
    return summary, coords


def guidance_text(raw: str) -> str:
    return (
        raw.rsplit("assistant", 1)[-1].split("EOF by user")[0].strip().rstrip("> \n")
        if "assistant" in raw
        else raw.strip()
    )


def gpu_loop(stop: threading.Event, rain: float, dem: str):
    while not stop.is_set():
        out = run_flood(4000, rain, dem)
        m = TIME_RE.search(out)
        if m:
            with _lock:
                RUN["gpu_runs"] += 1
                RUN["gpu_steps"] += 4000
                RUN["gpu_sps"] = round(4000.0 / float(m.group(1)))


def do_run(p: RunParams):
    bbox = dem_bbox(p.dem)
    area = os.path.basename(p.dem).replace("dem_", "").replace(".txt", "")
    try:
        with _lock:
            RUN.update(phase="flood", frame=0, frames=p.frames)
        water = None
        for i in range(1, p.frames + 1):
            n = max(1, p.steps * i // p.frames)
            run_flood(n, p.rain, p.dem, dump="/tmp/demo_depth.bin")
            water = np.fromfile("/tmp/demo_depth.bin", dtype=np.float32).reshape(SZ, SZ)
            publish(bbox, water, None)
            with _lock:
                RUN.update(frame=i, coverage=band_coverage(water))
            time.sleep(0.4)

        with _lock:
            RUN["phase"] = "routing"
        wheel_txt, wheel_path = route(0.5, bbox)
        car_txt, car_path = route(2.0, bbox)
        publish(bbox, water, {"wheelchair": wheel_path, "vehicle": car_path})
        with _lock:
            RUN["routes"] = {
                "wheelchair": {"summary": wheel_txt, "possible": bool(wheel_path)},
                "vehicle": {"summary": car_txt, "possible": bool(car_path)},
            }

        with _lock:
            cov = RUN.get("coverage") or {}
            RUN["phase"] = "narrating"
        docs = [
            {
                "doc_id": 1,
                "title": f"Flood assessment for {area}",
                "text": (
                    f"Simulated storm over {area}: rain {p.rain} m per cell per "
                    f"step for {p.steps} steps. Deepest water {cov.get('max_depth_m', '?')} m. "
                    f"Coverage: {cov.get('shallow_pct', '?')}% of the area under shallow "
                    f"water below 0.5 m (passable for everyone), "
                    f"{cov.get('vehicle_pct', '?')}% between 0.5 and 2 m (vehicles only), "
                    f"{cov.get('deep_pct', '?')}% deeper than 2 m (impassable)."
                ),
            },
            {
                "doc_id": 2,
                "title": "Route result: wheelchair user (limit 0.5 m)",
                "text": f"The routing engine computed: {wheel_txt}. "
                + (
                    "Recommended action: a safe crossing exists, so leave now "
                    "while the route is open; conditions can worsen quickly."
                    if wheel_path
                    else "Recommended action: there is no safe route, so stay "
                    "where you are, move to the highest point nearby, signal "
                    "for help, and do not enter the water."
                ),
            },
            {
                "doc_id": 3,
                "title": "Route result: vehicle (limit 2.0 m)",
                "text": f"The routing engine computed: {car_txt}. "
                + (
                    "Recommended action: a safe crossing exists, so drive it "
                    "now while the route is open; never drive into water of "
                    "unknown depth."
                    if car_path
                    else "Recommended action: there is no safe route, so do "
                    "not drive; stay where you are and signal for help."
                ),
            },
        ]
        payload = {
            "stream": True,
            "temperature": 0,
            "max_tokens": 180,
            "chat_template_kwargs": {"documents": docs},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Bonbibi, an emergency flood-guidance assistant. "
                        "Use plain, calm language a person in an emergency can "
                        "follow. Never invent street names, places, or facts."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Based only on the documents, write three short "
                        "sentences: first, what the wheelchair user should do "
                        "right now given their route result; second, what the "
                        "driver should do right now given their route result; "
                        "third, one safety note from the flood assessment."
                    ),
                },
            ],
        }
        stop = threading.Event()
        threading.Thread(
            target=gpu_loop, args=(stop, p.rain, p.dem), daemon=True
        ).start()
        req = urllib.request.Request(
            "http://127.0.0.1:8081/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=300) as r:
            for raw in r:
                line = raw.decode(errors="replace").strip()
                if not line.startswith("data: ") or line == "data: [DONE]":
                    continue
                delta = json.loads(line[6:])["choices"][0].get("delta", {})
                piece = delta.get("content") or ""
                if piece:
                    with _lock:
                        RUN["guidance"] = (RUN.get("guidance") or "") + piece
        stop.set()
        with _lock:
            RUN.update(phase="done", done=True)
    except Exception as e:
        with _lock:
            RUN.update(phase="error", error=str(e)[:300], done=True)
    finally:
        with _lock:
            RUN["running"] = False


@app.get("/")
def index():
    return FileResponse(os.path.join(UI, "index.html"))


@app.get("/api/areas")
def areas():
    out = []
    for d in sorted(glob.glob(f"{RES}/dem_*.txt")):
        name = os.path.basename(d).replace("dem_", "").replace(".txt", "")
        la0, la1, lo0, lo1 = dem_bbox(d)
        out.append(
            {
                "name": name,
                "dem": d,
                "bbox": [lo0, la0, lo1, la1],
                "basemap": os.path.exists(f"{RES}/static/{name}.pmtiles"),
            }
        )
    return out


@app.post("/api/run", status_code=202)
def start_run(p: RunParams):
    with _lock:
        if RUN.get("running"):
            raise HTTPException(status_code=409, detail="A storm is already running.")
        RUN.clear()
        RUN.update(
            running=True,
            phase="starting",
            done=False,
            frame=0,
            frames=p.frames,
            routes=None,
            guidance="",
            coverage=None,
            gpu_runs=0,
            gpu_steps=0,
            gpu_sps=0,
            started=time.time(),
        )
    threading.Thread(target=do_run, args=(p,), daemon=True).start()
    return {"ok": True}


@app.get("/api/state")
def state():
    with _lock:
        s = dict(RUN)
    s["elapsed"] = round(time.time() - s["started"]) if s.get("started") else 0
    return s


app.mount("/app/static", StaticFiles(directory=f"{RES}/static"), name="static")
app.mount("/ui", StaticFiles(directory=UI), name="ui")
