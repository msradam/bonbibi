# 🌊 Bonbibi: A Flood Co-Processor for the People Who Can't Just Run

**Arm Create: AI Optimization Challenge 2026 Submission (Physical AI track)**

**Author: Adam Munawar Rahman, July 2026**

Bonbibi turns a Raspberry Pi 5 into an offline flood-guidance station. The board's usually-idle VideoCore GPU simulates surface flooding over real terrain, physics-verified against a double-precision reference, while the four ARM cores concurrently route people to the nearest reachable shelter by mobility profile (wheelchair, on foot, vehicle) and Granite 4.1 3B narrates the computed result in plain language, grounded so it cannot invent a fact. Real cartography, real elevation, real shelter locations, all served from the device. No internet, no cloud. Named after the guardian spirit of the Sundarbans.

Overview video: (attached to the DevPost submission)

![Bonbibi console](docs/img/console.png)

---

## Inspiration

My previous ARM challenge entry, DreamMeridian, answered spatial questions offline on a Pi. Building it surfaced a harder question: in a disaster, the people who most need routing are the ones standard tools ignore.

UNDRR's 2023 global survey (6,342 respondents, 132 countries) quantifies it: only 26% of persons with disabilities could evacuate immediately without difficulty, and 10% could not evacuate at all, but given sufficient early warning those numbers move to 39% and 6%. Meanwhile only 8% said their local disaster plans address their needs. Transportation is a leading barrier: 41% of older adults who stayed behind in Hurricane Katrina cited lack of transportation, and in Vietnamese floods interviewees with mobility disabilities simply sheltered in place: "Without a boat or basket, we couldn't really go outside."

The 2022 northeastern Bangladesh flash floods put a number and names to that gap. Human Rights Watch documented at least 141 deaths in the June 15-28 floods, and interviewed survivors including a disabled man in Sylhet, Mohammad Sher Uddin, who said: "We were not prepared because we did not receive any warnings." Five of the documented deaths were people with disabilities and one was an older person, most drowning or falling ill while trying to reach an inaccessible toilet or shelter during the flood (Human Rights Watch, 2023).

Warning works. Routing is the missing half. And in the places that flood worst (river deltas, informal settlements), connectivity is exactly what fails first. The scale is documented: 1.81 billion people, 23% of humanity, face significant 1-in-100-year flood exposure, 89% of them in low- and middle-income countries (World Bank / Nature Communications, 2022). The UN's Early Warnings for All initiative aims to cover everyone on Earth by end-2027 with a $3.1B plan, yet 48% of least developed countries still lack adequate multi-hazard early warning, and the funded mechanism for acting ahead of a forecast, anticipatory action, was activated 146 times in 54 countries in 2025, reaching 9.6 million people. A $120 guidance station is the kind of pre-positioned activity that machinery exists to pay for. Full positioning research with citations: `docs/POSITIONING.md`.

The Sundarbans, where Bonbibi guards the forest, floods every monsoon. The offline data bundle for a Sundarbans village in this project is 823 KB. Bangladesh itself is the proof the theory works: warning plus shelters plus 76,020 trained volunteers took cyclone mortality from ~300,000 (1970) to about seventeen (2019).

---

## What It Does

One board, two engines, running at the same time:

- **GPU (VideoCore V3D)**: a WCA2D overland-flow simulation over a real elevation grid, in a Vulkan compute kernel found and verified by an LLM-driven, correctness-gated optimizer. Every run is checked against a double-precision CPU reference (NMSE), for mass conservation against injected rainfall, and for physically correct pooling.
- **CPU (4× Cortex-A76)**: shelter routing over the full-resolution depth field, a resident Granite 4.1 3B narrator, and the web console.

The interaction is a kiosk: run a storm, and the console shows hazard bands draped over a real basemap with an area advisory addressed by capability. Tap anywhere ("this person is here") and deterministic BFS finds the nearest shelter reachable under each mobility threshold, draws the routes, and Granite composes personal guidance from the computed verdicts. A headless CLI (`bonbibi_cli.py`) does the same over SSH, rendering the flood raster in ANSI half-blocks.

