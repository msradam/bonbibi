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
  --paper: #F5F5F1;
}

section {
  background: var(--phthalo);
  color: var(--paper);
  font-family: 'Noto Sans', sans-serif;
  padding: 70px 90px;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.bg-band {
  position: absolute;
  top: 0; bottom: 0;
  width: 140px;
  opacity: 0.55;
}

.wordmark {
  display: flex;
  align-items: center;
  gap: 22px;
  z-index: 1;
}
.wordmark img { width: 78px; height: 78px; }
.wordmark span {
  font-family: 'Jersey 25', monospace;
  font-size: 98px;
  color: var(--paper);
  line-height: 1;
}

.tagline {
  z-index: 1;
  margin-top: 26px;
  font-size: 30px;
  color: var(--paper);
  max-width: 720px;
  line-height: 1.35;
}

.badge {
  z-index: 1;
  margin-top: 40px;
  font-family: 'Jersey 20', monospace;
  font-size: 18px;
  color: var(--shamrock);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.swatches {
  z-index: 1;
  display: flex;
  gap: 10px;
  margin-top: 34px;
}
.swatches span {
  width: 46px;
  height: 14px;
  display: inline-block;
  border-radius: 2px;
}
</style>

<div class="bg-band" style="right:0px; background:#DCE9F2;"></div>
<div class="bg-band" style="right:100px; background:#9CC4DE;"></div>
<div class="bg-band" style="right:200px; background:#4A8CBF;"></div>
<div class="bg-band" style="right:300px; background:#1F4E86;"></div>

<div class="wordmark">
  <img src="data:image/png;base64,__LEAF__" alt="">
  <span>Bonbibi</span>
</div>

<div class="tagline">Flood simulation, accessible routing, and grounded AI guidance, entirely offline, on an $80 Raspberry Pi 5.</div>

<div class="swatches">
  <span style="background:#DCE9F2"></span>
  <span style="background:#9CC4DE"></span>
  <span style="background:#4A8CBF"></span>
  <span style="background:#1F4E86"></span>
  <span style="background:#4A1E68"></span>
</div>

<div class="badge">Arm Create: AI Optimization Challenge 2026 &middot; Physical AI Track</div>
