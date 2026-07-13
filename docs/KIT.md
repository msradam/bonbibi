# Bonbibi hardware kit

Two build variants, both an all-in-one capacitive touchscreen appliance
with no GPIO wiring, no soldering, and no added AI accelerator. The flood
physics runs on the Pi's own GPU and the language model on its CPU, so
the only accessories are a screen, audio, a clock battery, and power.

- **Field Unit**: smallest footprint, lowest energy, solar-viable. A 5"
  panel in an aluminum HMI shell. This is the primary build for the
  Satkhira pilot.
- **Shelter Kiosk**: a roomier 7" (or larger) screen for a fixed station
  where a wall or desk mount and mains or shelter battery are available.

Prices are approximate, July 2026, USD, and exclude the Pi. Confirm
current price and the capacitive-touch spec before ordering. Links are
Amazon search queries plus official product pages; the search queries
stay valid as stock rotates.

## Variant A: Field Unit

| Part | ~Price | Connection | Why |
|---|---|---|---|
| Raspberry Pi 5, 16 GB | $120 | — | Runs sim, router, and model; 16 GB holds the resident 3B model with headroom |
| Raspberry Pi Touch Display 2, 5" | $40 | DSI (dedicated) | Capacitive multi-touch, 720x1280, ~1.5 W panel, 91x143 mm |
| Argon Industria HMI 5C enclosure | ~$45 (est.) | houses both | Aluminum shell purpose-built for the Pi 5 + 5" Display 2 as a compact HMI panel |
| RTC battery | $5 | BAT connector (dedicated) | Keeps time offline so CAP alert and log timestamps are correct with no network |
| Mini USB speaker | $15 | USB | Spoken guidance out (the Pi 5 has no analog jack; USB is the audio path) |
| Official 27 W USB-C PD supply | $12 | USB-C | Covers the load peak during a simulation and narration burst |
| 64 GB A2 microSD | $10 | — | OS and per-area data |
| **Subtotal (no solar)** | **~$247** | | |

Off-grid option (per station, estimate): a 30 W panel (~$40) plus a
100 Wh portable power station or battery bank (~$100). See Power below.

