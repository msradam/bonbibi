/* Bonbibi panel — IDLE screen. Proof-of-life is the live clock: it
   changes every second by definition, so a frozen panel is visibly
   distinguishable from a dead one, same intent as README §5. */

const $ = (id) => document.getElementById(id);

const REMEDY = {
  sim: "Simulation binary missing or not executable — rebuild vkflood2 (see README Quick start).",
  route: "No terrain data loaded — run fetch_dem.py for at least one area.",
  narrate: "Narration model unreachable — start llama-server on 127.0.0.1:8081.",
};

function tickClock() {
  $("idle-clock").textContent = new Date().toLocaleTimeString("en-GB", { hour12: false });
}

function kmExtent(bbox) {
  const [lo0, la0, lo1, la1] = bbox;
  const latMid = ((la0 + la1) / 2) * (Math.PI / 180);
  const w = Math.abs(lo1 - lo0) * 111.32 * Math.cos(latMid);
  const h = Math.abs(la1 - la0) * 111.32;
  return `${w.toFixed(1)} × ${h.toFixed(1)} km`;
}

async function loadTerrain() {
  const areas = await (await fetch("/api/areas")).json();
  const withBasemap = areas.filter((x) => x.basemap);
  const a = withBasemap.find((x) => x.name === "redhook") || withBasemap[0] || areas[0];
  if (!a) return null;
  $("idle-community").textContent = a.name;
  $("terrain-name").textContent = a.name;
  $("terrain-extent").textContent = kmExtent(a.bbox);
  return a;
}

async function loadSelftest() {
  const t = await (await fetch("/api/selftest")).json();
  const box = $("idle-selftest");
  const failed = Object.entries(t.stages).filter(([, v]) => v === "fail");

  box.dataset.statusChip = t.overall === "pass" ? "safe" : "danger";
  $("selftest-word").textContent = t.overall === "pass" ? "PASS" : "FAIL";
  $("selftest-time").textContent = `SELF-TEST ${t.checked_at}`;

  const stages = $("selftest-stages");
  stages.innerHTML = "";
  for (const [stage, result] of Object.entries(t.stages)) {
    const li = document.createElement("li");
    li.dataset.stageResult = result;
    li.textContent = `${stage.toUpperCase()} ${result.toUpperCase().replace("_", " ")}`;
    stages.appendChild(li);
  }

  const remedy = $("selftest-remedy");
  if (failed.length) {
    remedy.hidden = false;
    remedy.textContent = failed.map(([stage]) => REMEDY[stage]).filter(Boolean).join(" ");
  } else {
    remedy.hidden = true;
  }
  return t;
}

$("run-check").addEventListener("click", async () => {
  const area = await loadTerrain();
  if (!area) return;
  $("run-check").disabled = true;
  $("run-check").textContent = "STARTING…";
  const r = await fetch("/api/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dem: area.dem, rain: 0.003, steps: 400, frames: 5 }),
  });
  if (r.ok || r.status === 409) {
    location.href = "/panel/running.html";
  } else {
    $("run-check").disabled = false;
    $("run-check").textContent = "RUN FLOOD CHECK";
  }
});

$("view-map").addEventListener("click", () => {
  location.href = "/panel/map.html";
});

tickClock();
setInterval(tickClock, 1000);
loadTerrain();
loadSelftest();
setInterval(loadSelftest, 30000);
