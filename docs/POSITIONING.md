# Bonbibi beyond the hackathon: positioning, market, and users

Every claim below survived adversarial verification against its cited
source (two deep-research passes plus targeted primary-source checks,
2026-07-12/13). Facts that failed or never completed verification are
listed at the end and must not be used.

## The thesis

Bonbibi is not an edge-AI gadget. It is **last-mile early-warning
infrastructure**: a ~$120, passively-cooled appliance that gives one
neighborhood, one shelter, or one village its own flood simulation,
mobility-aware evacuation routing, and plain-language guidance — with no
dependence on connectivity, cloud, or a data center. It sits at the
intersection of two documented facts:

1. **The edge is where the compute is going.** IDC forecasts global edge
   computing spending at nearly $261 billion in 2025, growing at 13.8%
   CAGR to ~$380 billion by 2028, with AI among its two fastest-growing
   segments; Grand View Research sizes edge AI specifically at $24.9B in
   2025 reaching $118.7B by 2033 (analyst estimates vary 2-3x; cite as
   attributed figures).
2. **The last mile of early warning is a recognized, funded, unclosed
   gap.** The UN's Early Warnings for All initiative (launched 2022,
   co-led by WMO/UNDRR with ITU and IFRC) aims to cover every person on
   Earth by end-2027 with a $3.1B five-year action plan — about 50 cents
   per person per year — of which $550M is for warning dissemination and
   $1B for preparedness to respond: precisely Bonbibi's pillars. Yet 48%
   of least developed countries and 57% of small island developing
   states still lack adequate multi-hazard early warning systems, and
   the UNDRR/WMO Global Observatory found 54% of tracked EWS financing
   concentrated in just five countries.

The population on the wrong side of that gap is quantified: **1.81
billion people — 23% of humanity — face significant 1-in-100-year flood
exposure; 89% of them live in low- and middle-income countries**, and
about 4 in 10 are poor (World Bank; Rentschler, Salhab & Jafino, Nature
Communications 2022).

The economics favor exactly this class of intervention: the Global
Commission on Adaptation found early warning systems return **at least
10x their cost**, that **24 hours of warning cuts ensuing damage by
roughly 30%**, and that $800M invested in EWS for developing countries
would avoid $3–16B per year in losses.

## The hardware position

Raspberry Pi is not hobbyist-scale: **over 75 million units sold**
through 2025, 7.6 million in FY2025 alone (Raspberry Pi Holdings FY2025
results). Within the edge-AI device field, Bonbibi's board sits in a
deliberate niche: a Pi 5 at ~$80–120 with **zero added accelerator
cost**, because the flood physics runs on the GPU every Pi already has —
where the comparable AI-branded platforms are the Jetson Orin Nano Super
dev kit ($249, 67 TOPS, 25 W envelope) and the Pi AI HAT+ add-ons ($70
for 13 TOPS, $110 for 26 TOPS). Those NPUs accelerate vision inference,
not general compute: neither runs a Vulkan physics kernel. Bonbibi's
claim is therefore not "cheapest TOPS" but **useful work per dollar of
silicon already deployed** — simulation on the free GPU, language on the
CPU, on the most widely owned computer of its class on Earth.

## Why this device shape, specifically

- **The architecture has operational precedent.** World Possible's
  RACHEL — an offline Pi server broadcasting educational content over
  local Wi-Fi — has run for a decade across dozens of countries;
  Jangala's Big Box (rapid-deploy humanitarian Wi-Fi) reports 100,000+
  people connected across refugee camps and disaster response. Offline
  Pi-class appliances survive the field. Bonbibi is the same deployment
  shape carrying computation instead of content.
- **Bangladesh proves the theory of change at national scale.** Early
  warning + shelters + volunteer committees took cyclone mortality from
  ~300,000 (Bhola, 1970) and ~138,000 (1991) to 3,363 (Sidr, 2007) and
  ~17 (Fani, 2019) — a hundred-fold decline. The infrastructure behind
  it: 5,000+ cyclone shelters (target 7,000+) and the Cyclone
  Preparedness Programme's **76,020 volunteers, half of them women by
  design**. Bonbibi's kiosk scenario is a computational upgrade to a
  shelter-and-volunteer network that already exists and already works.
