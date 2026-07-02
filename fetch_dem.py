"""Fetch a real elevation grid (DEM) for a NYC neighborhood from Open-Meteo's
free elevation API (no key, no GDAL). Writes a plain-text DEM that vkflood loads
as terrain. Offline-friendly: fetch once with internet, run the flood sim offline.

Output format (dem_redhook.txt):
  line 1: N minlat maxlat minlon maxlon
  next N lines: N elevations each (metres), row 0 = north edge.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request

# Location: argv = name minlat maxlat minlon maxlon; default Red Hook, Brooklyn.
if len(sys.argv) >= 6:
    NAME = sys.argv[1]
    MIN_LAT, MAX_LAT, MIN_LON, MAX_LON = (float(v) for v in sys.argv[2:6])
else:
    NAME = "redhook"
    MIN_LAT, MAX_LAT = 40.667, 40.685
    MIN_LON, MAX_LON = -74.020, -73.998
N = 48  # grid resolution (N x N)
BATCH = 500  # open-elevation takes many locations per POST


def grid_coords() -> list[tuple[float, float]]:
    # row 0 = north (max lat) so the raster reads top-down like a map
    coords = []
    for r in range(N):
        lat = MAX_LAT - (MAX_LAT - MIN_LAT) * r / (N - 1)
        for c in range(N):
            lon = MIN_LON + (MAX_LON - MIN_LON) * c / (N - 1)
            coords.append((lat, lon))
    return coords


def fetch(coords: list[tuple[float, float]]) -> list[float]:
    out: list[float] = []
    url = "https://api.open-elevation.com/api/v1/lookup"
    for i in range(0, len(coords), BATCH):
        chunk = coords[i : i + BATCH]
        body = json.dumps({
            "locations": [{"latitude": la, "longitude": lo} for la, lo in chunk]
        }).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=180) as resp:
            out.extend(r["elevation"] for r in json.load(resp)["results"])
        time.sleep(1.0)
        print(f"  fetched {len(out)}/{len(coords)}", file=sys.stderr)
    return out


def main() -> None:
    coords = grid_coords()
    elev = fetch(coords)
    assert len(elev) == N * N, (len(elev), N * N)
    lo, hi = min(elev), max(elev)
    with open(f"dem_{NAME}.txt", "w") as f:
        f.write(f"{N} {MIN_LAT} {MAX_LAT} {MIN_LON} {MAX_LON}\n")
        for r in range(N):
            f.write(" ".join(f"{elev[r * N + c]:.2f}" for c in range(N)) + "\n")
    print(f"wrote dem_{NAME}.txt: {N}x{N}, elevation {lo:.1f}..{hi:.1f} m (range {hi - lo:.1f} m)")


if __name__ == "__main__":
    main()
