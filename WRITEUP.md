# 🌊 Bonbibi: A Flood Co-Processor for the People Who Can't Just Run

**Arm Create: AI Optimization Challenge 2026 Submission — Physical AI track**

**Author: Adam Munawar Rahman, July 2026**

Bonbibi turns a Raspberry Pi 5 into an offline flood-guidance station. The board's usually-idle VideoCore GPU simulates surface flooding over real terrain, physics-verified against a double-precision reference, while the four ARM cores concurrently route people to the nearest reachable shelter by mobility profile — wheelchair, on foot, vehicle — and Granite 4.1 3B narrates the computed result in plain language, grounded so it cannot invent a fact. Real cartography, real elevation, real shelter locations, all served from the device. No internet, no cloud. Named after the guardian spirit of the Sundarbans.

Overview video: (attached to the DevPost submission)

![Bonbibi console](docs/img/console.png)

---

## Inspiration

My previous ARM challenge entry, DreamMeridian, answered spatial questions offline on a Pi. Building it surfaced a harder question: in a disaster, the people who most need routing are the ones standard tools ignore.

UNDRR's 2023 global survey (6,342 respondents, 132 countries) quantifies it: only 26% of persons with disabilities could evacuate immediately without difficulty, and 10% could not evacuate at all — but given sufficient early warning those numbers move to 39% and 6%. Meanwhile only 8% said their local disaster plans address their needs. Transportation is a leading barrier: 41% of older adults who stayed behind in Hurricane Katrina cited lack of transportation, and in Vietnamese floods interviewees with mobility disabilities simply sheltered in place — "Without a boat or basket, we couldn't really go outside."

Warning works. Routing is the missing half. And in the places that flood worst — river deltas, informal settlements — connectivity is exactly what fails first.

The Sundarbans, where Bonbibi guards the forest, floods every monsoon. The offline data bundle for a Sundarbans village in this project is 823 KB.

---

## What It Does

One board, two engines, running at the same time:

- **GPU (VideoCore V3D)**: a WCA2D overland-flow simulation over a real elevation grid, in a Vulkan compute kernel found and verified by an LLM-driven, correctness-gated optimizer. Every run is checked against a double-precision CPU reference (NMSE), for mass conservation against injected rainfall, and for physically correct pooling.
- **CPU (4× Cortex-A76)**: shelter routing over the full-resolution depth field, a resident Granite 4.1 3B narrator, and the web console.

The interaction is a kiosk: run a storm, and the console shows hazard bands draped over a real basemap with an area advisory addressed by capability. Tap anywhere — "this person is here" — and deterministic BFS finds the nearest shelter reachable under each mobility threshold, draws the routes, and Granite composes personal guidance from the computed verdicts. A headless CLI (`bonbibi_cli.py`) does the same over SSH, rendering the flood raster in ANSI half-blocks.

### Mobility profiles, from the flood-safety literature

| Profile | Still-water limit | Basis |
|---|---|---|
| Wheelchair / cannot wade | 0.1 m | ARR Project 10: no safe flow regime documented for frail or disabled persons |
| On foot | 0.5 m | ARR's depth ceiling for children, adopted conservatively (adult ceiling 1.2 m) |
| Vehicle | 0.3 m | floating depth of a small passenger car (ARR Stage 2; AIDR H1/H2 boundary) |

I originally guessed 0.5 m (wheelchair) and 2.0 m (vehicle). The literature falsified both — 2.0 m is AIDR's "unsafe for vehicles *and people*" class, wrong by roughly 6x — so the shipped system uses the standards' limiting depths, the map legend follows the AIDR hazard classes (H1–H4+), and cars correctly become unsafe *before* pedestrians.

### Guidance that cannot invent facts