- **The institutional mechanism exists and is funded.** Anticipatory
  action — acting ahead of forecast hazards through a pre-agreed
  trigger, pre-agreed activities, and pre-arranged financing (OCHA) —
  was activated **146 times across 54 countries in 2025, releasing
  almost $120M and reaching 9.6 million people**, with 205 further
  frameworks under development in 71 countries (Anticipation Hub, 2025
  global overview). A forecast-triggered local guidance station is a
  pre-agreed activity with a $120 hardware bill.

## Ranked first clients / deployment partners

1. **Anticipatory-action programmes** (OCHA/CERF, IFRC forecast-based
   financing, WFP/FAO/Start Network): funded ($120M released in 2025),
   trigger-based, explicitly pre-positioned — the contractual shape
   Bonbibi fits without invention.
2. **EW4All pillar 3/4 implementers** (WMO/UNDRR/ITU/IFRC country
   rollouts): the $550M dissemination + $1B preparedness budgets are the
   named funding lines for last-mile warning capability.
3. **Community EWS operators**: Bangladesh CPP (76,020 volunteers, 5,000+
   shelters), community-based flood EWS programmes in the Hindu Kush
   Himalaya region — organizations that already train volunteers to
   operate warning equipment.
4. **Municipal/neighborhood resilience organizations** in high-income
   flood zones (the Red Hook Initiative type): smaller scale, reachable
   directly, fast to pilot, with a documented history of running their
   own crisis infrastructure.
5. **Inclusive-DRR actors** (disabled persons' organizations, UNDRR
   stakeholder groups): Bonbibi is one of very few tools whose core
   design object is the mobility-constrained evacuee (UNDRR 2023: only
   8% of persons with disabilities say local plans address their needs).

## User stories (each fact cited; hedges preserved)

**1. The shelter captain — Gabura, Sundarbans, Bangladesh.** A CPP
volunteer — one of 76,020, half women by recruitment design — runs the
cyclone shelter in an embanked delta village. Her country's warning
system took cyclone mortality from ~300,000 dead in 1970 to about
seventeen in 2019, but the last mile still runs on flags, megaphones,
and what she can see from the embankment. On the shelter's battery sits
a $120 board holding her village's terrain, streets, and shelter list in
823 KB. When the upstream gauge crosses the trigger, she runs the storm:
the GPU floods her actual village in seconds, and for each family she
taps — the rice farmer with the disabled father, the school with forty
children — it answers in plain language who can still move, by which
path, and who must be helped out first. No signal required; the cyclone
took the towers an hour ago.

**2. The digital steward — Red Hook, Brooklyn.** When Sandy hit on
October 29, 2012, it cut power to 402 NYCHA buildings housing ~79,000
residents; the Red Hook Houses got electricity back on November 13, two
weeks later, and 81 buildings citywide still lacked heat the day after
that. What kept working was the neighborhood's own infrastructure: the
Red Hook Initiative's community WiFi mesh, built with the Open
Technology Institute starting fall 2011 — up before the storm — carried
up to 300 users a day afterward, and FEMA's response was to plug in: an
Innovation Fellow put a 15-megabit satellite uplink on RHI's roof by
November 12. A steward maintaining that mesh today could rack a Bonbibi
node beside the router: the same community-owned network, now carrying a
flood simulation of Red Hook itself, telling residents of America's
densest public housing which streets a wheelchair can still cross before
the water crests.

