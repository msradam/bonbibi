# Pilot concept note: shelter-anchored flood guidance stations, Satkhira, Bangladesh

Draft for partner discussion. Every factual claim is cited in
`POSITIONING.md` or flagged here as an estimate/validation item; nothing
in this note relies on a refuted or unverified research claim.

## Summary

Deploy ten Bonbibi stations — $150-class, passively cooled, offline
flood-guidance appliances — at cyclone shelters operated by Cyclone
Preparedness Programme (CPP) volunteer units in Satkhira district
(Sundarbans coast), for one full monsoon/cyclone season. Each station
holds its village's terrain, streets, and shelter list (~1 MB), runs a
physics-verified flood simulation on the board's GPU, routes residents
to reachable shelters by mobility profile (wheelchair / on foot /
vehicle, thresholds from ARR/AIDR standards), and narrates plain-language
guidance from an on-device language model that cannot invent facts.
Twelve months, two partner visits, drill-based evaluation.

## The problem, in verified numbers

1.81 billion people face significant flood exposure; 89% live in low-
and middle-income countries. Bangladesh's warning-plus-shelter system
took cyclone mortality from ~300,000 (1970) to about seventeen (2019) —
but the last mile still transmits *warnings*, not *guidance*: UNDRR's
global survey finds only 26% of persons with disabilities could evacuate
immediately without difficulty, improving to 39% with sufficient early
warning, while only 8% say local plans address their needs. Warning
dissemination reaches the village; computation does not. When
connectivity fails — the defining condition of a landfalling cyclone —
cloud-based tools fail with it.

## The intervention

Each station is a Raspberry Pi 5 in a sealed enclosure at the shelter,
powered from the shelter's existing solar/battery where available:

- **Before the season**: a one-time online fetch (elevation, offline
  basemap, shelter candidates: ~1 MB per village), a community mapping
  session to correct OSM shelter data with local knowledge, and a
  half-day training for the CPP unit (the operators are the existing
  76,020-strong volunteer force; no new cadre is created).
- **At a trigger** (CPP signal or anticipatory-action activation): the
  volunteer runs the forecast storm on the kiosk. The GPU simulates
  flooding over the village's actual terrain in seconds; the console
  shows AIDR-class hazard bands on a real local map, which shelters
  remain dry, and — per tapped household location — who can still move,
  by which route, and who must be assisted first, spoken aloud and in
  plain text.
- **Continuously**: the station is a drill tool. Volunteers rehearse
  differentiated evacuation (the wheelchair case, the flooded-shelter
  case) against simulated storms of increasing severity.

Safety architecture: deterministic code owns every safety decision
(depth thresholds, routes, recommended actions); the language model only
phrases computed facts, through IBM Granite's document-grounding
template; output carries CAP 1.2-shaped structure and a
simulation-based disclaimer. Measured on the board: ~700 simulation
steps/s concurrent with narration; guidance in ~15-40 s per query.

## Evidence of feasibility

- The system exists and is measured end to end (repo: build, run, and
  validation commands; physics gates; WCAG 2.2 AA console; headless CLI).
- Offline Pi-class appliances have a decade of field precedent (World
  Possible's RACHEL education servers; Jangala's Big Box connectivity
  units, 100,000+ people connected).
- **The comparable systems exist, work, and document their own gaps.**
  ICIMOD's community-based flood EWS runs in four Hindu Kush Himalaya
  countries on a caretaker model (a villager hosts the receiver and
  relays warnings by phone) and won a UNFCCC award — and by ICIMOD's own
  manual the instrument is a float sensor with sirens: it performs no
  flood modeling, no forecasting, no routing, its radio link is 700 m
  line-of-sight, and site selection *requires* good mobile signal at the
  caretaker's house. Practical Action's Nepal systems (eight river
  basins since 2002) achieved 2-3 hours of warning lead time (about 7
  with probabilistic forecasting), and both the implementers and the
  peer-reviewed evaluation (NHESS 2017) explicitly name disabled people,
  pregnant women, the elderly, and children as those for whom that lead
  time is inadequate — their stated remedy is longer lead time;
  computing *who can move where* in the time available is this pilot's
  addition.
