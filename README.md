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

## Pipeline

1. `fetch_dem.py <name> <minlat> <maxlat> <minlon> <maxlon>` pulls a real
   elevation grid (open-elevation, no key) and writes a plain-text DEM. Fetch
   once online, run offline. Samples for Red Hook (Brooklyn) and Dhaka
   (Bangladesh) are in `samples/`.
2. `vkflood.cpp` loads the DEM as terrain and runs a flux-limited (WCA2D)
   overland-flow stencil on the V3D GPU via Vulkan compute (`shaders/flux.comp`,
   `shaders/height.comp`). It is verified against a double-precision CPU
   reference (NMSE) and conserves rainfall mass. It writes a georeferenced depth
   grid.
3. `route.py <threshold_m>` runs a shortest-path search through cells whose water
   depth is at or below a per-person passable threshold (e.g. wheelchair vs
   vehicle). Same flood, different mobility, different route, or stranded.
4. A small LLM (Granite 4.0 1B) narrates the computed route as human guidance.
5. `bonbibi_mini.sh` runs the GPU flood loop and the CPU router + LLM
   concurrently, offline, and prints the guidance.

## Hardware and dependencies

- Raspberry Pi 5, Vulkan 1.3 (Mesa V3DV).
- llama.cpp built with Vulkan, plus the V3D small-shared-memory matmul fix
  (without it the Vulkan backend aborts at init on the Pi 5).
- Granite 4.0 1B (Q4_0 GGUF), run CPU-only (the GPU is busy with the flood).

## Build and run (on the Pi)

```
g++ -O3 -o vkflood vkflood.cpp -lvulkan
glslangValidator -V shaders/flux.comp -o flux.spv
glslangValidator -V shaders/height.comp -o height.spv
DEM=samples/dem_dhaka.txt RAIN=0.003 ./vkflood 256 400   # flood, verify, dump depth grid
python3 route.py 0.5                                      # wheelchair route (or stranded)
bash bonbibi_mini.sh                                      # full concurrent demo
```

`DEMFILE` and `PLACE` select the location for `bonbibi_mini.sh`; `RAIN` (m/step)
tunes rainfall against terrain relief.

## Status

Works and is verified: real-terrain flood on the GPU (NMSE-checked, mass
conserved), per-person accessible routing, concurrent GPU+CPU operation, offline,
on Red Hook and Dhaka from the same code.

Not yet production: the flood model has no drainage or infiltration, so absolute
depths are inflated and the spatial pattern is the meaningful output; routing is
a grid search, not [Valhalla](https://github.com/valhalla/valhalla) over the
street network (the depth grid is already georeferenced for that step); rainfall
is uniform, not a real weather feed.

## License

MIT. See `LICENSE`.
