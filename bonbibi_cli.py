"""Headless Bonbibi demo for a terminal: the same GPU flood simulation,
shelter routing, and grounded Granite narration as the console UI, with
the flood raster rendered as ANSI half-blocks. Runs ON the Pi over SSH,
needs the resident llama-server (run_llm.sh) for narration.

    python3 bonbibi_cli.py                          # area advisory
    python3 bonbibi_cli.py --lat 40.681 --lon -74.01  # guide a person

Bands follow AIDR Guideline 7-3 hazard classes; thresholds are limiting
still-water depths (see HACKATHON.md for the literature).
"""

import argparse
import sys

import numpy as np

import routing
from bonbibi_app import (
    RES,
    SZ,
    THRESHOLDS,
    THRESHOLDS_DOC,
    ADVISORY_INSTRUCTION,
    PERSON_INSTRUCTION,
    band_coverage,
    dem_bbox,
    flood_doc,
    load_shelters,
    narrate,
    run_flood,
    shelter_status,
)

BANDS = (
    (0.05, (144, 202, 249)),
    (0.3, (66, 165, 245)),
    (0.5, (30, 90, 200)),
    (1.2, (69, 39, 160)),
)
ROUTE_RGB = {
    "wheelchair": (46, 125, 50),
    "foot": (15, 76, 129),
    "vehicle": (239, 108, 0),
}
RESET = "\x1b[0m"


def load_terrain(dem_path: str) -> np.ndarray:
    with open(dem_path) as f:
        dn = int(f.readline().split()[0])
        dem = np.array(f.read().split(), dtype=np.float32).reshape(dn, dn)
    dem -= dem.min()
    ix = (np.arange(SZ) * dn) // SZ
    return dem[np.ix_(ix, ix)]


def colorize(water, terrain, route_cells):
    t = (terrain / max(terrain.max(), 1e-6)) ** 0.6
    img = np.stack([70 + 90 * t, 78 + 85 * t, 64 + 78 * t], axis=-1)
    for thr, rgb in BANDS:
        img[water >= thr] = rgb
    for profile, cells in route_cells.items():
        rgb = ROUTE_RGB[profile]
        for r, c in cells:
            img[max(0, r - 1) : r + 2, max(0, c - 1) : c + 2] = rgb
    return img.astype(np.uint8)


