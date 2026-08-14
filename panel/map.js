/* Bonbibi panel — MAP screen. Reuses the real map.html (MapLibre + PMTiles
   + the same server-generated flood-image overlay the desktop console
   uses) in an iframe, with panel-native chrome around it: Jersey/Phthalo
   header, discrete pan/zoom controls (native touch drag/pinch still works
   too -- this is additive, per README §8's "no gesture-only" rule, not a
   lockout), and a status line carrying the same facts as the map. */

const $ = (id) => document.getElementById(id);

async function loadArea() {
  const areas = await (await fetch("/api/areas")).json();
  const withBasemap = areas.filter((a) => a.basemap);
  const area = withBasemap.find((a) => a.name === "redhook") || withBasemap[0] || areas[0];
  if (!area) {
    $("map-status").textContent = "No offline basemap loaded for this device.";
    return null;
  }
  $("map-title").textContent = `MAP — ${area.name}`;
  $("map-frame").src = `/app/static/map.html?chrome=0&area=${area.name}&bbox=${area.bbox.join(",")}`;
  return area;
}

function sendToMap(msg) {
  $("map-frame").contentWindow.postMessage(msg, "*");
}

for (const [id, action] of [
  ["ctl-zoomin", "zoom-in"],
  ["ctl-zoomout", "zoom-out"],
]) {
  $(id).addEventListener("click", () => sendToMap({ type: "bonbibi:map-control", action }));
}
for (const [id, dx, dy] of [
  ["ctl-up", 0, -80],
  ["ctl-down", 0, 80],
  ["ctl-left", -80, 0],
  ["ctl-right", 80, 0],
]) {
  $(id).addEventListener("click", () => sendToMap({ type: "bonbibi:map-control", action: "pan", dx, dy }));
}

$("map-back").addEventListener("click", () => {
  location.href = "/panel/index.html";
});

window.addEventListener("message", async (e) => {
  if (!e.data || e.data.type !== "bonbibi:tap") return;
  $("map-status").textContent = "Routing from this location…";
  const r = await fetch("/api/locate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat: e.data.lat, lon: e.data.lon }),
  });
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    $("map-status").textContent = body.detail || "Could not route from there.";
    return;
  }
  const { routes } = await r.json();
  const best = ["foot", "vehicle", "wheelchair"]
    .map((k) => routes[k])
    .find((route) => route && route.possible);
  $("map-status").textContent = best
    ? best.summary
    : "No shelter is reachable from this location without crossing water above every profile's limit.";
});

loadArea();
