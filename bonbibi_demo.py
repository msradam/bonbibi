"""Streamlit demo of the bonbibi split: the V3D GPU floods real terrain
while the CPU routes around the water and Granite narrates the route.

Runs ON the Pi, next to the flood harness and llama.cpp:

    /root/demo-venv/bin/streamlit run bonbibi_demo.py \
        --server.address 0.0.0.0 --server.port 8501 \
        --server.enableStaticServing true

The map is real cartography, fully offline: a Protomaps PMTiles extract
plus styling assets cached once by fetch_basemap.py, rendered by map.html
(a real page under ./static; MapLibre's worker pipeline does not survive
Streamlit's srcdoc iframes) and embedded via components.iframe. The demo
publishes flood depth (three mobility bands) and route lines to
static/live/, and the map polls and updates in place. Phase 2 streams
Granite's grounded guidance from the CPU while the GPU keeps simulating,
with live throughput for both halves of the board.
"""

import glob
import json
import os
import re
import subprocess
import threading
import time

import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

RES = "/root/v3d-research"
SZ = 256
GRID = 16
LIVE = f"{RES}/static/live"
VKFLOOD_ENV = {"STRIP": "2", "FUSED": "1", "FLUX_SPV": "fused2s.spv"}
LLAMA_BIN = f"{RES}/llama.cpp/build-vulkan/bin/llama-completion"
TIME_RE = re.compile(r"time=([0-9.]+)s")
CELL_RE = re.compile(r"\(r(\d+),c(\d+)\)")

st.set_page_config(page_title="bonbibi", page_icon="🌊", layout="wide")
os.makedirs(LIVE, exist_ok=True)


@st.cache_data
def dem_bbox(dem_path: str) -> tuple[float, float, float, float]:
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


def publish(bbox, water: np.ndarray | None, routes: dict | None):
    """Write the banded depth PNG + state.json that map.html polls."""
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


def route(threshold: float, bbox) -> tuple[str, list]:
    """Returns (summary line, [[lon, lat], ...] cell-centre path)."""
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


def gpu_loop(stats: dict, stop: threading.Event):
    while not stop.is_set():
        out = run_flood(4000, stats["rain"], stats["dem"])
        m = TIME_RE.search(out)
        if m:
            stats["runs"] += 1
            stats["steps"] += 4000
            stats["sps"] = 4000.0 / float(m.group(1))


def llm_reader(proc, buf: list):
    for chunk in iter(lambda: proc.stdout.read(64), b""):
        buf.append(chunk.decode(errors="replace"))


def guidance_text(raw: str) -> str:
    return (
        raw.rsplit("assistant", 1)[-1].split("EOF by user")[0].strip()
        if "assistant" in raw
        else raw.strip()
    )


st.title("bonbibi — one board, two engines")
st.caption(
    "Raspberry Pi 5, zero connectivity at runtime. The V3D GPU simulates "
    "flooding over real terrain (WCA2D, physics-gated kernel from seppa) "
    "while the four CPU cores route around the water and Granite 4.0 1B "
    "narrates the result. Basemap, elevation, model: all local."
)

with st.sidebar:
    st.header("Storm")
    dems = sorted(glob.glob(f"{RES}/dem_*.txt")) or [f"{RES}/dem_redhook.txt"]
    default = next((i for i, d in enumerate(dems) if "redhook" in d), 0)
    dem = st.selectbox(
        "Terrain (DEM)", dems, index=default, format_func=os.path.basename
    )
    rain = st.slider(
        "Rain (m per cell per step)", 0.001, 0.010, 0.003, 0.001, format="%.3f"
    )
    steps = st.slider("Simulation steps", 100, 1000, 400, 100)
    frames = st.slider("Animation frames", 2, 12, 5)
    go = st.button("Run the storm", type="primary", use_container_width=True)