**What "offline" means, precisely.** The seven areas shipped in `samples/` (Red Hook, Dhaka, Gabura/Sundarbans, Beira, Sehwan, Kuttanad, downtown DC) need no internet at all, ever: elevation, basemap, and shelter data are already in the repo, and the basemap is a local Protomaps PMTiles extract served by the Pi itself, not a remote tile server. Adding a new area is the only online step (`fetch_dem.py`, `fetch_basemap.py`, `fetch_shelters.py`, run once), after which that area is offline too. Simulation, routing, narration, and the map all run with the network interface down. The one optional exception is `fetch_live.py` (USGS gage + Open-Meteo rainfall), which drives a run from real conditions instead of a manual rain rate and needs connectivity only when invoked.

### Mobility profiles, from the flood-safety literature

| Profile | Still-water limit | Basis |
|---|---|---|
| Wheelchair / cannot wade | 0.1 m | ARR Project 10: no safe flow regime documented for frail or disabled persons |
| On foot | 0.5 m | ARR's depth ceiling for children, adopted conservatively (adult ceiling 1.2 m) |
| Vehicle | 0.3 m | floating depth of a small passenger car (ARR Stage 2; AIDR H1/H2 boundary) |

I originally guessed 0.5 m (wheelchair) and 2.0 m (vehicle). The literature falsified both: 2.0 m is AIDR's "unsafe for vehicles *and people*" class, wrong by roughly 6x, so the shipped system uses the standards' limiting depths, the map legend follows the AIDR hazard classes (H1–H4+), and cars correctly become unsafe *before* pedestrians.

### Guidance that cannot invent facts

