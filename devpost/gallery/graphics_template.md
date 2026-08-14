---
marp: true
paginate: false
---

<style>
@font-face {
  font-family: 'Jersey 20';
  src: url(data:font/woff2;base64,__JERSEY20__) format('woff2');
}
@font-face {
  font-family: 'Jersey 25';
  src: url(data:font/woff2;base64,__JERSEY25__) format('woff2');
}
@font-face {
  font-family: 'Noto Sans';
  src: url(data:font/woff2;base64,__NOTOSANS__) format('woff2');
}

:root {
  --phthalo: #123524;
  --phthalo-mid: #1f5b3e;
  --shamrock: #50c38b;
  --jade: #39a772;
  --paper: #F5F5F1;
  --danger: #e0574a;
}

section {
  background: var(--phthalo);
  color: var(--paper);
  font-family: 'Noto Sans', sans-serif;
  padding: 60px 90px;
  justify-content: center;
}
section h1, section h2, section h3, section p, section div {
  color: var(--paper);
}

.kicker {
  font-family: 'Jersey 20', monospace;
  font-size: 20px;
  color: var(--shamrock);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-bottom: 20px;
}
.big-title {
  font-size: 42px;
  font-weight: 700;
  line-height: 1.25;
  max-width: 1000px;
  margin: 0 0 40px 0;
}

/* architecture diagram */
.arch-row { display: flex; gap: 50px; align-items: stretch; }
.arch-box {
  flex: 1;
  border: 2px solid var(--shamrock);
  border-radius: 4px;
  padding: 30px;
}
.arch-box h3 {
  font-family: 'Jersey 25', monospace;
  font-size: 28px;
  color: var(--shamrock);
  margin: 0 0 16px 0;
}
.arch-box ul { margin: 0; padding-left: 22px; font-size: 18px; line-height: 1.6; }
.arch-box li { margin-bottom: 6px; }
.arch-join {
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Jersey 20', monospace;
  font-size: 20px;
  color: var(--paper);
  padding: 0 6px;
  text-align: center;
}
.arch-footer {
  margin-top: 34px;
  font-family: 'Jersey 20', monospace;
  font-size: 18px;
  color: var(--shamrock);
  letter-spacing: 0.03em;
  text-transform: uppercase;
}

/* thresholds infographic */
.thresh-row { display: flex; gap: 60px; }
.thresh-col { flex: 1; }
.thresh-col h3 {
  font-family: 'Jersey 20', monospace;
  font-size: 20px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin: 0 0 18px 0;
}
.thresh-col.before h3 { color: var(--danger); }
.thresh-col.after h3 { color: var(--shamrock); }
.thresh-item {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  border-bottom: 1px solid rgba(245,245,241,0.25);
  padding: 12px 0;
  font-size: 19px;
}
.thresh-item .val {
  font-family: 'Jersey 25', monospace;
  font-size: 28px;
}
.before .thresh-item .val { color: var(--danger); }
.after .thresh-item .val { color: var(--shamrock); }
.thresh-note {
  margin-top: 32px;
  font-size: 19px;
  max-width: 950px;
  line-height: 1.5;
}
.cite {
  font-family: 'Jersey 20', monospace;
  font-size: 16px;
  color: var(--shamrock);
  letter-spacing: 0.02em;
  text-transform: uppercase;
  margin-top: 26px;
  opacity: 0.9;
}
</style>

<div class="kicker">How it works</div>
<div class="big-title">One board, two engines, running at the same time.</div>

<div class="arch-row">
  <div class="arch-box">
    <h3>GPU: VideoCore V3D</h3>
    <ul>
      <li>WCA2D overland-flow simulation over real elevation data</li>
      <li>Vulkan compute kernel, LLM-optimized inside a correctness gate</li>
      <li>1.59x over the original two-pass stencil</li>
      <li>Verified every run: NMSE vs. a double-precision CPU reference, mass conservation</li>
    </ul>
  </div>
  <div class="arch-join">+<br>same<br>board</div>
  <div class="arch-box">
    <h3>CPU: 4&times; Cortex-A76</h3>
    <ul>
      <li>Deterministic BFS routing, one verdict per mobility profile</li>
      <li>Granite 4.1 3B narrates the computed result, grounded, never decides</li>
      <li>The web console and kiosk UI</li>
      <li>Arm-specific tuning: native repack, hidden Vulkan device, Q4_0</li>
    </ul>
  </div>
</div>

<div class="arch-footer">$80 Raspberry Pi 5, fully offline, no cloud</div>

---

<div class="kicker">Research corrected an assumption</div>
<div class="big-title">The thresholds I guessed were wrong, so the shipped system uses the literature's numbers.</div>

<div class="thresh-row">
  <div class="thresh-col before">
    <h3>Originally guessed</h3>
    <div class="thresh-item"><span>Wheelchair / cannot wade</span><span class="val">0.5 m</span></div>
    <div class="thresh-item"><span>Vehicle</span><span class="val">2.0 m</span></div>
  </div>
  <div class="thresh-col after">
    <h3>Shipped (from the standards)</h3>
    <div class="thresh-item"><span>Wheelchair / cannot wade</span><span class="val">0.1 m</span></div>
    <div class="thresh-item"><span>On foot</span><span class="val">0.5 m</span></div>
    <div class="thresh-item"><span>Vehicle</span><span class="val">0.3 m</span></div>
  </div>
</div>

<div class="thresh-note">2.0 m is AIDR's "unsafe for vehicles and people" hazard class, not a safe driving depth. The guessed vehicle threshold was wrong by roughly 6x. The shipped system uses ARR Project 10 and AIDR Guideline 7-3's limiting depths instead, so cars correctly become unsafe before pedestrians do.</div>

<div class="cite">Source: Engineers Australia / Australian Rainfall and Runoff, Project 10; Australian Institute for Disaster Resilience, Guideline 7-3</div>