Links: [Pi 5 16GB](https://www.amazon.com/s?k=Raspberry+Pi+5+16GB) ·
[Touch Display 2 5-inch](https://www.amazon.com/s?k=Raspberry+Pi+Touch+Display+2+5+inch)
([official](https://www.raspberrypi.com/news/a-new-5-variant-of-raspberry-pi-touch-display-2/)) ·
[Argon Industria HMI 5C](https://www.amazon.com/s?k=Argon+Industria+HMI+5C)
([announcement](https://www.cnx-software.com/2026/04/24/argon-industria-hmi-5c-an-industrial-aluminum-enclosure-for-the-5-inch-raspberry-pi-touch-display-2/)) ·
[RTC battery](https://www.amazon.com/s?k=Raspberry+Pi+5+RTC+battery)
([official](https://www.raspberrypi.com/products/rtc-battery/)) ·
[mini USB speaker](https://www.amazon.com/s?k=mini+USB+speaker) ·
[27W USB-C supply](https://www.amazon.com/s?k=Raspberry+Pi+5+27W+USB-C+power+supply) ·
[64GB A2 microSD](https://www.amazon.com/s?k=SanDisk+64GB+microSD+A2) ·
[100Wh power station](https://www.amazon.com/s?k=100Wh+portable+power+station)

## Variant B: Shelter Kiosk

Two screen choices. The official display keeps the official-parts
pedigree but has no speakers, so it needs the USB speaker. The CrowVision
integrates speakers and a larger panel, which collapses screen and audio
into one purchase.

| Part | ~Price | Connection | Why |
|---|---|---|---|
| Raspberry Pi 5, 16 GB | $120 | — | as above |
| Screen A: Touch Display 2, 7" | $60 | DSI | 720x1280 capacitive; pair with the case below |
| ...case: SmartiPi Touch Pro 3 | ~$45 | houses both | Pi mounts behind the display, single USB-C in, wall or desk mount |
| Screen B (alt): Elecrow CrowVision 11.6" | ~$110 | HDMI + USB | Larger panel with built-in speakers; no separate speaker needed |
| RTC battery | $5 | BAT connector | offline timestamps |
| Mini USB speaker (Screen A only) | $15 | USB | spoken guidance out |
| Official 27 W USB-C PD supply | $12 | USB-C | load peaks |
| 64 GB A2 microSD | $10 | — | OS and data |
| **Subtotal (Screen A)** | **~$267** | | |
| **Subtotal (Screen B)** | **~$257** | | |

Links: [Touch Display 2 7-inch](https://www.amazon.com/s?k=Raspberry+Pi+Touch+Display+2+7+inch) ·
[SmartiPi Touch Pro 3](https://www.amazon.com/SmartiPi-Touch-Pro-Compatible-Raspberry/dp/B0F6ZR584W) ·
[Elecrow CrowVision 11.6"](https://www.amazon.com/s?k=Elecrow+CrowVision+11.6+Raspberry+Pi)
([Elecrow](https://www.elecrow.com/crowvision-11-6-raspberry-pi-capacitive-touch-display-hd-1366-768-ips-screen-for-raspberry-pi.html))

## Power and energy

Measured figures: the Pi 5 idles near 3 W, about 3.6 W with peripherals;
with the 5" Touch Display 2 the whole unit draws about 5.26 W booted
(7.46 W at boot), per Tom's Hardware. Full CPU and GPU load can reach
roughly 20 to 25 W for short periods.

The number that governs the energy budget is the idle draw, not the
peak, because the duty cycle is low. Bonbibi sits idle showing the map
almost all the time and only spikes for the seconds to minutes of a
storm simulation and narration during an actual event. Size the battery
and panel for the roughly 5 W average; size the power supply (the 27 W
official unit) for the peak.

Rough off-grid planning at 5 W average, about 120 Wh per day:

- A 100 Wh battery gives roughly 18 hours of dark-time autonomy.
- A 30 W panel at 4 to 5 peak-sun-hours produces about 120 to 150 Wh per
  day, which covers the daily draw.
- Oversize both for real field derating (dust, angle, cloud, and the
  peaks). This is a planning estimate, not a validated field figure.

Community EWS programmes document battery degradation during grid
disruption and recommend solar-charged equipment (Practical Action); a
5 W appliance is well inside what a small panel and bank sustain.

## Audio and on-device text-to-speech

The USB speaker only matters once narration runs on the Pi itself. The
current console uses the browser's speech synthesis, which runs in the
viewer's browser, not on the board. For a standalone kiosk driving its
own screen and speaker, add on-device TTS (Piper is the Arm-friendly
candidate) writing to the USB audio device. Track this as the audio
integration work item; the speaker is the hardware half of it.

For a kiosk that also takes voice input later, a single USB speakerphone
puck (Anker PowerConf class,
[search](https://www.amazon.com/s?k=Anker+PowerConf+USB+speakerphone))
combines speaker, microphone array, and echo cancellation in one plug,
which is a better fit than a bare speaker for a person standing at the
unit. It replaces the mini USB speaker line above.

## Deliberately not in the kit

- **AI accelerator HATs** (Raspberry Pi AI HAT+, Hailo; NPU boards).
  Different vendor, and the point is that the flood physics runs on the
  GPU every Pi already has. Adding a vision NPU does not help this
  workload and defeats the cost argument.
- **GPIO HATs** (I2S audio, SPI screens, sensor HATs). They need the
  header and often a specific case; the USB and DSI parts above avoid
  that entirely.
- **Resistive touchscreens.** Single-touch, need a stylus or fingernail,
  and worse for a public kiosk and for anyone with limited dexterity,
  which cuts against the accessibility premise. Every screen listed here
  is capacitive multi-touch.
- **RasPad-for-Pi-5.** The RasPad tablet was designed for the Pi 4;
  fitting a Pi 5 is a modification, not a supported build.

## Portable alternative

If a self-contained battery unit is a hard requirement, the Pi Slate
([announcement](https://www.cnx-software.com/2026/05/11/pi-slate-a-raspberry-pi-5-handheld-linux-cyberdeck-with-a-5-inch-1280x720-touchscreen-display/))
is a Pi 5 handheld with a 5" touchscreen and a built-in 10,000 mAh
battery (3 to 5 hours). It carries a keyboard and more standby drain than
a kiosk needs, so it suits carry-in field use rather than a fixed
station.
