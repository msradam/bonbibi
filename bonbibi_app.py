"""Bonbibi's UI backend: a small FastAPI app that owns the run pipeline
(GPU flood frames -> routes -> Granite narration with the GPU looping)
and serves the accessible console UI plus the offline map assets.

Runs ON the Pi:

    /root/demo-venv/bin/uvicorn bonbibi_app:app --host 0.0.0.0 --port 8500

Narration needs a resident llama-server (model loads once, guidance
streams immediately; --jinja enables Granite's chat template so route
facts pass as grounded documents via chat_template_kwargs):

    GGML_VK_VISIBLE_DEVICES=99 llama-server -m granite-4.1-3b-Q4_0.gguf \
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
import routing
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
# Mobility thresholds: limiting STILL-WATER depths from ARR Project 10 and
# AIDR Guideline 7-3 (see HACKATHON.md for quotes). Wheelchair/limited
# mobility: no safe flow regime is documented for frail or disabled persons,
# so only nuisance depth is allowed. On foot: 0.5 m is ARR's depth ceiling
# for children, adopted as the conservative walking limit because the
# simulation does not model velocity (able-bodied adult ceiling is 1.2 m).
# Vehicle: 0.3 m is the floating depth of a small passenger car (AIDR H1/H2
# boundary). Note vehicles become unsafe BEFORE pedestrians.
THRESHOLDS = {"wheelchair": 0.1, "foot": 0.5, "vehicle": 0.3}
BANDS = (0.05, 0.3, 0.5, 1.2)  # AIDR hazard classes H1 | H2 | H3 | H4+

TIME_RE = re.compile(r"time=([0-9.]+)s")

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
    lo, h1, h2, h3 = BANDS
    return {
        "h1_pct": round(100.0 * np.count_nonzero((water >= lo) & (water < h1)) / n, 1),
        "h2_pct": round(100.0 * np.count_nonzero((water >= h1) & (water < h2)) / n, 1),
        "h3_pct": round(100.0 * np.count_nonzero((water >= h2) & (water < h3)) / n, 1),
        "h4_pct": round(100.0 * np.count_nonzero(water >= h3) / n, 1),
        "max_depth_m": round(float(water.max()), 2),
    }


def publish(
    bbox, water: np.ndarray | None, routes: dict | None, origin=None, shelters=None
):
    la0, la1, lo0, lo1 = bbox
    state = {
        "v": time.time_ns(),
        "flood": water is not None,
        "origin": origin,
        "shelters": shelters or [],
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
        lo, h1, h2, h3 = BANDS
        rgba[(water >= lo) & (water < h1)] = (144, 202, 249, 100)
        rgba[(water >= h1) & (water < h2)] = (66, 165, 245, 130)
        rgba[(water >= h2) & (water < h3)] = (30, 90, 200, 170)
        rgba[water >= h3] = (69, 39, 160, 205)
        Image.fromarray(rgba).save(f"{LIVE}/depth.png.tmp", format="PNG")
        os.replace(f"{LIVE}/depth.png.tmp", f"{LIVE}/depth.png")
    with open(f"{LIVE}/state.json.tmp", "w") as f:
        json.dump(state, f)
    os.replace(f"{LIVE}/state.json.tmp", f"{LIVE}/state.json")


def load_shelters(area: str) -> list:
    path = f"{RES}/static/shelters_{area}.json"
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def shelter_status(shelters: list, depth, bbox) -> list:
    out = []
    for s in shelters:
        r, c = routing.to_cell(s["lat"], s["lon"], bbox)
        d = float(depth[r * routing.SZ + c]) if depth is not None else 0.0
        out.append({**s, "depth_m": round(d, 2), "flooded": d > 0.05})
    return out


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


LAST: dict = {}

ADVISORY_INSTRUCTION = (
    "Write a short area advisory based only on the documents, addressed "
    "to residents by capability: one sentence for people who cannot wade "
    "(wheelchair users and others), one for drivers, one on shelters, "
    "using the water depths and coverage from the documents."
)

PERSON_INSTRUCTION = (
    "Write four short sentences based only on the documents: what this "
    "person should do right now if they use a wheelchair or cannot wade; "
    "what to do if they are on foot; what to do if they can drive; and one "
    "safety note from the flood assessment. Use each route result."
)


THRESHOLDS_DOC = {
    "doc_id": 1,
    "title": "Mobility safety limits (still water)",
    "text": (
        "Vehicles are unsafe in water above 0.3 m (cars float). Walking is "
        "unsafe above 0.5 m. Wheelchair users and people who cannot wade are "
        "unsafe in any standing water above 0.1 m. Able-bodied adults must "
        "never enter water above 1.2 m."
    ),
}


def flood_doc(area, rain, steps, cov) -> dict:
    return {
        "doc_id": 2,
        "title": f"Flood assessment for {area}",
        "text": (
            f"Simulated storm over {area}: rain {rain} m per cell per "
            f"step for {steps} steps. Deepest water {cov.get('max_depth_m', '?')} m. "
            f"Coverage: {cov.get('h1_pct', '?')}% under shallow water below 0.3 m, "
            f"{cov.get('h2_pct', '?')}% at 0.3 to 0.5 m (unsafe for vehicles), "
            f"{cov.get('h3_pct', '?')}% at 0.5 to 1.2 m (unsafe on foot except "
            f"able-bodied adults), and {cov.get('h4_pct', '?')}% above 1.2 m "
            f"(unsafe for everyone). This is a simulation, not an observation."
        ),
    }


def narrate(docs: list, instruction: str):
    """Stream Granite's grounded composition into RUN['guidance']."""
    payload = {
        "stream": True,
        "temperature": 0,
        "max_tokens": 240,
        "chat_template_kwargs": {"documents": docs},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Bonbibi, an emergency flood-guidance assistant. "
                    "Write plain sentences without markdown, bold, or headings. "
                    "Use plain, calm language a person in an emergency can "
                    "follow. Never invent street names, places, or facts."
                ),
            },
            {"role": "user", "content": instruction},
        ],
    }
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