**3. The panchayat secretary — Kuttanad, Kerala.** In 2018 Kerala took
its worst flooding since 1924 — rainfall 42% above normal, releases from
37 dams, 433 dead in the PDNA window, 5.4 million affected — and
below-sea-level Kuttanad was underwater from July after its polder bunds
breached, part of 65,188 hectares inundated by satellite count. The
response ran through local government: 3,879 relief camps holding 1.45
million people at peak, coordinated by committees constituted at the
panchayat level. A panchayat secretary with a Bonbibi node runs
tomorrow's forecast against her own polders before the bunds go, and
reads out — in advance, per hamlet, per mobility — who needs the boat,
who can wade the road, and who goes to which camp; the recovery bill
Kerala actually paid was $4.4 billion.

**4. The first responder — Beira, Mozambique.** Cyclone Idai made
landfall at Beira on the night of March 14–15, 2019; the IFRC assessment
team that reached the city on the 17th — airport closed, the last road
severed by a burst dam — estimated from the air that "90 per cent of the
area" was damaged or destroyed, a preliminary aerial figure that became
the event's defining number. Beira was cut off precisely when it most
needed to compute: no communications, no grid, no cloud. A response team
carrying a Bonbibi node in a hand case lands with the city's terrain and
shelters already aboard, simulates the still-rising water on battery
power, and hands coordinators capability-specific movement guidance
while the network is still weeks from restoration.

**5. The camp coordinator — Sehwan, Sindh, Pakistan.** The 2022 monsoon
floods affected 33 million Pakistanis, killed more than 1,730, displaced
over 8 million, and left damage and losses the official PDNA (Government
of Pakistan with the World Bank, ADB, EU, and UN) put above $30 billion
($14.9B damages, $15.2B losses). Around Sehwan, displaced families waited
on embankments for water that took months to drain. A coordinator with a
Bonbibi node doesn't need the drowned cell network to answer the daily
questions — which settlements can a supply truck reach today (cars float
at 0.3 m), which can only be reached on foot, where are the people who
can't wade at all — because the simulation, the routing, and the
narration are all on the board in her hand.

## Facts that failed or lack verification — do not use

- "World Possible ships an offline RACHEL AI" — refuted (0-3).
- "Mortality is 6x lower with good EWS" — failed verification; use the
  GCA 10x / 30% figures.
- Kudumbashree Pathanamthitta "6,500 volunteers" specifics — refuted as
  stated.
- Beira death toll, "port handles X% of trade", named reconstruction
  programmes; Pakistan "one-third submerged" attribution; Manchar Lake
  breach specifics; Red Hook Houses exact resident count; number of Red
  Hook digital stewards — none survived verification; write around them.
- Kerala death tolls vary by window (339 for 1–30 Aug; 433 for the PDNA
  window; 483 full season): always attach the date window.

## Sources

UN EW4All (un.org/en/climatechange/early-warnings-for-all) · WMO Global
Status of MHEWS 2025 (library.wmo.int/records/item/69684) · UNDRR/WMO
Global Observatory for EWS Investments (undrr.org) · Global Commission
on Adaptation, Adapt Now, 2019 (gca.org) · Rentschler, Salhab & Jafino,
Nature Communications 2022 · World Bank South Asia blog, Bangladesh
cyclone protection · CPP volunteer database (voldb.cpp.gov.bd) · IDC
edge computing forecast, Mar 2025 · Grand View Research, Edge AI ·
Raspberry Pi Holdings FY2025 results (investors.raspberrypi.com) ·
Raspberry Pi AI HAT+ announcement (raspberrypi.com/news) · NVIDIA Jetson
Orin Nano Super announcement, Dec 2024 · World Possible
(worldpossible.org/rachel) · Jangala (janga.la) · OCHA anticipatory
action (unocha.org/anticipatory-action) · Anticipation Hub, Anticipatory
Action in 2025: A Global Overview · New America/OTI, Red Hook WiFi case
study · NYCHA press release, Nov 14 2012 · Kerala PDNA (sdma.kerala.gov.in,
Feb 2019) and Govt. of Kerala Memorandum, Aug 2018 · UNDP Kerala PDNA ·
IFRC press release, Mar 2019 (Beira) · World Bank press release, Oct 28
2022 (Pakistan PDNA).
