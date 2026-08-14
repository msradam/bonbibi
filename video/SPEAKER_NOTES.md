Speaker notes for `out/bonbibi_submission.mp4` (2:58). The video itself is silent (a slide deck spliced with screen capture, no voiceover); these are the talking points for presenting it live or recording a voiceover later, written the way you'd actually say them out loud, not a restatement of the on-screen text. Timestamps mark where each beat should land.

**0:00: Title**
Hi, I'm Adam. This is Bonbibi, a flood guidance station that runs entirely offline on a Raspberry Pi 5. Built for the Arm Create AI Optimization Challenge, Physical AI track.

**0:12: Hook**
Here's the problem: when the network goes down in a flood, that's exactly when people need routing the most.

**0:17: UNDRR stat**
The UNDRR surveyed over six thousand people with disabilities across 132 countries. Only 26% could evacuate immediately without difficulty, but give them warning and that jumps to 39%. Without warning, 10% couldn't evacuate at all. With it, that drops to 6%.

**0:29: Thesis**
So warning works. The missing half is routing, and the places that flood worst are exactly the places where connectivity fails first. This isn't a niche problem: 1.8 billion people face significant flood risk, and 89% of them live in low- and middle-income countries.

**0:38: Article screenshot**
And this isn't hypothetical. This is a real Human Rights Watch report from June 2023.

**0:43: Bangladesh case**
141 people were killed in the June 2022 floods in northeastern Bangladesh. People with disabilities and older people died disproportionately, not because the water found them first, but because the shelters weren't accessible and the warnings never reached them. One survivor, Mohammad Sher Uddin, put it plainly: "We were not prepared because we did not receive any warnings."

**0:56: Transition**
So let's see what we built. This is live, running on a Raspberry Pi 5, no internet connection.

**1:01: Demo: the panel**
This is the panel itself, the physical kiosk. It runs a real self-test on boot: simulation, routing, and the narration model. Tap "run flood check" and it kicks off the actual GPU simulation.

**1:16: Demo: console storm**
Here's the same engine on the desktop console, running a storm over Red Hook, Brooklyn. Those hazard bands are draped over a real offline basemap, and the water-depth breakdown updates live as the simulation runs.

**1:35: Demo: routes diverge**
Now tap a location and the system routes a person to the nearest shelter, separately for each mobility profile. Watch what happens: the wheelchair route comes back "stranded" where the vehicle and foot routes don't, because the flood depth crosses a different safety threshold for each one.

**1:54: How it works**
So how does this actually work? One board, two engines, running at the same time. The GPU simulates the flood. Four Arm cores route people and narrate the result. At the same time.

**2:02: GPU kernel**
The flood kernel itself was optimized by an LLM, but inside a correctness gate. A finite-state machine owns the whole compile, verify, benchmark, keep-or-revert loop, so a kernel that breaks the physics literally cannot produce a benchmark number. That gate-verified process got us a 1.59x speedup, and under concurrent LLM decode, that advantage actually grows to 2.09x.

**2:13: Concurrency table**
Here's the proof the split is worth it: the GPU-plus-CPU deployment beats the best CPU-only alternative on both axes at once, more flood throughput and more decode throughput than partitioning, oversubscribing, or time-slicing the same cores.

**2:19: Arm specifics intro**
Now the Arm-specific part: three findings that only show up once you actually benchmark the board instead of assuming.

**2:25: KleidiAI**
First: Arm's own KleidiAI library loses to the native runtime-repack path on this chip. The Cortex-A76 doesn't have i8mm or SVE, so KleidiAI never reaches its best kernels here. llama.cpp's own dotprod repack path wins, by close to 40% on prompt processing.

**2:34: The Vulkan bug**
Second, a real bug: if a Vulkan device is visible at all, llama.cpp pins the CPU's weights in GPU write-combined memory, even when you tell it to use zero GPU layers. One environment variable fixes it, and it's worth 10.6x on prompt processing. Not the 22% an earlier pass measured on a smaller model, the real number, on the production model.

**2:45: Q4_0 vs. everything**
Third: Q4_0 beats every K-quant we tried, and it beats speculative decoding too. Speculative decoding sounds like a free win, but on four shared cores the draft model just competes for the same memory bandwidth the target needs, so it's 6% slower, not faster. We measured it, and rejected it.

**2:52: Closing**
That's Bonbibi. MIT licensed, and every number in this video has its source cited in the repo. Arm AI Optimization Challenge 2026, Physical AI track. Thanks for watching.
