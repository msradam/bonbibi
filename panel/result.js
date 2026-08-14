/* Bonbibi panel — RESULT screen.
   Live-wires the depth gauge (marker position, active band, status
   chip, verdict) from real /api/state + /api/thresholds data.

   NOT yet wired: source/location/timeline/shelter/route text. Those
   describe a SPECIFIC person's routed result (from /api/locate, which
   needs a tapped lat/lon on the interactive map) — this panel has no
   map, so which location it should always check (the install site
   itself? a fixed community reference point?) is a product decision,
   not something to guess here. Left as the reference's demo content
   until that's answered. */

const $ = (id) => document.getElementById(id);

const GAUGE_PX_PER_M =
  parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--depth-gauge-body-block-size")) /
  parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--depth-gauge-scale-max-m"));

const BAND_EDGES = { d0: 0.1, d1: 0.3, d2: 0.5, d3: 1.2 }; // metres; matches tokens.json semantic.depth ranges

function bandFor(depthM) {
  if (depthM < BAND_EDGES.d0) return "D0";
  if (depthM < BAND_EDGES.d1) return "D1";
  if (depthM < BAND_EDGES.d2) return "D2";
  if (depthM < BAND_EDGES.d3) return "D3";
  return "D4";
}

function buildTicks() {
  const el = $("gauge-ticks");
  el.innerHTML = "";
  for (let i = 0; i <= 24; i++) {
    const m = i * 0.05;
    const y = Math.round(m * GAUGE_PX_PER_M);
    const major = Math.abs(m % 0.5) < 1e-9;
    const mid = Math.abs(m % 0.1) < 1e-9;
    const len = major ? 16 : mid ? 10 : 6; // rank by length, never colour — README §6
    const tick = document.createElement("div");
    tick.style.insetBlockStart = `${y}px`;
    tick.style.insetInlineStart = `${50 - len}px`;
    tick.style.inlineSize = `${len}px`;
    tick.style.blockSize = "2px";
    el.appendChild(tick);
    if (major && i > 0) {
      const num = document.createElement("div");
      num.className = "gauge__tick-num";
      num.style.insetBlockStart = `${y - 11}px`;
      num.textContent = m.toFixed(2);
      el.appendChild(num);
    }
  }
}

function setDepth(depthM) {
  const band = bandFor(depthM);
  $("depth-value").textContent = depthM.toFixed(2);
  $("hazard-band").textContent = band;

  const y = Math.round(depthM * GAUGE_PX_PER_M);
  $("marker-outer").style.insetBlockStart = `${y - 3}px`;
  $("marker-core").style.insetBlockStart = `${y - 1}px`;
  $("marker-tab").style.insetBlockStart = `${y - 5}px`;
  $("marker-outer").setAttribute("data-water-surface", depthM.toFixed(2));
  $("marker-outer").setAttribute("aria-label", `Measured depth ${depthM.toFixed(2)} metres`);
  $("gauge").setAttribute("aria-label", `Depth gauge. Measured water ${depthM.toFixed(2)} metres, band ${band}.`);
}

function setVerdict(depthM, thresholds) {
  if (!thresholds) return;
  // Carry the engine key through the DOM (README §10's A4 lesson) — the
  // profile that's still passable, resolved from the real threshold
  // constant, not a display string.
  const passable = ["wheelchair", "vehicle", "foot"].filter((p) => depthM <= thresholds[p]);
  const banner = $("verdict-banner");
  if (passable.length === 0) {
    banner.dataset.statusChip = "danger";
    $("verdict-text").textContent = "NOT PASSABLE";
  } else {
    banner.dataset.statusChip = "safe";
    $("verdict-text").textContent = `PASSABLE ${passable[passable.length - 1].toUpperCase()}`;
  }

  const nearest = Math.min(...Object.values(thresholds).map((t) => Math.abs(t - depthM)));
  const chip = $("status-chip");
  chip.dataset.statusChip = nearest < 0.05 ? "warning" : "safe";
  $("status-chip-text").textContent = nearest < 0.05 ? "APPROACHING LIMIT" : "WITHIN LIMITS";
}

async function poll() {
  const [state, thresholds] = await Promise.all([
    fetch("/api/state").then((r) => r.json()),
    fetch("/api/thresholds").then((r) => r.json()),
  ]);
  const depthM = state.coverage ? state.coverage.max_depth_m : null;
  if (depthM != null) {
    setDepth(depthM);
    setVerdict(depthM, thresholds);
  }
}

const params = new URLSearchParams(location.search);
const mode = params.get("mode");
if (mode) document.querySelector(".frame").dataset.mode = mode;

buildTicks();
poll();
setInterval(poll, 2000);