bbox = dem_bbox(dem)
area = os.path.basename(dem).replace("dem_", "").replace(".txt", "")
if not os.path.exists(f"{RES}/static/{area}.pmtiles"):
    area = "redhook"
la0, la1, lo0, lo1 = bbox

left, right = st.columns([3, 2])
with left:
    components.iframe(
        f"/app/static/map.html?area={area}&bbox={lo0},{la0},{lo1},{la1}", height=650
    )
    status_slot = st.empty()
routes_slot = right.container()
llm_slot = right.empty()
m1, m2, m3 = st.columns(3)
gpu_metric, steps_metric, tok_metric = m1.empty(), m2.empty(), m3.empty()

if not os.path.exists(f"{LIVE}/state.json"):
    publish(bbox, None, None)

if go:
    status_slot.info("GPU: flooding the terrain...")
    water = None
    for i in range(1, frames + 1):
        n = max(1, steps * i // frames)
        run_flood(n, rain, dem, dump="/tmp/demo_depth.bin")
        water = np.fromfile("/tmp/demo_depth.bin", dtype=np.float32).reshape(SZ, SZ)
        publish(bbox, water, None)
        time.sleep(0.4)

    status_slot.info("CPU: routing two mobility profiles through the flood...")
    wheel_txt, wheel_path = route(0.5, bbox)
    car_txt, car_path = route(2.0, bbox)
    publish(bbox, water, {"wheelchair": wheel_path, "vehicle": car_path})
    with routes_slot:
        st.subheader("Routes (deterministic, CPU)")
        st.markdown(f"**Wheelchair (≤0.5 m):** {wheel_txt}")
        st.markdown(f"**Vehicle (≤2.0 m):** {car_txt}")

    prompt = (
        f"You are an emergency guidance assistant in a {area} flood. "
        f"A routing engine computed:\n"
        f"- Wheelchair user (can only cross water up to 0.5 m deep): {wheel_txt}\n"
        f"- Car (can cross water up to 2.0 m deep): {car_txt}\n"
        f"In 3 short sentences, tell the wheelchair user and the driver "
        f"what each should do right now."
    )
    model = glob.glob(f"{RES}/models/**/*ranite*4*.gguf", recursive=True)[0]

    stats = {"runs": 0, "steps": 0, "sps": 0.0, "rain": rain, "dem": dem}
    stop = threading.Event()
    threading.Thread(target=gpu_loop, args=(stats, stop), daemon=True).start()

    status_slot.info("CPU: Granite narrating — while the GPU keeps simulating.")
    proc = subprocess.Popen(
        [
            LLAMA_BIN,
            "-m",
            model,
            "-ngl",
            "0",
            "-t",
            "4",
            "-n",
            "150",
            "--temp",
            "0",
            "-p",
            prompt,
        ],
        cwd=RES,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env={**os.environ, "GGML_VK_VISIBLE_DEVICES": "99"},
    )
    buf: list = []
    reader = threading.Thread(target=llm_reader, args=(proc, buf), daemon=True)
    reader.start()

    t0 = time.time()
    while proc.poll() is None or reader.is_alive():
        llm_slot.markdown(
            f"**Granite guidance (CPU, streaming):**\n\n{guidance_text(''.join(buf))} ▌"
        )
        gpu_metric.metric("GPU flood throughput", f"{stats['sps']:,.0f} steps/s")
        steps_metric.metric("GPU steps during narration", f"{stats['steps']:,}")
        tok_metric.metric("narration time", f"{time.time() - t0:,.0f} s")
        time.sleep(0.3)
        if not reader.is_alive() and proc.poll() is not None:
            break
    stop.set()

    llm_slot.markdown(f"**Granite guidance (CPU):**\n\n{guidance_text(''.join(buf))}")
    status_slot.success(
        f"Done. While Granite spoke, the GPU simulated {stats['steps']:,} more flood steps "
        f"({stats['runs']} full 4,000-step updates) at {stats['sps']:,.0f} steps/s."
    )
