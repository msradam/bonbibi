/* Bonbibi console: load areas, run storms, poll state, keep every result
   readable by screen readers (status line, live guidance, labelled gauge). */

const $ = (id) => document.getElementById(id);
let areas = [];
let polling = null;

const PHASES = {
  starting: "Starting the storm...",
  flood: "Simulating flood on the GPU...",
  routing: "Routing two mobility profiles on the CPU...",
  narrating: "Granite is narrating on the CPU while the GPU keeps simulating...",
  done: "Done.",
  error: "The run failed.",
};

async function loadAreas() {
  areas = await (await fetch("/api/areas")).json();
  const sel = $("area");
  sel.innerHTML = "";
  for (const a of areas.filter((a) => a.basemap)) {
    const o = document.createElement("option");
    o.value = a.name;
    o.textContent = a.name;
    if (a.name === "redhook") o.selected = true;
    sel.append(o);
  }
  sel.addEventListener("change", setMap);
  setMap();
}

function setMap() {
  const a = areas.find((x) => x.name === $("area").value);
  if (!a) return;
  $("map").src = `/app/static/map.html?chrome=0&area=${a.name}&bbox=${a.bbox.join(",")}`;
  $("map").title = `Map of ${a.name} showing simulated flood depth and evacuation routes`;
  $("map-alt").textContent =
    `No storm has been run yet. The map shows ${a.name} with no flooding.`;
}

for (const k of ["rain", "steps"]) {
  $(k).addEventListener("input", () => ($(`${k}-out`).value = $(k).value));
}

$("storm-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const a = areas.find((x) => x.name === $("area").value);
  const r = await fetch("/api/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      dem: a.dem,
      rain: parseFloat($("rain").value),
      steps: parseInt($("steps").value, 10),
      frames: 5,
    }),
  });
  if (r.status === 409) {
    $("phase").textContent = "A storm is already running. Wait for it to finish.";
    return;
  }
  $("run").disabled = true;
  $("run").textContent = "Running...";
  $("guidance").textContent = "";
  $("guidance").classList.add("streaming");
  if (!polling) polling = setInterval(poll, 400);
});

function chip(el, route) {
  el.classList.remove("chip-empty", "chip-pass", "chip-stranded");
  if (!route) {
    el.classList.add("chip-empty");
    el.textContent = "not computed";
  } else if (route.possible) {
    el.classList.add("chip-pass");
    el.textContent = "passable";
  } else {
    el.classList.add("chip-stranded");
    el.textContent = "stranded";
  }
}

async function poll() {
  const s = await (await fetch("/api/state")).json();
  let phase = PHASES[s.phase] || "Ready. The GPU is idle.";
  if (s.phase === "flood") phase += ` (frame ${s.frame} of ${s.frames})`;
  if (s.phase === "error") phase = `The run failed: ${s.error}`;
  if ($("phase").textContent !== phase) $("phase").textContent = phase;

  if (s.coverage) {
    const c = s.coverage;
    const pct = Math.min(100, (c.max_depth_m / 3) * 100);
    $("gauge-fill").style.height = `${pct}%`;
    $("gauge").setAttribute(
      "aria-label",
      `Depth gauge. Deepest simulated water ${c.max_depth_m} metres. ` +
        `Wheelchair limit 0.5 metres, vehicle limit 2.0 metres.`
    );
    $("cov-shallow").textContent = `${c.shallow_pct}%`;
    $("cov-vehicle").textContent = `${c.vehicle_pct}%`;
    $("cov-deep").textContent = `${c.deep_pct}%`;
    $("map-alt").textContent =
      `Flood over ${$("area").value}: ${c.shallow_pct}% of the area under shallow water, ` +
      `${c.vehicle_pct}% passable by vehicle only, ${c.deep_pct}% impassable; ` +
      `deepest water ${c.max_depth_m} m.`;
  }

  if (s.routes) {
    chip($("chip-wheel"), s.routes.wheelchair);
    chip($("chip-vehicle"), s.routes.vehicle);
    $("route-wheel").textContent = s.routes.wheelchair.summary;
    $("route-vehicle").textContent = s.routes.vehicle.summary;
  } else {
    chip($("chip-wheel"), null);
    chip($("chip-vehicle"), null);
    $("route-wheel").textContent = "Tap the map to route a person to shelter.";
    $("route-vehicle").textContent = "Tap the map to route a person to shelter.";
  }

  if (s.guidance) $("guidance").textContent = s.guidance;

  $("m-sps").textContent = s.gpu_sps ? s.gpu_sps.toLocaleString() : "—";
  $("m-steps").textContent = s.gpu_steps ? s.gpu_steps.toLocaleString() : "—";
  $("m-time").textContent = s.elapsed || "—";

  if (s.done && !s.routes && $("phase").textContent === "Done.") {
    $("phase").textContent =
      "Done. Tap the map at a person's location to guide them to shelter.";
  }
  if (s.done) {
    clearInterval(polling);
    polling = null;
    $("run").disabled = false;
    $("run").textContent = "Run the storm";
    $("guidance").classList.remove("streaming");
    if (s.guidance && "speechSynthesis" in window) {
      $("speak").hidden = false;
    }
  }
}

$("speak").addEventListener("click", () => {
  const btn = $("speak");
  if (btn.getAttribute("aria-pressed") === "true") {
    speechSynthesis.cancel();
    btn.setAttribute("aria-pressed", "false");
    btn.textContent = "Speak guidance";
    return;
  }
  const u = new SpeechSynthesisUtterance($("guidance").textContent);
  u.onend = () => {
    btn.setAttribute("aria-pressed", "false");
    btn.textContent = "Speak guidance";
  };
  speechSynthesis.speak(u);
  btn.setAttribute("aria-pressed", "true");
  btn.textContent = "Stop speaking";
});

window.addEventListener("message", async (e) => {
  if (!e.data || e.data.type !== "bonbibi:tap") return;
  $("phase").textContent = "Routing from their location...";
  $("guidance").textContent = "";
  $("guidance").classList.add("streaming");
  if (!polling) polling = setInterval(poll, 400);
  const r = await fetch("/api/locate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat: e.data.lat, lon: e.data.lon }),
  });
  if (!r.ok) {
    clearInterval(polling);
    polling = null;
    $("guidance").classList.remove("streaming");
    $("phase").textContent = (await r.json()).detail || "Could not route from there.";
  }
});

loadAreas();
poll();
