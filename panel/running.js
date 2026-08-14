/* Bonbibi panel — RUNNING screen. "A determinate progress indicator
   and the stage name. Nothing else." (README §5) — no self-test, no
   exercise bar, no chrome; stress impairs cognitive inhibition, so
   irrelevant content has to be absent here, not just de-emphasised. */

const $ = (id) => document.getElementById(id);

const STAGE_TEXT = {
  starting: "Starting the storm…",
  flood: "Simulating flood on the GPU…",
  routing: "Routing mobility profiles…",
  narrating: "Composing guidance…",
  done: "Done.",
  error: "The run failed.",
};

// Cumulative weight per phase boundary. flood's own share (5-55) is
// further scaled by its real frame/frames fraction, the only stage
// with genuine sub-progress data from the backend; the others don't
// report progress within themselves, so they step rather than glide.
const PHASE_FLOOR = { starting: 0, flood: 5, routing: 55, narrating: 70, done: 100, error: 0 };

function progressFor(s) {
  const floor = PHASE_FLOOR[s.phase] ?? 0;
  if (s.phase === "flood" && s.frames) {
    return floor + (50 * s.frame) / s.frames;
  }
  return floor;
}

async function poll() {
  const s = await (await fetch("/api/state")).json();
  const pct = Math.round(progressFor(s));
  $("running-stage").textContent = s.phase === "error" && s.error
    ? `The run failed: ${s.error}`
    : STAGE_TEXT[s.phase] || "Working…";
  $("running-progress").setAttribute("aria-valuenow", String(pct));
  $("running-progress-fill").style.inlineSize = `${pct}%`;

  if (s.done && s.phase !== "error") {
    location.href = "/panel/result.html";
    return;
  }
  setTimeout(poll, 400);
}

poll();
