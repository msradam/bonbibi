# Bonbibi

Offline, edge flood-aware accessible routing on a Raspberry Pi 5. The integrated
GPU (Broadcom VideoCore VII / V3D) runs a flood simulation while the CPU runs a
small language model and a routing engine at the same time, with no internet.
Named after the guardian of the Sundarbans.

Status: preliminary exploration (NYU advanced project; ARM AI optimization
challenge, Physical AI track). The pieces below run and are verified; the
production gaps are listed under Status.

## Idea

A Pi 5 does inference on the CPU while the GPU sits idle. Bonbibi puts the idle
GPU to work as a flood co-processor: it simulates surface flooding over real
terrain, and the CPU meanwhile runs the routing and the language interface. The
two run concurrently on one board that costs about USD 80.

The division of labor is deliberate: deterministic code owns the safety-critical
logic (which cells are passable at a given water depth, and the route through
them), and the language model only turns the computed result into guidance. A
small model doing depth-threshold arithmetic is a safety bug; a shortest-path
search is not.

The GPU flood shaders are optimized by
[Seppa](https://github.com/msradam/seppa), AutoKernel ported to a
finite-state-machine optimizer driven by an LLM agent. That optimization is what
makes the GPU offload worthwhile: the concurrent GPU + CPU split here is the
workload it exists to enable.

## Pipeline

1. `fetch_dem.py <name> <minlat> <maxlat> <minlon> <maxlon>` pulls a real
   elevation grid (open-elevation, no key) and writes a plain-text DEM. Fetch
   once online, run offline. Samples for Red Hook (Brooklyn), Dhaka
   (Bangladesh), and downtown DC are in `samples/`.
2. `vkflood.cpp` loads the DEM as terrain and runs a flux-limited (WCA2D)
   overland-flow stencil on the V3D GPU via Vulkan compute (`shaders/flux.comp`,
   `shaders/height.comp`). It is verified against a double-precision CPU
   reference (NMSE) and conserves rainfall mass. It writes a georeferenced depth
   grid.
3. Two routers read that same depth grid:
   - `route.py <threshold_m>` — a BFS over the raster grid. Fast, offline,
     needs nothing but the flood raster.
   - `router_streets.cpp <graph.osm.pbf> <flood_depth.txt> <threshold_m>` —
     the production router: a RoutingKit Customizable Contraction Hierarchy
     (CCH) over the real OSM street graph. It samples the flood raster onto
     each street segment, marks segments deeper than the threshold
     impassable, and resolves the route to actual street names (OSM `name`
     tags), not grid cells. The CCH topology is preprocessed once; each
     flood update is a re-customization that runs in ~14ms on the Pi 5 —
     what makes real-time re-routing on a moving flood viable.
   Both take a per-person passable-depth threshold (wheelchair vs vehicle,
   say) — same flood, different mobility, different route, or stranded.
4. `fetch_live.py [lat lon usgs_site] [YYYY-MM-DD]` pulls a live river/tide
   gage (USGS Water Services) and rainfall (Open-Meteo — live forecast, or a
   historical storm day via the archive API) and prints a `RAIN` value that
   drives `vkflood` from real conditions instead of a synthetic constant.
5. A small LLM (Granite 4.0 1B) narrates the computed route as human
   guidance. Grounding matters: given raw distance numbers, Granite has been
   observed inventing street names; given the actual street list from
   `router_streets`, it narrates only those.
6. `bonbibi_mini.sh` runs the GPU flood loop and `route.py` + LLM
   concurrently on synthetic rain, offline. `bonbibi_live.sh` runs the same
   concurrent pattern using `router_streets` and real gage/rainfall data
   from `fetch_live.py`.

## Hardware and dependencies

- Raspberry Pi 5, Vulkan 1.3 (Mesa V3DV).
- llama.cpp, run CPU-only by design: the GPU is dedicated to the flood
  simulation, and current stock llama.cpp Vulkan (`-ngl > 0`) hangs on this
  device rather than completing a forward pass (V3D's 16 KB shared-memory
  limit is smaller than `mul_mat` assumes). Getting a real GPU-accelerated
  `MUL_MAT` working through Seppa's FSM loop — not yet done — is the
  highest-value next step for GPU-accelerated inference here; see Seppa's
  docs for the design work already done toward it.
- Granite 4.0 1B (Q4_0 GGUF), run CPU-only (the GPU is busy with the flood).
- For `router_streets` / `bonbibi_live.sh`: [RoutingKit](https://github.com/RoutingKit/RoutingKit)
  (BSD-2) built under `deps/routingkit`, and an `.osm.pbf` car-routing extract
  for the target area (e.g. the District of Columbia extract from
  [Geofabrik](https://download.geofabrik.de/north-america/us.html)).

## Build and run (on the Pi)

```
g++ -O3 -o vkflood vkflood.cpp -lvulkan
glslangValidator -V shaders/flux.comp -o flux.spv
glslangValidator -V shaders/height.comp -o height.spv
DEM=samples/dem_dhaka.txt RAIN=0.003 ./vkflood 256 400   # flood, verify, dump depth grid
python3 route.py 0.5                                      # grid-based route (or stranded)
bash bonbibi_mini.sh                                      # full concurrent demo, synthetic rain

# real-street routing (needs RoutingKit + an .osm.pbf, see Hardware above)
git clone https://github.com/RoutingKit/RoutingKit deps/routingkit && make -C deps/routingkit
g++ -O3 -std=c++17 -Ideps/routingkit/include router_streets.cpp deps/routingkit/lib/libroutingkit.a -lz -fopenmp -o router_streets
curl -fsSLo samples/dc.osm.pbf https://download.geofabrik.de/north-america/us/district-of-columbia-latest.osm.pbf
python3 fetch_live.py 2021-09-01   # real DC storm day (Hurricane Ida remnants); omit for live conditions
bash bonbibi_live.sh               # full concurrent demo, real streets + real data
```

`DEMFILE` and `PLACE` select the location for `bonbibi_mini.sh`; `RAIN` (m/step)
tunes rainfall against terrain relief. `bonbibi_live.sh` takes the same
`DEMFILE`/`PLACE` plus `OSMPBF` (default `samples/dc.osm.pbf`) and an optional
date argument for `fetch_live.py`.

## Status

Works and is verified: real-terrain flood on the GPU (NMSE-checked, mass
conserved), per-person accessible routing over both a raster grid and the real
OSM street network (RoutingKit CCH, ~14ms re-customization per flood update),
live gage and rainfall ingestion (USGS + Open-Meteo), grounded LLM guidance,
concurrent GPU+CPU operation, offline, across Red Hook, Dhaka, and downtown DC
from the same code.

Not yet production: the flood model has no drainage or infiltration, so
absolute depths are inflated and the spatial pattern is the meaningful output;
`router_streets` demonstrates real-street routing on one region (DC) rather
than shipping a packaged multi-region extract pipeline; there's no live,
open, street-level flood-sensor feed to assimilate against (FloodNet NYC is
the closest fit but access is by-request, not an open API) — the GPU sim is
what currently supplies the spatial field.

## License

MIT. See `LICENSE`.
