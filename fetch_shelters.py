"""One-time shelter-candidate fetch for an area, same pattern as
fetch_dem.py / fetch_basemap.py: while online, query Overpass for OSM
amenities that serve as evacuation shelter candidates inside the DEM
bbox; afterwards routing runs offline against the saved file.

  fetch_shelters.py <dem_file> <name>

Writes static/shelters_<name>.json: [{"name", "kind", "lat", "lon"}].
Candidates are schools, community centres, places of worship, and
explicit emergency shelters; real deployments should review this list
with local knowledge (OSM completeness varies by region).
"""

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

dem, name = sys.argv[1], sys.argv[2]
with open(dem) as f:
    _, la0, la1, lo0, lo1 = f.readline().split()

query = f"""
[out:json][timeout:60];
(
  nwr["amenity"~"^(school|community_centre|place_of_worship)$"]({la0},{lo0},{la1},{lo1});
  nwr["emergency"="shelter"]({la0},{lo0},{la1},{lo1});
  nwr["social_facility"="shelter"]({la0},{lo0},{la1},{lo1});
);
out center tags;
"""
req = urllib.request.Request(
    "https://overpass-api.de/api/interpreter",
    data=urllib.parse.urlencode({"data": query}).encode(),
    headers={"User-Agent": "bonbibi-shelter-fetch/1.0 (one-time)"},
)
elements = json.load(urllib.request.urlopen(req, timeout=120))["elements"]

shelters, seen = [], set()
for e in elements:
    lat = e.get("lat") or e.get("center", {}).get("lat")
    lon = e.get("lon") or e.get("center", {}).get("lon")
    if lat is None:
        continue
    tags = e.get("tags", {})
    label = tags.get("name") or tags.get("amenity", "shelter").replace("_", " ")
    key = (round(lat, 5), round(lon, 5))
    if key in seen:
        continue
    seen.add(key)
    shelters.append(
        {
            "name": label,
            "kind": tags.get("emergency") or tags.get("amenity") or "shelter",
            "lat": lat,
            "lon": lon,
        }
    )

out = Path("static") / f"shelters_{name}.json"
out.write_text(json.dumps(shelters, indent=1))
print(f"{len(shelters)} shelter candidates -> {out}")