Granite receives the flood assessment, the safety limits, and each route verdict as **documents through its native RAG chat template** (llama.cpp `--jinja` + `chat_template_kwargs`), with recommended actions owned by code per verdict. The model composes; it never decides. Output is accompanied by a CAP 1.2-shaped structured alert (`status: Exercise` — the spec's designation for simulated events) and an on-screen disclaimer. The console is WCAG 2.2 AA: zero axe-core violations in idle and post-run states, keyboard-only operable, streaming guidance in an `aria-live` region, text alternatives for the map, verdict chips that differ by symbol as well as color, and browser speech output.

---

## Why Bonbibi

The closest systems are connectivity-dependent and disability-unaware. The Iowa Flood Center's routing DSS is a web app with binary road closures whose authors explicitly call for disability integration as future work; OpenPaths (2026), the newest academic accessible-routing system, is built entirely on Google APIs and cloud LLM agents with no offline mode. Meshtastic-class disaster tools solve offline *messaging*, not simulation or routing. The 2025 Journal of Hydrology review defines flood-evacuation systems as simulation + hazard assessment + shelters + routing + movement modeling: Bonbibi runs three of the five components on an $80 board, offline.

Shelter candidates come from OpenStreetMap (schools, community centres, places of worship — matching how Bangladesh actually shelters: 86% of assessed 2022 flood evacuation centres were schools), fetched once per area. Where OSM is thin — rural Sundarbans returns zero candidates — the system says so rather than pretending.

---

## The ARM Optimization Story

This challenge scores optimization, so here is the ledger — every number measured on the board, cool starts, with reproduction commands in the repos.

**1. The GPU kernel was optimized by an LLM inside a machine-owned correctness gate.** Seppa (companion repo) is a Burr finite-state machine served over MCP: the model proposes kernel and host-contract changes; the machine owns compile → verify → benchmark → keep/revert and refuses out-of-order transitions, so a variant that fails physics can never produce a benchmark number. A falsification sweep attributed the stencil's cost to fixed per-invocation overhead — not memory traffic — and the winning kernel fuses the two passes and strip-mines two cells per invocation: **1.59x** (1,345 → 2,140 steps/s at 256², NMSE 1.3e-9 over 4,000 steps). The machine then re-derived the result from its own baseline over the network, including refusing to benchmark a deliberately mass-violating kernel.

**2. The concurrency claim is measured, with a counterfactual.** Under simultaneous 4-thread LLM decode, the optimized kernel's advantage *grows* to **2.09x** (712 vs 340 steps/s), while decode keeps 90% of its solo rate. A gate-verified CPU-only version of the same physics (OpenMP) outruns the GPU on idle cores — 3,803 steps/s — but idle cores don't exist in this deployment: the best CPU-only scheme (core partitioning) reaches 8.4 t/s + 681 steps/s, while the GPU split delivers 10.3 t/s + 712 steps/s, dominating partitioned, oversubscribed (decode collapses 79%), and time-sliced alternatives on both axes.

**3. One environment variable is worth +22% decode.** With any Vulkan device visible, llama.cpp places CPU weights in GPU host-pinned write-combined memory even at `-ngl 0`. Hiding the device (`GGML_VK_VISIBLE_DEVICES=99`): 9.40 → **11.44 t/s**, same binary, same flags. Any ARM board with an integrated GPU running llama.cpp CPU-only should do this.

**4. The Arm-optimized inference path was verified, and alternatives were benchmarked honestly.** The Q4_0 runtime-repack dotprod kernels are engaged (`REPACK = 1, DOTPROD = 1`; the Cortex-A76 has no i8mm/SVE). KleidiAI (`-DGGML_CPU_KLEIDIAI=ON`) was built and measured: the native repack path beats it by 5–6% on this core — kept native. K-quants decode *slower* than Q4_0 despite smaller weights (and prompt speed drops 4x off the repack path) — kept Q4_0. Speculative decoding with the 1B drafting for the 3B reaches 78% acceptance but nets **15% slower**: on four shared cores the draft competes for the same memory bandwidth it's supposed to save — rejected on measurement.

**5. What did work for the 3B narrator:** 3 threads beat 4 (**+12%**, the fourth core is pure memory contention — it now belongs to the router), and KV-cache warming (`--cache-reuse 256`, documents ordered static-first) cuts repeat time-to-first-token from **16.0 s to 0.2 s**, so every tap after the first in a storm reuses the cached prefix.

**6. The model was chosen on grounded-quality evidence.** An A/B on identical grounded documents: Granite 4.0 1B is 2.1x faster but drops the decision-critical fact (the shelter's name and distance); Granite 4.1 3B keeps it, quotes thresholds correctly, and pays no disproportionate concurrency penalty. One resident model, 4.1 3B Q4_0.

---

## Benchmarks

Concurrent envelope (Pi 5, cool starts, steady-state thermally governed):

| Condition | GPU flood (steps/s) | CPU decode (t/s) |
|---|---|---|
| Optimized kernel alone | 2,127 | — |
| Decode alone (1B, GPU hidden) | — | 11.5 |
| **Concurrent (deployment)** | **712** | **10.3** |
| Best CPU-only alternative (partitioned) | 681 | 8.4 |

Narrator (Granite 4.1 3B Q4_0, production config `-t 3 --cache-reuse 256`):

| Metric | Value |
|---|---|
| Decode, alone / under GPU flood | 6.07 / ~5 t/s |
| Repeat-request TTFT (warm cache) | 0.2 s (vs 16.0 s cold) |
| Storm → area advisory | ~32 s |
| Tap → personal guidance | ~41 s first, ~14 s warm |

Full tables, thermal traces, and raw logs: `HACKATHON.md` and the seppa repo's `docs/paper/` (a companion paper with every number's reproduction command).

---

## Hardware

Raspberry Pi 5 16GB (4× Cortex-A76 @ 2.4 GHz, VideoCore VII V3D, LPDDR4X), Vulkan 1.3 via Mesa v3dv, passively cooled. Offline data bundle per deployed area: ~12 KB elevation + <1 MB vector basemap + shelter list. Total resident inference memory: ~2.3 GB.

---

## Challenges

**The optimizer needed a cage.** LLM-proposed kernels that break physics can look fast. Seppa's FSM makes verification a state transition the model cannot skip — the demo includes the machine refusing to benchmark a kernel with doubled rainfall.

**The first optimization search failed for a structural reason.** Searching shader text found nothing; every real win lived in the host contract (buffer packing, kernel fusion, dispatch geometry). Widening the action space recovered the full speedup. Plateaus are evidence about the search space, not just the hardware.

**My thresholds were wrong and the literature said so.** Research falsified both original mobility thresholds (a car floats at 0.3 m, not 2.0 m). The shipped system uses the standards' numbers and cites them.

**Offline maps have a right way and a wrong way.** Bulk-fetching OSM raster tiles violates their usage policy (their server correctly refused). The right way: Protomaps PMTiles bbox extracts — the intended offline use — under 1 MB per area.

**A 1B model paraphrases verdicts.** "Stranded" became "seek alternative routes" until recommended actions moved into the documents as code-owned text. The safety architecture hardened into: deterministic code decides the action, the model only phrases it.

---

## What I Learned

- Measure, don't assume, on edge silicon: the GPU loses the drag race to its own CPU and still wins the deployment; speculative decoding is a loss when draft and target share bandwidth; a fourth core can be worth negative tokens per second.
- Correctness gates change what an LLM optimizer is: with the machine owning verification, a wrong-but-fast kernel is unrepresentable, and every kept number is trustworthy by construction.
- Grounding is an architecture, not a prompt: Granite's document template plus code-owned verdicts turned narration from plausible to faithful.
- The accessibility literature designs the product for you: multimodal delivery, plain language, and capability-addressed warnings are documented requirements, not nice-to-haves.

---

## What's Next

- Wire the street-graph router (RoutingKit CCH, ~14 ms re-customization, already in the repo) into the console for street-name routes and narration.
- On-device TTS (Piper) for spoken guidance within the measured concurrency envelope.
- GPU-accelerated inference through Seppa's verified small-matmul path once the upstream llama.cpp Vulkan composition defect (isolated on llvmpipe, documented in the seppa repo) is fixed — the same board would then run physics and attention on the GPU.
- Live sensor assimilation (FloodNet-class street sensors) where feeds exist.

---

## Step-by-Step Instructions

Complete build/run/validate instructions are in `README.md`. The short version, on a Pi 5:

```bash
# one-time, online: fetch an area (elevation, basemap, shelters)
python3 fetch_dem.py redhook 40.667 40.685 -74.02 -73.998
python3 fetch_basemap.py dem_redhook.txt redhook
python3 fetch_shelters.py dem_redhook.txt redhook

# build + validate physics (expect NMSE=yes, mass conserved=yes)
g++ -O3 -o vkflood2 vkflood2.cpp -lvulkan
glslangValidator -V shaders/fused2s.comp -o fused2s.spv
DEM=dem_redhook.txt RAIN=0.002 STRIP=2 FUSED=1 FLUX_SPV=fused2s.spv ./vkflood2 256 400
python3 routing.py    # routing self-check

# run (llama.cpp built CPU-side per its ARM docs; model: granite-4.1-3b Q4_0)
GGML_VK_VISIBLE_DEVICES=99 llama-server -m granite-4.1-3b-Q4_0.gguf \
    -ngl 0 -t 3 -c 4096 --jinja --cache-reuse 256 --port 8081 &
uvicorn bonbibi_app:app --host 0.0.0.0 --port 8500
# or headless:
python3 bonbibi_cli.py --lat 40.681 --lon -74.01
```

---

## Works Cited

Australian Institute for Disaster Resilience. (2017). *Guideline 7-3: Flood Hazard*. https://knowledge.aidr.org.au/media/3518/adr-guideline-7-3.pdf

Engineers Australia / Australian Rainfall and Runoff. (2011). *Project 10: Appropriate Safety Criteria for People and Vehicles*. https://arr.ga.gov.au/

Dibbelt, J., Strasser, B., & Wagner, D. (2016). Customizable Contraction Hierarchies. *ACM Journal of Experimental Algorithmics*, 21, Article 1.5.

Guidolin, M., Chen, A. S., Ghimire, B., Keedwell, E. C., Djordjević, S., & Savić, D. A. (2016). A weighted cellular automata 2D inundation model for rapid flood analysis. *Environmental Modelling & Software*, 84, 378–394.

IBM Granite. (2026). *Granite 4.0/4.1 Prompt Engineering Guide*. https://github.com/ibm-granite/granite-4.0-language-models

IOM DTM. (2022). *Bangladesh: North-Eastern Flash Flood — Evacuation Centre Assessment*. https://dtm.iom.int/

llama.cpp. Arm AArch64 optimized kernels and runtime repacking (PRs #5780, #10446); server prompt caching. https://github.com/ggml-org/llama.cpp

Herfort, B., et al. (2023). A spatio-temporal analysis investigating completeness and inequalities of global urban building data in OpenStreetMap. *Nature Communications*, 14, 3985.

Protomaps. *PMTiles: a single-file archive format for tiled data*. https://protomaps.com/

UNDRR. (2023). *Global Survey Report on Persons with Disabilities and Disasters*. https://www.undrr.org/report/2023-gobal-survey-report-on-persons-with-disabilities-and-disasters

Xia, J., Falconer, R. A., Xiao, X., & Wang, Y. (2014). Criterion of vehicle stability in floodwaters based on theoretical and experimental studies. *Natural Hazards*, 70, 1619–1630.

Journal of Hydrology. (2025). An overview of flood evacuation planning: models, methods and future directions. https://doi.org/10.1016/j.jhydrol.2025.133026