- **Local resilience is a documented need, not a hypothesis.** In the
  2014 Babai River flood the gauging station washed away, the gauge
  reader's phone was damaged, the communication chain broke at the
  crucial period, and more than 20 people died (NHESS 2017). Practical
  Action's own sustainability guidance flags battery degradation during
  grid disruption and recommends solar-charged equipment that runs for
  days — the design premise of this station.
- **Cost sits under the field benchmark.** ICIMOD's instrument set cost
  ~USD 1,000 in hardware (May 2015 figure) with ~USD 10,000 per site
  including community mobilization; one USD 1,000 instrument's warning
  saved USD 3,300 in assets in a single 2013 flood. A Bonbibi station's
  hardware is $250-400 — a computation-and-guidance layer priced below
  the sensing layer it complements.
- **The funding channel is operating at scale.** WFP's anticipatory
  action alone covered 6.2 million people across 44 countries in 2024
  with a US$100M portfolio (US$72.6M prearranged for activations).

## Partners

- **CPP / Bangladesh Red Crescent** — shelter access, volunteer
  operators, drill integration (to be approached; the CPP unit-based
  model is the design assumption).
- **An anticipatory-action actor** (IFRC/BDRCS Early Action Protocol or
  OCHA-coordinated framework) — trigger integration and financing
  mechanism: anticipatory action released ~$120M across 146 activations
  in 54 countries in 2025.
- **A local disability organization** — mobility-profile mapping and
  the accessibility acceptance test (the pilot's core differentiator).

## Budget estimate (10 stations, 12 months)

Hardware per station (verified MSRPs where marked):

| Item | Est. |
|---|---|
| Raspberry Pi 5 16 GB (MSRP, verified) | $120 |
| microSD, PSU, sealed case | ~$60 |
| Small touchscreen | ~$80 |
| Solar/battery share (where shelter power absent; estimate) | ~$140 |
| **Per station** | **~$250–400** |

Programme (estimates): 10 stations ~$4,000; per-village data
preparation and community mapping ~$3,000; training and two field
visits ~$12,000; local coordinator (part-time, 12 months) ~$9,000;
evaluation ~$6,000; contingency 15%. **Total: ~$39,000.** For scale
context: Bangladesh's shelter network is 5,000+ buildings; a station in
every one is under $2M of hardware, and per-site cost sits below
ICIMOD's ~USD 10,000 community-EWS benchmark.

## Evaluation

Primary questions: does station-assisted drilling change evacuation
plans for mobility-constrained residents, and does guidance hold up
under real triggers?

Indicators: station uptime through the season (target >95%); number of
drills run per site; volunteers certified per site; count of
mobility-constrained residents with a pre-computed shelter route
(baseline ≈ 0); time from trigger to per-household guidance (measured:
under one minute per query after simulation); qualitative acceptance
from disabled residents and volunteers; any real-activation after-action
reviews.

Method: pre/post drill observation with the partner DPO; season-end
structured interviews; all station logs are local and reviewable.

## Risks and honest limits

- **Model/language**: guidance is currently English; Bengali narration
  is a pilot workstream requiring model validation (Granite's
  multilingual coverage must be tested against plain-language standards
  before field use; until then, volunteers mediate).
- **Data**: OSM shelter coverage in rural Satkhira is near zero (our
  Gabura fetch returned none) — hence the community mapping session as
  a required activity, not an option. SRTM-derived elevation reads
  canopy in vegetated deltas; the pilot should ingest better DEMs where
  the partner can source them (the pipeline is input-agnostic).
- **Physics**: the simulation has no drainage/infiltration; absolute
  depths are conservative-high and the pilot frames outputs as spatial
  pattern + relative severity, consistent with the disclaimer.
- **Sustainability**: ICIMOD's own 2022 review finds community EWS are
  "generally initiated, funded, and managed by external agencies" — the
  known weak point of this class. This design mitigates what it can:
  commodity hardware, an existing volunteer force as operators (no new
  cadre), zero recurring cloud costs, and the proven caretaker model for
  custody.

## Beyond the pilot

Success unlocks three verified funding-aligned paths: the EW4All
dissemination/preparedness pillars ($550M + $1B of the $3.1B action
plan); anticipatory-action frameworks (205 in development across 71
countries); and Bangladesh's own shelter expansion (government target
7,000+ shelters). The same station generalizes beyond cyclonic flood to
pluvial and riverine events — anywhere terrain, water, and mobility
intersect.
