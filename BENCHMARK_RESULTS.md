# Bonbibi Benchmark Results

**Device:** Raspberry Pi 5 16GB (4× Cortex-A76 @ 2.4 GHz, VideoCore VII V3D, LPDDR4X), passively cooled
**Software:** llama.cpp `57998d5`, Mesa v3dv (Vulkan 1.3), Granite 4.1 3B Q4_0 (production narrator)
**Dates:** GPU kernel and concurrency numbers 2026-07-12; CPU LLM numbers reproduced live 2026-08-14 on the production model, kiosk stopped to remove GPU contention, cool starts

All commands to reproduce every number below are in `bench_llm_cpu.sh` (CPU/LLM) and `docs/gpu_kernel/paper.pdf` (GPU kernel). Raw output: `bench_llm_cpu.log` (llama-bench), `spec_decode.log` (speculative decoding server), and `docs/gpu_kernel/benchmarks/` (GPU kernel and concurrency logs).

## Summary

| Metric | Value |
|---|---|
| GPU flood kernel speedup (optimizer-found vs. original) | **1.59x** (1,345 → 2,140 steps/s @ 256², NMSE 1.3e-9) |
| GPU kernel speedup under concurrent CPU decode | **2.09x** (grows under load; decode keeps 90% of solo rate) |
| CPU decode win from hiding the GPU from llama.cpp | **+13.7%** decode, **10.6x** prompt processing |
| Native repack vs. KleidiAI (Arm's own library), production model | **+39.7%** prompt processing, **+14.3%** decode |
| Q4_0 vs. best K-quant, production model | **+73.9%** prompt processing, **+7.8%** decode (Q4_0 wins) |
| Speculative decoding (1B drafts 3B) vs. plain decode | **6.0% slower** (51.7% draft acceptance), rejected |
| KV-cache warming, repeat time-to-first-token | 16.0s → **0.2s** |

---

## GPU: correctness-gated kernel optimization

A Burr finite-state machine served over MCP: the model proposes kernel and host-contract changes, the machine owns compile → verify → benchmark → keep/revert, and refuses out-of-order transitions: a variant that fails physics can never produce a benchmark number. One real session, full ledger included: `docs/gpu_kernel/optimization_session/`.

| Kernel | steps/s @ 256² | vs. baseline | NMSE vs. CPU reference |
|---|---|---|---|
| Original two-pass stencil | 1,345 | n/a | pass |
| Optimizer-found (fused, strip-mined) | 2,140 | **1.59x** | 1.3e-9 (pass, 4,000 steps) |

A falsification sweep attributed the original cost to fixed per-invocation overhead, not memory traffic; the winning kernel fuses the two passes and strip-mines two cells per invocation. The machine also independently refused to benchmark a deliberately mass-violating kernel: the correctness gate held under an adversarial test.

## GPU + CPU concurrency counterfactual

| Condition | GPU flood (steps/s) | CPU decode (t/s) |
|---|---|---|
| Optimized kernel alone | 2,127 | n/a |
| Decode alone (1B, GPU hidden) | n/a | 11.5 |
| **Concurrent (deployment config)** | **712** | **10.3** |
| Best CPU-only alternative (core partitioning) | 681 | 8.4 |
| Oversubscribed CPU-only | n/a | decode collapses 79% |

The GPU+CPU split dominates every CPU-only scheduling alternative tested (partitioned, oversubscribed, time-sliced) on both axes simultaneously. This is the concurrency claim's counterfactual, not just a single measured number.

---

## CPU: the Arm-specific LLM optimization ledger

Reproduced 2026-08-14 against the actual production model (`granite-4.1-3b-Q4_0.gguf`), CPU-only (`-ngl 0` on every run; an earlier draft of this run omitted it and silently offloaded to the GPU's Vulkan backend on one test, producing a nonsense number, caught and fixed), `-t 3`, `r=5`, kiosk/display stopped to remove GPU contention from the measurement.

### 1. Hiding the GPU from CPU-only inference (`GGML_VK_VISIBLE_DEVICES=99`)

| Config | pp128 (t/s) | tg64 (t/s) |
|---|---|---|
| Vulkan device visible (`-ngl 0`) | 2.12 ± 0.00 | 4.16 ± 0.51 |
| Vulkan device hidden | 22.39 ± 0.12 | 4.73 ± 0.02 |
| **Delta** | **10.6x** | **+13.7%** |

With any Vulkan device visible, llama.cpp places CPU weights in GPU host-pinned write-combined memory even at `-ngl 0`: fast for a GPU to write, bad for a CPU to read repeatedly during batched matmul. An earlier pass on a smaller model measured only the decode effect (+22%); prompt processing turns out to be the much larger, previously unmeasured half of this bug. Any Arm board with an integrated GPU running llama.cpp CPU-only should set this.

### 2. Native repack vs. Arm KleidiAI

| Build | pp128 (t/s) | tg64 (t/s) |
|---|---|---|
| Native (`REPACK=1, DOTPROD=1`) | 31.16 ± 0.44 | 5.35 ± 0.28 |
| KleidiAI (`-DGGML_CPU_KLEIDIAI=ON`) | 22.31 ± 0.35 | 4.68 ± 0.04 |
| **Native wins by** | **39.7%** | **14.3%** |

The Cortex-A76 has no i8mm/SVE, so it never reaches KleidiAI's best kernels; llama.cpp's own aarch64 dotprod repack path is faster on this exact core. Verified on the production model, not a smaller stand-in. Kept native.

### 3. Q4_0 vs. K-quants

| Quant | Size | pp128 (t/s) | tg64 (t/s) |
|---|---|---|---|
| Q4_0 (shipped) | 1.84 GiB | 21.22 ± 0.01 | 4.69 ± 0.00 |
| Q3_K_M | 1.60 GiB | 5.97 ± 0.03 | 4.00 ± 0.07 |
| Q4_K_M | 1.95 GiB | 12.20 ± 0.04 | 4.35 ± 0.04 |

Q4_0 wins on both metrics against both K-quant variants, despite Q3_K_M being 13% smaller. K-quants pay a large prompt-processing penalty off the repack path (3.5x and 1.7x slower respectively) on top of slower decode. Kept Q4_0.

### 4. Thread count: a real tradeoff, not a clean win

| Threads | pp128 (t/s) | tg64 (t/s) |
|---|---|---|
| 3 | 21.44 ± 0.28 | **4.70 ± 0.01** |
| 4 | **25.24 ± 0.42** | 4.38 ± 0.01 |

3 threads wins decode by +7.3% but loses prompt processing by 17.7%. Production keeps `-t 3` because the interactive narration path is decode-bound; a prompt-processing-heavy workload on this same hardware should use `-t 4`. (An earlier single-run estimate claimed +12% for 3 threads on decode; this `r=5` mean is the number to cite.)

### 5. KV-cache warming

Cold time-to-first-token on a repeat request: **16.0s → 0.2s** with `cache_prompt` + `--cache-reuse 256` (prompt_n 607 → 1). Documents are ordered static-first (safety limits, then flood assessment, then per-person routes) so successive taps in the same storm share the longest cached prefix. Measured in the app: second tap 13.6s vs. 17.7s end-to-end (partial reuse; per-person docs differ).

### 6. Speculative decoding (1B drafts for 3B)

`llama-speculative-simple` hung at model warmup twice (no crash, no OOM: a real tool incompatibility with dual-model loading on this build). Switched to `llama-server -md`, the tool the original pass used, and drove it with a real chat completion request. Raw server log: `spec_decode.log`.

| Metric | Value |
|---|---|
| Draft acceptance | **51.7%** (77 accepted / 149 generated) |
| Effective decode (speculative) | 4.42 t/s |
| Baseline decode (non-speculative, same `-t 3`) | 4.70 t/s |
| **Net effect** | **6.0% slower** |

Consistent with the 2026-07-12 finding (78% acceptance, 15% slower on a different prompt): different prompt, different acceptance rate, same conclusion, on four shared cores the draft model competes for the same memory bandwidth the batch-verify step is supposed to save. Rejected on measurement, twice.

---

## Production narrator config

```
llama-server -m granite-4.1-3b-Q4_0.gguf -ngl 0 -t 3 -c 4096 \
    --jinja --cache-reuse 256 --host 127.0.0.1 --port 8081
GGML_VK_VISIBLE_DEVICES=99   # hides the GPU, see finding #1 above
```
