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
  --complementary: #351222;
  --danger: #e0574a;
}

section {
  background: var(--phthalo);
  color: var(--paper);
  font-family: 'Noto Sans', sans-serif;
  padding: 55px 80px;
  justify-content: center;
}

.leaf {
  width: 0.85em;
  height: 0.85em;
  vertical-align: -0.1em;
}

section.title {
  align-items: flex-start;
}
section.title h1 {
  font-family: 'Jersey 25', monospace;
  font-size: 90px;
  margin: 0;
  line-height: 1;
  display: flex;
  align-items: center;
  gap: 18px;
}
section.title .tagline {
  font-size: 28px;
  color: var(--paper);
  margin-top: 16px;
  font-weight: 400;
}
section.title .byline {
  font-family: 'Jersey 20', monospace;
  font-size: 20px;
  color: var(--shamrock);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin-top: 34px;
  line-height: 1.6;
}

section.hook {
  align-items: flex-start;
  justify-content: center;
}
section.hook h1 {
  font-size: 48px;
  line-height: 1.28;
  font-weight: 700;
  max-width: 980px;
  margin: 0;
}
section.hook .accent { color: var(--shamrock); }

section.stat {
  align-items: flex-start;
}
section.stat .stat-row {
  display: flex;
  gap: 60px;
}
section.stat .stat-block { max-width: 420px; }
section.stat .stat-num {
  font-family: 'Jersey 25', monospace;
  font-size: 112px;
  line-height: 1;
  color: var(--shamrock);
  white-space: nowrap;
}
section.stat .stat-num .arrow { color: var(--paper); font-size: 0.5em; margin: 0 10px; }
section.stat .stat-cap {
  font-size: 22px;
  color: var(--paper);
  margin-top: 14px;
  max-width: 380px;
  line-height: 1.35;
}
section.stat .stat-footer {
  font-size: 40px;
  color: var(--paper);
  margin-top: 40px;
  max-width: 920px;
  line-height: 1.45;
}
section.stat .stat-footnote {
  font-family: 'Jersey 20', monospace;
  font-size: 18px;
  color: var(--shamrock);
  letter-spacing: 0.03em;
  margin-top: 20px;
  text-transform: uppercase;
}