def do_run(p: RunParams):
    bbox = dem_bbox(p.dem)
    area = os.path.basename(p.dem).replace("dem_", "").replace(".txt", "")
    try:
        with _lock:
            RUN.update(phase="flood", frame=0, frames=p.frames)
        water = None
        area_shelters = load_shelters(area)
        for i in range(1, p.frames + 1):
            n = max(1, p.steps * i // p.frames)
            run_flood(n, p.rain, p.dem, dump="/tmp/demo_depth.bin")
            water = np.fromfile("/tmp/demo_depth.bin", dtype=np.float32).reshape(SZ, SZ)
            publish(
                bbox,
                water,
                None,
                shelters=shelter_status(area_shelters, water.reshape(-1), bbox),
            )
            with _lock:
                RUN.update(frame=i, coverage=band_coverage(water))
            time.sleep(0.4)

        with _lock:
            RUN["phase"] = "routing"
        depth = water.reshape(-1)
        shelters = shelter_status(area_shelters, depth, bbox)
        dry = sum(1 for s in shelters if not s["flooded"])
        publish(bbox, water, None, shelters=shelters)
        LAST.update(
            depth=depth,
            bbox=bbox,
            area=area,
            shelters=shelters,
            rain=p.rain,
            steps=p.steps,
        )
        with _lock:
            RUN["shelters"] = {"total": len(shelters), "dry": dry}
            RUN["routes"] = None

        with _lock:
            cov = RUN.get("coverage") or {}
            RUN["phase"] = "narrating"
        docs = [
            THRESHOLDS_DOC,
            flood_doc(area, p.rain, p.steps, cov),
            {
                "doc_id": 3,
                "title": f"Shelter status in {area}",
                "text": (
                    "No shelter candidates are known for this area."
                    if not shelters
                    else f"All {len(shelters)} known shelter candidates are standing in floodwater."
                    if dry == 0
                    else f"All {len(shelters)} known shelter candidates are on dry ground."
                    if dry == len(shelters)
                    else f"{dry} of {len(shelters)} known shelter candidates are on dry "
                    f"ground; the other {len(shelters) - dry} are standing in floodwater."
                ),
            },
        ]
        stop = threading.Event()
        threading.Thread(
            target=gpu_loop, args=(stop, p.rain, p.dem), daemon=True
        ).start()
        narrate(docs, ADVISORY_INSTRUCTION)
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


class LocateParams(BaseModel):
    lat: float
    lon: float


@app.post("/api/locate")
def locate(q: LocateParams):
    with _lock:
        if RUN.get("running"):
            raise HTTPException(
                status_code=409, detail="A storm is running; wait for it."
            )
    if LAST.get("depth") is None:
        raise HTTPException(status_code=400, detail="Run a storm first.")
    depth, bbox, area = LAST["depth"], LAST["bbox"], LAST["area"]
    shelters = LAST["shelters"]
    if not shelters:
        raise HTTPException(
            status_code=400, detail=f"No shelter candidates known for {area}."
        )
    origin = routing.to_cell(q.lat, q.lon, bbox)
    goals = [routing.to_cell(s["lat"], s["lon"], bbox) for s in shelters]
    here_depth = float(depth[origin[0] * routing.SZ + origin[1]])

    results, paths, docs = {}, {}, []
    for name, thr in THRESHOLDS.items():
        idx, path = routing.route_to_shelter(depth, thr, origin, goals)
        if idx is not None:
            s = shelters[idx]
            dist = routing.path_length_m(path, bbox)
            results[name] = {
                "possible": True,
                "shelter": s["name"],
                "kind": s["kind"],
                "distance_m": dist,
                "summary": f"Nearest reachable shelter: {s['name']} ({s['kind']}), about {dist} m away.",
            }
            paths[name] = [
                routing.to_lonlat(r, c, bbox) for r, c in path[::4] + [path[-1]]
            ]
            action = {
                "wheelchair": "Recommended action: a path avoiding standing "
                "water exists, so go now with assistance if possible; "
                "conditions can worsen quickly.",
                "foot": "Recommended action: a walkable path exists, so go "
                "now; never enter fast-moving water.",
                "vehicle": "Recommended action: a driveable path avoiding "
                "water above 0.3 m exists, so drive it now; never drive "
                "into water of unknown depth.",
            }[name]
            text = (
                f"From this person's location, the nearest shelter reachable "
                f"without crossing water deeper than {thr} m is {s['name']} "
                f"({s['kind']}), about {dist} m away. {action}"
            )
        else:
            results[name] = {
                "possible": False,
                "summary": f"No shelter is reachable without crossing water deeper than {thr} m.",
            }
            text = (
                f"No shelter is reachable from this person's location without "
                f"crossing water deeper than {thr} m; they are stranded for "
                f"this mobility profile. Recommended action: stay in place, "
                f"move to the highest point nearby, signal for help, and do "
                f"not enter the water."
            )
        docs.append(
            {
                "doc_id": len(docs) + 3,
                "title": f"Route result: {name} (limit {thr} m)",
                "text": text,
            }
        )
    docs.insert(
        0, flood_doc(area, LAST["rain"], LAST["steps"], band_coverage(LAST["depth"]))
    )
    docs.insert(0, THRESHOLDS_DOC)
    if here_depth > 0.05:
        docs.append(
            {
                "doc_id": len(docs) + 1,
                "title": "Water at this person's location",
                "text": f"The water at their own location is {here_depth:.2f} m deep right now.",
            }
        )

    publish(
        bbox,
        LAST["depth"].reshape(routing.SZ, routing.SZ),
        paths,
        origin=[q.lon, q.lat],
        shelters=shelters,
    )
    with _lock:
        RUN.update(
            running=True, phase="narrating", done=False, guidance="", routes=results
        )
    try:
        narrate(docs, PERSON_INSTRUCTION)
    finally:
        with _lock:
            RUN.update(phase="done", done=True, running=False)
    return {"ok": True, "routes": results}


def cap_alert(s: dict) -> dict | None:
    """CAP 1.2-shaped structured alert (status Exercise: simulated event)."""
    if not s.get("coverage") or not LAST.get("area"):
        return None
    cov = s["coverage"]
    la0, la1, lo0, lo1 = LAST["bbox"]
    sev = (
        "Extreme"
        if cov["h4_pct"] > 10
        else "Severe"
        if cov["h3_pct"] > 10
        else "Moderate"
    )
    return {
        "identifier": f"bonbibi-{LAST['area']}-{int(s.get('started', 0))}",
        "sender": "bonbibi-on-device",
        "sent": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "status": "Exercise",
        "msgType": "Alert",
        "scope": "Public",
        "info": {
            "category": "Met",
            "event": "Flood (simulated)",
            "urgency": "Immediate",
            "severity": sev,
            "certainty": "Likely",
            "headline": f"Simulated flood over {LAST['area']}: deepest water "
            f"{cov['max_depth_m']} m",
            "instruction": s.get("guidance") or "",
            "area": {
                "areaDesc": LAST["area"],
                "polygon": f"{la0},{lo0} {la1},{lo0} {la1},{lo1} {la0},{lo1} {la0},{lo0}",
            },
        },
    }


@app.get("/api/state")
def state():
    with _lock:
        s = dict(RUN)
    s["elapsed"] = round(time.time() - s["started"]) if s.get("started") else 0
    s["cap"] = cap_alert(s) if s.get("done") else None
    return s


app.mount("/app/static", StaticFiles(directory=f"{RES}/static"), name="static")
app.mount("/ui", StaticFiles(directory=UI), name="ui")