Granite receives the flood assessment, the safety limits, and each route verdict as **documents through its native RAG chat template** (llama.cpp `--jinja` + `chat_template_kwargs`), with recommended actions owned by code per verdict. The model composes; it never decides. Output is accompanied by a CAP 1.2-shaped structured alert (`status: Exercise`, the spec's designation for simulated events) and an on-screen disclaimer. The console is WCAG 2.2 AA: zero axe-core violations in idle and post-run states, keyboard-only operable, streaming guidance in an `aria-live` region, text alternatives for the map, verdict chips that differ by symbol as well as color, and browser speech output.

---

## Why Bonbibi

The closest systems are connectivity-dependent and disability-unaware. The Iowa Flood Center's routing DSS is a web app with binary road closures whose authors explicitly call for disability integration as future work; OpenPaths (2026), the newest academic accessible-routing system, is built entirely on Google APIs and cloud LLM agents with no offline mode. Meshtastic-class disaster tools solve offline *messaging*, not simulation or routing. The 2025 Journal of Hydrology review defines flood-evacuation systems as simulation + hazard assessment + shelters + routing + movement modeling: Bonbibi runs three of the five components on an $80 board, offline.

Shelter candidates come from OpenStreetMap (schools, community centres, places of worship, matching how Bangladesh actually shelters: 86% of assessed 2022 flood evacuation centres were schools), fetched once per area. Where OSM is thin (rural Sundarbans returns zero candidates), the system says so rather than pretending.

---

## The ARM Optimization Story

This challenge scores optimization, so here is the ledger: every number measured on the board, cool starts, with reproduction commands in the repos. Items 3–5's CPU-side numbers were re-measured live on 2026-08-14 against the actual production model (`granite-4.1-3b-Q4_0.gguf`, not a smaller stand-in), CPU-only (`-ngl 0` on every run, kiosk/display stopped to remove GPU contention), `-t 3`, `r=5`; raw `llama-bench` output is in `bench_llm_cpu.log`, reproduction script `bench_llm_cpu.sh`.

**1. The GPU kernel was optimized by an LLM inside a machine-owned correctness gate.** Seppa (companion repo) is a Burr finite-state machine served over MCP: the model proposes kernel and host-contract changes; the machine owns compile → verify → benchmark → keep/revert and refuses out-of-order transitions, so a variant that fails physics can never produce a benchmark number. A falsification sweep attributed the stencil's cost to fixed per-invocation overhead, not memory traffic, and the winning kernel fuses the two passes and strip-mines two cells per invocation: **1.59x** (1,345 → 2,140 steps/s at 256², NMSE 1.3e-9 over 4,000 steps). The machine then re-derived the result from its own baseline over the network, including refusing to benchmark a deliberately mass-violating kernel.

**2. The concurrency claim is measured, with a counterfactual.** Under simultaneous 4-thread LLM decode, the optimized kernel's advantage *grows* to **2.09x** (712 vs 340 steps/s), while decode keeps 90% of its solo rate. A gate-verified CPU-only version of the same physics (OpenMP) outruns the GPU on idle cores (3,803 steps/s), but idle cores don't exist in this deployment: the best CPU-only scheme (core partitioning) reaches 8.4 t/s + 681 steps/s, while the GPU split delivers 10.3 t/s + 712 steps/s, dominating partitioned, oversubscribed (decode collapses 79%), and time-sliced alternatives on both axes.

**3. Hiding the GPU from the CPU-only inference process is worth up to 10x, not just +22% decode.** With any Vulkan device visible, llama.cpp places CPU weights in GPU host-pinned write-combined memory even at `-ngl 0`: fast for a GPU to write, bad for a CPU to read repeatedly during batched matmul. Hiding the device (`GGML_VK_VISIBLE_DEVICES=99`), same binary, same flags: prompt processing **2.12 → 22.39 t/s (10.6x)**, decode **4.16 → 4.73 t/s (+13.7%)**. An earlier pass on a smaller model reported only a +22% decode effect; re-measuring on the production model surfaced the much larger prompt-processing regression as the bigger half of this bug. Any Arm board with an integrated GPU running llama.cpp CPU-only should set this.

**4. The Arm-optimized inference path beats KleidiAI, every K-quant, and speculative decoding, on the production model.** The Q4_0 runtime-repack dotprod kernels are engaged (`REPACK = 1, DOTPROD = 1`; the Cortex-A76 has no i8mm/SVE). KleidiAI (`-DGGML_CPU_KLEIDIAI=ON`) was built and re-benchmarked against native on Granite 4.1 3B: native wins prompt processing by **39.7%** (31.16 vs 22.31 t/s) and decode by **14.3%** (5.35 vs 4.68 t/s). Kept native. Q3_K_M and Q4_K_M were also re-benchmarked: Q4_0 beats even the better of the two (Q4_K_M) by **73.9%** prompt processing (21.22 vs 12.20 t/s) and **7.8%** decode (4.69 vs 4.35 t/s), despite Q3_K_M being 13% smaller. Kept Q4_0. Speculative decoding (1B drafting for the 3B, via `llama-server -md`) was re-run live through a real chat completion: **51.7% draft acceptance (77/149)**, effective decode **4.42 t/s vs. a 4.70 t/s non-speculative baseline at the same thread count: 6.0% slower**, not faster. Same conclusion as the 2026-07-12 pass (78% acceptance, 15% slower on a different prompt) on a fresh prompt and a fresh acceptance rate: the draft model competes for the same memory bandwidth it's supposed to save on four shared cores. Rejected on measurement, twice now.

**5. What did work for the 3B narrator, with an honest correction:** thread count is a real tradeoff, not a clean win: 3 threads beats 4 on decode (4.70 vs 4.38 t/s, **+7.3%**) but *loses* on prompt processing (21.44 vs 25.24 t/s, 4 threads is 17.7% faster there). Production keeps `-t 3` because decode latency dominates the interactive narration UX. KV-cache warming (`--cache-reuse 256`, documents ordered static-first) cuts repeat time-to-first-token from **16.0 s to 0.2 s**, so every tap after the first in a storm reuses the cached prefix.

**6. The model was chosen on grounded-quality evidence.** An A/B on identical grounded documents: Granite 4.0 1B is 2.1x faster but drops the decision-critical fact (the shelter's name and distance); Granite 4.1 3B keeps it, quotes thresholds correctly, and pays no disproportionate concurrency penalty. One resident model, 4.1 3B Q4_0.

---

## Benchmarks

Concurrent envelope (Pi 5, cool starts, steady-state thermally governed):

| Condition | GPU flood (steps/s) | CPU decode (t/s) |
|---|---|---|
| Optimized kernel alone | 2,127 | n/a |
| Decode alone (1B, GPU hidden) | n/a | 11.5 |
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

Hardware verification, straight from the raw logs, not asserted specs:

```
$ head -1 bench_llm_cpu.log
=== 2026-08-14T16:11:51Z — Raspberry Pi 5 Model B Rev 1.1 ===

$ grep system_info spec_decode.log
system_info: n_threads = 3 (n_threads_batch = 3) / 4 | CPU : NEON = 1 | ARM_FMA = 1 |
FP16_VA = 1 | DOTPROD = 1 | LLAMAFILE = 1 | OPENMP = 1 | REPACK = 1 |
```

---

## Challenges

**The optimizer needed a cage.** LLM-proposed kernels that break physics can look fast. Seppa's FSM makes verification a state transition the model cannot skip: the demo includes the machine refusing to benchmark a kernel with doubled rainfall.

**The first optimization search failed for a structural reason.** Searching shader text found nothing; every real win lived in the host contract (buffer packing, kernel fusion, dispatch geometry). Widening the action space recovered the full speedup. Plateaus are evidence about the search space, not just the hardware.

**My thresholds were wrong and the literature said so.** Research falsified both original mobility thresholds (a car floats at 0.3 m, not 2.0 m). The shipped system uses the standards' numbers and cites them.

**Offline maps have a right way and a wrong way.** Bulk-fetching OSM raster tiles violates their usage policy (their server correctly refused). The right way: Protomaps PMTiles bbox extracts (the intended offline use), under 1 MB per area.

**A 1B model paraphrases verdicts.** "Stranded" became "seek alternative routes" until recommended actions moved into the documents as code-owned text. The safety architecture hardened into: deterministic code decides the action, the model only phrases it.

**The board went unresponsive before the deadline.** The touchscreen for the kiosk demo arrived late, leaving a narrow window to wire it up and record a live on-device capture; the Pi 5 stopped responding on the network shortly after (unresponsive at the OS level, no ping/ARP/SSH, though powered) before that recording could happen. The numbers in this writeup are not invented to cover the gap: they come from `bench_llm_cpu.log`, `spec_decode.log`, and `BENCHMARK_RESULTS.md`, all captured directly on the Pi earlier the same day, before the board went down. What's missing is a fresh live-hardware video capture, not the measurements themselves. Recovered logs from the board's SD card (`sdcard_recovery/`, pulled read-only via `debugfs` after the crash, since SSH could no longer reach it) confirm the console itself was live that day: `bonbibi_server.log` shows Uvicorn serving `GET /panel/ HTTP/1.1" 200 OK`, and `cog.log` shows the kiosk browser loading that page successfully. The last attempt's `llama_server.log` shows the narrator backend failing to start (`env: 'llama.cpp/build-vulkan/bin/llama-server': No such file or directory`, a stale binary path in the launcher, not a hardware fault), so that particular run had the map and console live without spoken/text guidance.

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
- GPU-accelerated inference through Seppa's verified small-matmul path once the upstream llama.cpp Vulkan composition defect (isolated on llvmpipe, documented in the seppa repo) is fixed: the same board would then run physics and attention on the GPU.
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

IOM DTM. (2022). *Bangladesh: North-Eastern Flash Flood, Evacuation Centre Assessment*. https://dtm.iom.int/

llama.cpp. Arm AArch64 optimized kernels and runtime repacking (PRs #5780, #10446); server prompt caching. https://github.com/ggml-org/llama.cpp

Herfort, B., et al. (2023). A spatio-temporal analysis investigating completeness and inequalities of global urban building data in OpenStreetMap. *Nature Communications*, 14, 3985.

Human Rights Watch. (2023). *Bangladesh: Protect People Most at Risk During Monsoon Season*. https://www.hrw.org/news/2023/06/19/bangladesh-protect-people-most-risk-during-monsoon-season

Protomaps. *PMTiles: a single-file archive format for tiled data*. https://protomaps.com/

UNDRR. (2023). *Global Survey Report on Persons with Disabilities and Disasters*. https://www.undrr.org/report/2023-gobal-survey-report-on-persons-with-disabilities-and-disasters

Xia, J., Falconer, R. A., Xiao, X., & Wang, Y. (2014). Criterion of vehicle stability in floodwaters based on theoretical and experimental studies. *Natural Hazards*, 70, 1619–1630.

Journal of Hydrology. (2025). An overview of flood evacuation planning: models, methods and future directions. https://doi.org/10.1016/j.jhydrol.2025.133026
