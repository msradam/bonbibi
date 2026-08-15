# GPU kernel: optimization evidence

Raw evidence for the GPU-side claims in `WRITEUP.md`'s "ARM Optimization
Story" and `BENCHMARK_RESULTS.md`: the correctness-gated, LLM-driven
search that found the winning flood kernel (`shaders/fused2s.comp`,
1.59x over the original two-pass stencil, 2.09x under concurrent CPU
decode), and the counterfactual proving that split beats every
CPU-only scheduling scheme tested.

- **`paper.pdf`**: the full technical writeup, methodology, and every
  number's reproduction command.
- **`optimization_session/`**: one real session of the correctness-gate
  in action, a finite-state machine served over MCP that lets a model
  propose kernel and host-contract changes, owns compile, verify,
  benchmark, and keep/revert itself, and refuses out-of-order
  transitions. `summary.md` is the human-readable digest;
  `ledger_responses.json` is the full machine-generated ledger,
  every proposed shader variant, its verdict, and its measured
  steps/s, unedited.
- **`benchmarks/concurrency/`**: the optimized kernel and the original
  kernel, each run alone and concurrently against the CPU narrator,
  raw `vkflood2`/`llama-bench` output plus thermal traces
  (`thermal_*.log`), steady-state, cool starts.
- **`benchmarks/cpu_only_counterfactual/`**: the same physics as a
  gate-verified OpenMP build, run partitioned and oversubscribed
  against concurrent CPU decode, the comparison that shows the GPU
  split dominates every CPU-only scheduling alternative.
- **`benchmarks/hardware_specs/`**: `vulkaninfo` and `vcgencmd` output
  from the board these numbers were measured on.