def draw(img, width, markers):
    ix = (
        (np.arange(width) * SZ) // SZ
        if width == SZ
        else (np.arange(width) * SZ) // width
    )
    small = img[np.ix_(ix, ix)]
    mark = {}
    for (r, c), (ch, fg) in markers.items():
        mark[(r * width // SZ) // 2, c * width // SZ] = (ch, fg)
    lines = []
    for y in range(0, width - 1, 2):
        row = []
        for x in range(width):
            tr, tg, tb = small[y, x]
            br, bg, bb = small[y + 1, x]
            m = mark.get((y // 2, x))
            if m:
                ch, (fr, fg_, fb) = m
                row.append(f"\x1b[38;2;{fr};{fg_};{fb}m\x1b[48;2;{br};{bg};{bb}m{ch}")
            else:
                row.append(f"\x1b[38;2;{tr};{tg};{tb}m\x1b[48;2;{br};{bg};{bb}m▀")
        lines.append("".join(row) + RESET)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Bonbibi terminal demo")
    ap.add_argument("--dem", default=f"{RES}/dem_redhook.txt")
    ap.add_argument("--rain", type=float, default=0.002)
    ap.add_argument("--steps", type=int, default=400)
    ap.add_argument("--frames", type=int, default=5)
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--width", type=int, default=72)
    args = ap.parse_args()

    bbox = dem_bbox(args.dem)
    area = args.dem.split("dem_")[-1].removesuffix(".txt")
    terrain = load_terrain(args.dem)
    shelters = load_shelters(area)

    print(f"◆ Bonbibi — {area}: rain {args.rain} m/cell/step, {args.steps} steps")
    print("  GPU: V3D flood simulation | CPU: routing + Granite 4.1 3B | offline\n")

    water = None
    print("\x1b[2J", end="")
    for i in range(1, args.frames + 1):
        n = max(1, args.steps * i // args.frames)
        out = run_flood(n, args.rain, args.dem, dump="/tmp/cli_depth.bin")
        water = np.fromfile("/tmp/cli_depth.bin", dtype=np.float32).reshape(SZ, SZ)
        stat = shelter_status(shelters, water.reshape(-1), bbox)
        markers = {}
        for s in stat:
            cell = routing.to_cell(s["lat"], s["lon"], bbox)
            markers[cell] = ("◆", (179, 38, 30) if s["flooded"] else (27, 127, 75))
        sps = ""
        for line in out.splitlines():
            if "time=" in line:
                sps = line.split("time=")[1].split("s")[0]
                sps = f"  GPU {n / float(sps):,.0f} steps/s"
        print("\x1b[H", end="")
        print(draw(colorize(water, terrain, {}), args.width, markers))
        print(f"step {n}/{args.steps}{sps}   ◆ shelter (green dry, red flooded)")

    cov = band_coverage(water)
    depth = water.reshape(-1)
    print(
        f"\ncoverage: {cov['h1_pct']}% <0.3m | {cov['h2_pct']}% 0.3-0.5m (no driving) | "
        f"{cov['h3_pct']}% 0.5-1.2m (foot only) | {cov['h4_pct']}% >1.2m (unsafe for all) | "
        f"deepest {cov['max_depth_m']} m"
    )

    docs = [THRESHOLDS_DOC, flood_doc(area, args.rain, args.steps, cov)]
    if args.lat is not None and args.lon is not None:
        origin = routing.to_cell(args.lat, args.lon, bbox)
        goals = [routing.to_cell(s["lat"], s["lon"], bbox) for s in shelters]
        route_cells, markers = {}, {origin: ("◉", (255, 255, 255))}
        for s in shelters:
            cell = routing.to_cell(s["lat"], s["lon"], bbox)
            d = float(depth[cell[0] * SZ + cell[1]])
            markers[cell] = ("◆", (179, 38, 30) if d > 0.05 else (27, 127, 75))
        print(f"\nperson at ({args.lat}, {args.lon}):")
        for name, thr in THRESHOLDS.items():
            idx, path = routing.route_to_shelter(depth, thr, origin, goals)
            if idx is not None:
                s = shelters[idx]
                dist = routing.path_length_m(path, bbox)
                verdict = f"✓ {s['name']} ({dist} m)"
                route_cells[name] = path[:: max(1, len(path) // 200)]
                text = (
                    f"From this person's location, the nearest shelter reachable "
                    f"without crossing water deeper than {thr} m is {s['name']}, "
                    f"about {dist} m away. Recommended action: go now while the "
                    f"path is open; conditions can worsen quickly."
                )
            else:
                verdict = "✕ stranded"
                text = (
                    f"No shelter is reachable without crossing water deeper than "
                    f"{thr} m; they are stranded for this mobility profile. "
                    f"Recommended action: stay in place, move to the highest "
                    f"point nearby, signal for help, and do not enter the water."
                )
            print(f"  {name:11s} (≤{thr} m): {verdict}")
            docs.append(
                {
                    "doc_id": len(docs) + 1,
                    "title": f"Route result: {name} (limit {thr} m)",
                    "text": text,
                }
            )
        print()
        print(draw(colorize(water, terrain, route_cells), args.width, markers))
        print("  ◉ person   routes: green wheelchair, blue foot, orange vehicle")
        instruction = PERSON_INSTRUCTION
    else:
        stat = shelter_status(shelters, depth, bbox)
        dry = sum(1 for s in stat if not s["flooded"])
        docs.append(
            {
                "doc_id": 3,
                "title": f"Shelter status in {area}",
                "text": f"{dry} of {len(stat)} known shelter candidates are on dry ground."
                if stat
                else "No shelter candidates are known for this area.",
            }
        )
        instruction = ADVISORY_INSTRUCTION

    print("\n— Granite guidance (grounded in the computed facts above) —")
    try:
        narrate(
            docs,
            instruction,
            sink=lambda piece: (sys.stdout.write(piece), sys.stdout.flush()),
        )
    except OSError:
        print("(narration unavailable: start the resident llama-server via run_llm.sh)")
    print("\n\nSimulation-based guidance composed on-device by a language model")
    print("from computed facts. Verify with local authorities.")


if __name__ == "__main__":
    main()
