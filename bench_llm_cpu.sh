#!/bin/bash
# Reproduces every CPU-side LLM optimization claim in WRITEUP.md's "The ARM
# Optimization Story" (items 3-5): KleidiAI vs. native repack, the
# GGML_VK_VISIBLE_DEVICES=99 decode win, 3-vs-4 threads, Q4_0 vs. K-quants,
# and speculative decoding. Run on the Pi:
#
#   bash bench_llm_cpu.sh
#
# Requires both llama.cpp builds already present at the paths below (one
# built with -DGGML_CPU_KLEIDIAI=ON, one without), the production model,
# the Q3_K_M/Q4_K_M variants (download from the same HuggingFace repo, do
# not requantize from Q4_0 -- that compounds quantization error), and the
# 1B draft model. Writes raw llama-bench output to bench_llm_cpu.log and
# the speculative-decoding server log to spec_decode.log, both in this
# directory. Stop any kiosk/display process first to remove GPU contention.
set -u
RES=/root/v3d-research
NATIVE_BIN="$RES/llama.cpp/build-vulkan/bin/llama-bench"
KLEIDI_BIN="$RES/llama.cpp/build-kleidi/bin/llama-bench"
MODEL="$RES/models/granite-4.1-3b-Q4_0.gguf"
OUT="$(dirname "$0")/bench_llm_cpu.log"

: > "$OUT"
log() { echo "$@" | tee -a "$OUT"; }

log "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) — $(cat /proc/device-tree/model 2>/dev/null || echo unknown board) ==="
log ""

log "--- KleidiAI vs native repack (GGML_VK_VISIBLE_DEVICES=99, -ngl 0, -t 3, r=5) ---"
log "[native]"
GGML_VK_VISIBLE_DEVICES=99 "$NATIVE_BIN" -m "$MODEL" -p 128 -n 64 -t 3 -ngl 0 -r 5 2>&1 | tee -a "$OUT"
log "[kleidiai]"
GGML_VK_VISIBLE_DEVICES=99 "$KLEIDI_BIN" -m "$MODEL" -p 128 -n 64 -t 3 -ngl 0 -r 5 2>&1 | tee -a "$OUT"
log ""

log "--- GGML_VK_VISIBLE_DEVICES=99 decode win (native build, -ngl 0 both sides, -t 3, r=5) ---"
log "[vulkan device visible]"
"$NATIVE_BIN" -m "$MODEL" -p 128 -n 64 -t 3 -ngl 0 -r 5 2>&1 | tee -a "$OUT"
log "[vulkan device hidden]"
GGML_VK_VISIBLE_DEVICES=99 "$NATIVE_BIN" -m "$MODEL" -p 128 -n 64 -t 3 -ngl 0 -r 5 2>&1 | tee -a "$OUT"
log ""

log "--- 3 vs 4 threads (native build, GPU hidden, -ngl 0, r=5) ---"
log "[t=3]"
GGML_VK_VISIBLE_DEVICES=99 "$NATIVE_BIN" -m "$MODEL" -p 128 -n 64 -t 3 -ngl 0 -r 5 2>&1 | tee -a "$OUT"
log "[t=4]"
GGML_VK_VISIBLE_DEVICES=99 "$NATIVE_BIN" -m "$MODEL" -p 128 -n 64 -t 4 -ngl 0 -r 5 2>&1 | tee -a "$OUT"
log ""

Q3KM="$RES/models/granite-4.1-3b-Q3_K_M.gguf"
Q4KM="$RES/models/granite-4.1-3b-Q4_K_M.gguf"
log "--- Q4_0 vs K-quants (native build, GPU hidden, -ngl 0, -t 3, r=5) ---"
log "[Q4_0]"
GGML_VK_VISIBLE_DEVICES=99 "$NATIVE_BIN" -m "$MODEL" -p 128 -n 64 -t 3 -ngl 0 -r 5 2>&1 | tee -a "$OUT"
log "[Q3_K_M]"
GGML_VK_VISIBLE_DEVICES=99 "$NATIVE_BIN" -m "$Q3KM" -p 128 -n 64 -t 3 -ngl 0 -r 5 2>&1 | tee -a "$OUT"
log "[Q4_K_M]"
GGML_VK_VISIBLE_DEVICES=99 "$NATIVE_BIN" -m "$Q4KM" -p 128 -n 64 -t 3 -ngl 0 -r 5 2>&1 | tee -a "$OUT"
log ""

# NOTE: llama-speculative-simple hung silently at dual-model warmup on this
# build (no crash, no OOM, just dead after several minutes -- a real tool
# incompatibility, reproduced twice). Use llama-server -md instead, the tool
# the original 2026-07-12 pass used, and drive it with a real chat
# completion. Its acceptance/timing stats print to the server's own log.
SERVER_BIN="$RES/llama.cpp/build-vulkan/bin/llama-server"
DRAFT="$RES/models/granite-4.0-1b-dense/granite-4.0-1b-Q4_0.gguf"
SPEC_LOG="$(dirname "$0")/spec_decode.log"
log "--- Speculative decoding: 1B drafts for 3B (native build, GPU hidden, -ngl 0, -t 3/-td 3) ---"
log "baseline (non-speculative) tg64 is the [t=3] result from the thread-count section above"

GGML_VK_VISIBLE_DEVICES=99 "$SERVER_BIN" -m "$MODEL" -md "$DRAFT" \
  -ngl 0 -ngld 0 -t 3 -td 3 -c 4096 --host 127.0.0.1 --port 8082 \
  > "$SPEC_LOG" 2>&1 &
SERVER_PID=$!

for _ in $(seq 1 20); do
  st=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8082/health 2>/dev/null)
  [ "$st" = "200" ] && break
  sleep 5
done

if [ "$st" = "200" ]; then
  curl -s -m 90 http://127.0.0.1:8082/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"messages":[{"role":"user","content":"Write a short area advisory: one sentence for wheelchair users, one for drivers, one on shelters. Still water is 0.42 m, band D2. Coverage: 12% under 0.3 m, 8% between 0.3 and 0.5 m, 3% between 0.5 and 1.2 m."}],"max_tokens":128,"temperature":0}' \
    -o /dev/null -w "chat completion: HTTP %{http_code} in %{time_total}s\n" | tee -a "$OUT"
else
  log "speculative server never became healthy (last status: $st)"
fi

kill "$SERVER_PID" 2>/dev/null
grep -E "draft acceptance|print_timing" "$SPEC_LOG" | tee -a "$OUT"
log "(full server log: $SPEC_LOG)"

log ""
log "=== done, raw output in $OUT ==="
