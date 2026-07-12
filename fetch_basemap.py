"""One-time offline basemap fetch, the same pattern as fetch_dem.py: while
online, extract a Protomaps vector-tile archive for a DEM's bbox and the
styling assets; afterwards the demo map runs with zero connectivity.
Bbox extracts from Protomaps' daily planet builds are their intended use.

  fetch_basemap.py <dem_file> <name> [build_date YYYYMMDD]

Writes static/<name>.pmtiles plus (once) static/pmtiles.js,
static/basemaps.js, and static/basemaps-assets/ (fonts + sprites).
Requires the pmtiles CLI: github.com/protomaps/go-pmtiles releases.
"""

import subprocess
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

dem, name = sys.argv[1], sys.argv[2]
build = (
    sys.argv[3]
    if len(sys.argv) > 3
    else (date.today() - timedelta(days=1)).strftime("%Y%m%d")
)

with open(dem) as f:
    _, la0, la1, lo0, lo1 = f.readline().split()
la0, la1, lo0, lo1 = (float(v) for v in (la0, la1, lo0, lo1))
pad_lat, pad_lon = (la1 - la0) * 0.3, (lo1 - lo0) * 0.3

static = Path("static")
static.mkdir(exist_ok=True)
subprocess.run(
    [
        "pmtiles",
        "extract",
        f"https://build.protomaps.com/{build}.pmtiles",
        str(static / f"{name}.pmtiles"),
        f"--bbox={lo0 - pad_lon},{la0 - pad_lat},{lo1 + pad_lon},{la1 + pad_lat}",
    ],
    check=True,
)

for fname, url in (
    ("pmtiles.js", "https://unpkg.com/pmtiles@4.3.0/dist/pmtiles.js"),
    ("basemaps.js", "https://unpkg.com/@protomaps/basemaps@5.5.0/dist/basemaps.js"),
    ("maplibre-gl.js", "https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"),
    ("maplibre-gl.css", "https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css"),
):
    p = static / fname
    if not p.exists():
        p.write_bytes(urllib.request.urlopen(url, timeout=60).read())

assets = static / "basemaps-assets"
if not assets.exists():
    zip_path = static / "bm-assets.zip"
    zip_path.write_bytes(
        urllib.request.urlopen(
            "https://github.com/protomaps/basemaps-assets/archive/refs/heads/main.zip",
            timeout=120,
        ).read()
    )
    subprocess.run(["unzip", "-q", str(zip_path), "-d", str(static)], check=True)
    (static / "basemaps-assets-main").rename(assets)
    zip_path.unlink()
print(f"offline basemap ready: static/{name}.pmtiles + styling assets")
