"""Streamlit demo of the bonbibi split: the V3D GPU floods real terrain
while the CPU routes around the water and Granite narrates the route.

Runs ON the Pi, next to the flood harness and llama.cpp:

    /root/demo-venv/bin/streamlit run bonbibi_demo.py \
        --server.address 0.0.0.0 --server.port 8501

Phase 1 animates the flood evolving over the DEM (each frame is a fresh
deterministic GPU run to step N, full-resolution depth dump). Phase 2
computes the two mobility routes from the final depth grid, then streams
Granite's grounded guidance from the CPU while the GPU keeps simulating
in the background, with live throughput for both halves of the board.
"""

import glob
import os
import re
import subprocess
import threading
import time

import numpy as np
import streamlit as st
from PIL import Image

RES = "/root/v3d-research"
SZ = 256
VKFLOOD_ENV = {"STRIP": "2", "FUSED": "1", "FLUX_SPV": "fused2s.spv"}
LLAMA_BIN = f"{RES}/llama.cpp/build-vulkan/bin/llama-completion"
TIME_RE = re.compile(r"time=([0-9.]+)s")

st.set_page_config(page_title="bonbibi", page_icon="🌊", layout="wide")


@st.cache_data
def load_terrain(dem_path: str) -> np.ndarray:
    with open(dem_path) as f:
        head = f.readline().split()
        dn = int(head[0])
        dem = np.array(f.read().split(), dtype=np.float32).reshape(dn, dn)
    dem -= dem.min()
    ys = (np.arange(SZ) * dn) // SZ
    xs = (np.arange(SZ) * dn) // SZ
    return dem[np.ix_(ys, xs)]


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


def render(terrain: np.ndarray, water: np.ndarray | None) -> Image.Image:
    t = (terrain / terrain.max()) ** 0.7
    gy, gx = np.gradient(terrain)
    light = -gx - gy
    m = np.abs(light).max()
    shade = (0.72 + 0.28 * light / m)[..., None] if m > 0 else 1.0
    img = np.stack([90 + 120 * t, 100 + 110 * t, 80 + 100 * t], axis=-1) * shade
    if water is not None:
        a = np.clip(water / 2.0, 0.0, 0.85)[..., None]
        blue = np.array([30.0, 90.0, 210.0])
        img = img * (1 - a) + blue * a
    return Image.fromarray(img.astype(np.uint8)).resize((640, 640), Image.BILINEAR)


def route(threshold: float) -> str:
    p = subprocess.run(
        ["python3", "route.py", str(threshold)],
        cwd=RES,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return p.stdout.strip().splitlines()[0] if p.stdout.strip() else "(no route output)"


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


st.title("bonbibi — one board, two engines")
st.caption(
    "Raspberry Pi 5. The V3D GPU simulates flooding over real terrain "
    "(WCA2D, physics-gated kernel from seppa) while the four CPU cores "
    "route around the water and Granite 4.0 1B narrates the result."
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
    frames = st.slider("Animation frames", 4, 16, 8)
    go = st.button("Run the storm", type="primary", use_container_width=True)

left, right = st.columns([3, 2])
frame_slot = left.empty()
status_slot = left.empty()
routes_slot = right.container()
llm_slot = right.empty()
m1, m2, m3 = st.columns(3)
gpu_metric, steps_metric, tok_metric = m1.empty(), m2.empty(), m3.empty()

terrain = load_terrain(dem)
frame_slot.image(render(terrain, None), caption="terrain, dry")

if go:
    status_slot.info("GPU: flooding the terrain...")
    water = None
    for i in range(1, frames + 1):
        n = max(1, steps * i // frames)
        out = run_flood(n, rain, dem, dump="/tmp/demo_depth.bin")
        water = np.fromfile("/tmp/demo_depth.bin", dtype=np.float32).reshape(SZ, SZ)
        m = TIME_RE.search(out)
        sps = f"{n / float(m.group(1)):,.0f} steps/s" if m else ""
        frame_slot.image(
            render(terrain, water),
            caption=f"step {n}/{steps} — max depth {water.max():.2f} m — GPU {sps}",
        )

    status_slot.info("CPU: routing two mobility profiles through the flood...")
    wheel = route(0.5)
    car = route(2.0)
    with routes_slot:
        st.subheader("Routes (deterministic, CPU)")
        st.markdown(f"**Wheelchair (≤0.5 m):** {wheel}")
        st.markdown(f"**Vehicle (≤2.0 m):** {car}")

    place = os.path.basename(dem).replace("dem_", "").replace(".txt", "")
    prompt = (
        f"You are an emergency guidance assistant in a {place} flood. "
        f"A routing engine computed:\n"
        f"- Wheelchair user (can only cross water up to 0.5 m deep): {wheel}\n"
        f"- Car (can cross water up to 2.0 m deep): {car}\n"
        f"In 3 short sentences, tell the wheelchair user and the driver "
        f"what each should do right now."
    )
    model = glob.glob(f"{RES}/models/**/*ranite*4*.gguf", recursive=True)[0]

    stats = {"runs": 0, "steps": 0, "sps": 0.0, "rain": rain, "dem": dem}
    stop = threading.Event()
    gpu_thread = threading.Thread(target=gpu_loop, args=(stats, stop), daemon=True)
    gpu_thread.start()

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
        text = "".join(buf)
        shown = (
            text.rsplit("assistant", 1)[-1].split("EOF by user")[0].strip()
            if "assistant" in text
            else ""
        )
        llm_slot.markdown(f"**Granite guidance (CPU, streaming):**\n\n{shown} ▌")
        gpu_metric.metric("GPU flood throughput", f"{stats['sps']:,.0f} steps/s")
        steps_metric.metric("GPU steps during narration", f"{stats['steps']:,}")
        tok_metric.metric("narration time", f"{time.time() - t0:,.0f} s")
        time.sleep(0.3)
        if not reader.is_alive() and proc.poll() is not None:
            break
    stop.set()

    text = "".join(buf)
    shown = (
        text.rsplit("assistant", 1)[-1].split("EOF by user")[0].strip()
        if "assistant" in text
        else text.strip()
    )
    llm_slot.markdown(f"**Granite guidance (CPU):**\n\n{shown}")
    status_slot.success(
        f"Done. While Granite spoke, the GPU simulated {stats['steps']:,} more flood steps "
        f"({stats['runs']} full 4,000-step updates) at {stats['sps']:,.0f} steps/s."
    )