section.transition {
  align-items: center;
  justify-content: center;
  text-align: center;
}
section.transition h1 {
  font-family: 'Jersey 25', monospace;
  font-size: 58px;
  margin: 0;
}
section.transition .sub {
  font-family: 'Jersey 20', monospace;
  font-size: 22px;
  color: var(--shamrock);
  margin-top: 16px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

section.section-head {
  align-items: flex-start;
  justify-content: center;
}
section.section-head .kicker {
  font-family: 'Jersey 20', monospace;
  font-size: 20px;
  color: var(--shamrock);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 16px;
}
section.section-head h1 {
  font-size: 46px;
  line-height: 1.28;
  font-weight: 700;
  max-width: 980px;
  margin: 0;
}
section.section-head p {
  font-size: 23px;
  max-width: 800px;
  line-height: 1.5;
  margin-top: 20px;
}

section.metric {
  align-items: flex-start;
}
section.metric .kicker {
  font-family: 'Jersey 20', monospace;
  font-size: 18px;
  color: var(--shamrock);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-bottom: 24px;
}
section.metric .metric-row {
  display: flex;
  gap: 55px;
}
section.metric .metric-block { max-width: 380px; }
section.metric .metric-num {
  font-family: 'Jersey 25', monospace;
  font-size: 92px;
  line-height: 1;
  color: var(--shamrock);
  white-space: nowrap;
}
section.metric .metric-num.warn { color: var(--danger); }
section.metric .metric-label {
  font-size: 18px;
  color: var(--paper);
  margin-top: 10px;
  max-width: 360px;
  line-height: 1.35;
  text-transform: uppercase;
  font-family: 'Jersey 20', monospace;
  letter-spacing: 0.02em;
}
section.metric .metric-note {
  font-size: 21px;
  color: var(--paper);
  margin-top: 40px;
  max-width: 820px;
  line-height: 1.55;
}

section.table-slide table,
section.table-slide thead,
section.table-slide tbody,
section.table-slide tr,
section.table-slide th,
section.table-slide td {
  background: transparent !important;
}
section.table-slide table {
  font-family: 'Jersey 25', monospace;
  font-size: 26px;
  border-collapse: collapse;
  width: 100%;
  max-width: 980px;
  margin-top: 20px;
}
section.table-slide th {
  font-family: 'Jersey 20', monospace;
  font-weight: 400;
  text-align: right;
  padding: 10px 20px;
  border-bottom: 3px solid var(--paper);
  font-size: 18px;
  letter-spacing: 0.03em;
}
section.table-slide th:first-child { text-align: left; }
section.table-slide td {
  padding: 13px 20px;
  text-align: right;
}
section.table-slide td:first-child {
  text-align: left;
  font-family: 'Jersey 20', monospace;
  font-size: 18px;
  letter-spacing: 0.02em;
}
section.table-slide tr.win td { color: var(--shamrock); }
section.table-slide .note {
  font-size: 21px;
  margin-top: 34px;
  max-width: 820px;
  line-height: 1.55;
}

section.closing {
  align-items: center;
  justify-content: center;
  text-align: center;
}
section.closing h1 {
  font-family: 'Jersey 25', monospace;
  font-size: 86px;
  display: flex;
  align-items: center;
  gap: 16px;
  justify-content: center;
  margin: 0;
}
section.closing .repo {
  font-size: 24px;
  margin-top: 20px;
}
section.closing .event {
  font-family: 'Jersey 20', monospace;
  font-size: 18px;
  color: var(--shamrock);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin-top: 14px;
}

section h1, section h2, section h3, section p, section div, section table, section th, section td {
  color: var(--paper);
}

.cite {
  font-family: 'Jersey 20', monospace;
  font-size: 16px;
  color: var(--shamrock);
  letter-spacing: 0.02em;
  text-transform: uppercase;
  margin-top: 28px;
  opacity: 0.9;
  max-width: 900px;
  line-height: 1.5;
}

section.article-shot {
  align-items: center;
  justify-content: center;
  text-align: center;
}
section.article-shot .kicker {
  font-family: 'Jersey 20', monospace;
  font-size: 20px;
  color: var(--shamrock);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-bottom: 24px;
}
section.article-shot img {
  max-height: 570px;
  max-width: 780px;
  border: 3px solid var(--shamrock);
  box-shadow: 0 0 0 10px var(--phthalo-mid);
  object-fit: contain;
  background: var(--paper);
}
section.article-shot .cite {
  margin-top: 26px;
  max-width: 900px;
  text-align: center;
}

section.case {
  align-items: flex-start;
}
section.case .kicker {
  font-family: 'Jersey 20', monospace;
  font-size: 18px;
  color: var(--shamrock);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-bottom: 20px;
}
section.case .case-num {
  font-family: 'Jersey 25', monospace;
  font-size: 100px;
  line-height: 1;
  color: var(--shamrock);
}
section.case .case-label {
  font-size: 18px;
  font-family: 'Jersey 20', monospace;
  text-transform: uppercase;
  color: var(--paper);
  margin-top: 10px;
  letter-spacing: 0.02em;
  max-width: 800px;
  line-height: 1.4;
}
section.case .case-note {
  font-size: 21px;
  color: var(--paper);
  margin-top: 26px;
  max-width: 820px;
  line-height: 1.5;
}
section.case .quote {
  font-size: 26px;
  font-style: italic;
  color: var(--paper);
  max-width: 850px;
  line-height: 1.5;
  margin-top: 26px;
  border-left: 4px solid var(--shamrock);
  padding-left: 22px;
}
section.case .quote-attr {
  font-size: 15px;
  font-family: 'Jersey 20', monospace;
  color: var(--shamrock);
  margin-top: 8px;
  margin-left: 26px;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}
</style>

<!-- _class: title -->

<h1><img class="leaf" src="data:image/png;base64,__LEAF__"> Bonbibi</h1>

<div class="tagline">Flood guidance, entirely offline, on a Raspberry Pi 5.</div>

<div class="byline">Adam Munawar Rahman<br>Arm Create: AI Optimization Challenge 2026, Physical AI Track</div>

---

<!-- _class: hook -->

# When the network goes down in a flood, <span class="accent">routing still has to work.</span>

---

<!-- _class: stat -->

<div class="stat-row">
  <div class="stat-block">
    <div class="stat-num">26<span style="font-size:0.5em">%</span><span class="arrow">&rarr;</span>39<span style="font-size:0.5em">%</span></div>
    <div class="stat-cap">of disabled evacuees could leave immediately, with warning</div>
  </div>
  <div class="stat-block">
    <div class="stat-num">10<span style="font-size:0.5em">%</span><span class="arrow">&rarr;</span>6<span style="font-size:0.5em">%</span></div>
    <div class="stat-cap">could not evacuate at all, with warning</div>
  </div>
</div>

<div class="stat-footnote">UNDRR 2023 global survey, 6,342 respondents, 132 countries</div>

---

<!-- _class: stat -->

<div class="stat-footer">
Warning works. <strong style="color:var(--shamrock)">Routing is the missing half</strong>, especially where connectivity fails first.
</div>

<div class="stat-footnote" style="margin-top:34px;">1.81 BILLION PEOPLE FACE SIGNIFICANT FLOOD RISK, 89% IN LOW- AND MIDDLE-INCOME COUNTRIES</div>

<div class="cite">Source: World Bank / Nature Communications, 2022</div>

---

<!-- _class: article-shot -->

<div class="kicker">This is not a hypothetical.</div>

<img src="hrw_article.png" alt="Human Rights Watch article: Bangladesh, Protect People Most at Risk During Monsoon Season">

<div class="cite">Human Rights Watch, hrw.org, June 19, 2023</div>

---

<!-- _class: case -->

<div class="kicker">What the report found</div>

<div class="case-num">141</div>
<div class="case-label">people killed in flash floods, June 15&ndash;28, 2022 (government data)</div>

<div class="case-note">People with disabilities and older people died disproportionately: inaccessible shelters, warnings that never reached them.</div>

<div class="quote">&ldquo;We were not prepared because we did not receive any warnings.&rdquo;</div>
<div class="quote-attr">Mohammad Sher Uddin, 50, disabled flood survivor, Sylhet</div>

<div class="cite">Source: Human Rights Watch, June 19, 2023</div>

---

<!-- _class: transition -->

# Let's see it.

<div class="sub">Live, on a Raspberry Pi 5, no internet</div>

---

<!-- _class: section-head -->

<div class="kicker">How it works</div>

# One board, two engines, running at the same time.

<p>The GPU simulates the flood. Four Arm cores route and narrate. At the same time.</p>

---

<!-- _class: metric -->

<div class="kicker">GPU kernel, LLM-optimized, correctness-gated</div>

<div class="metric-row">
  <div class="metric-block">
    <div class="metric-num">1.59x</div>
    <div class="metric-label">steps/s over the original two-pass stencil</div>
  </div>
  <div class="metric-block">
    <div class="metric-num">2.09x</div>
    <div class="metric-label">that advantage grows under concurrent LLM decode</div>
  </div>
</div>

<div class="metric-note">A finite-state machine owns compile &rarr; verify &rarr; benchmark &rarr; keep/revert. A kernel that fails physics can never produce a benchmark number.</div>

<div class="cite">Source: BENCHMARK_RESULTS.md</div>

---

<!-- _class: table-slide -->

<div class="kicker">The concurrency counterfactual</div>

<table>
<thead>
<tr><th>Condition</th><th>GPU steps/s</th><th>CPU t/s</th></tr>
</thead>
<tbody>
<tr class="win"><td>Deployment (GPU + CPU split)</td><td>712</td><td>10.3</td></tr>
<tr><td>Best CPU-only alternative</td><td>681</td><td>8.4</td></tr>
</tbody>
</table>

<div class="note">The split wins both axes at once, against every CPU-only alternative tested.</div>

<div class="cite" style="margin-top:14px;">Source: BENCHMARK_RESULTS.md</div>

---

<!-- _class: section-head -->

<div class="kicker">Arm-specific optimization, measured, not assumed</div>

# Three findings that only show up when you actually benchmark the board.

---

<!-- _class: metric -->

<div class="kicker">Native repack beats Arm KleidiAI</div>

<div class="metric-row">
  <div class="metric-block">
    <div class="metric-num">+39.7%</div>
    <div class="metric-label">prompt processing</div>
  </div>
  <div class="metric-block">
    <div class="metric-num">+14.3%</div>
    <div class="metric-label">decode</div>
  </div>
</div>

<div class="metric-note">Cortex-A76 has no i8mm/SVE, so KleidiAI never reaches its best kernels here. llama.cpp&apos;s own repack path wins instead.</div>

<div class="cite">Source: HACKATHON.md</div>

---

<!-- _class: metric -->

<div class="kicker">A real bug, found and fixed</div>

<div class="metric-row">
  <div class="metric-block">
    <div class="metric-num">10.6x</div>
    <div class="metric-label">prompt processing, GPU hidden vs. visible</div>
  </div>
</div>

<div class="metric-note">Any visible Vulkan device pins CPU weights in GPU write-combined memory, even at zero GPU layers. One environment variable fixes it.</div>

<div class="cite">Source: bench_llm_cpu.sh</div>

---

<!-- _class: metric -->

<div class="kicker">Q4_0 beats every K-quant and speculative decoding</div>

<div class="metric-row">
  <div class="metric-block">
    <div class="metric-num">+73.9%</div>
    <div class="metric-label">Q4_0 vs. best K-quant, prompt processing</div>
  </div>
  <div class="metric-block">
    <div class="metric-num warn">6.0%<br>slower</div>
    <div class="metric-label">speculative decoding, rejected on measurement</div>
  </div>
</div>

<div class="cite">Source: BENCHMARK_RESULTS.md</div>

---

<!-- _class: closing -->

<h1><img class="leaf" src="data:image/png;base64,__LEAF__"> Bonbibi</h1>

<div class="repo">github.com/msradam/bonbibi: MIT licensed</div>

<div class="event">Arm AI Optimization Challenge 2026, Physical AI Track</div>
