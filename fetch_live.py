"""Live flood-driver data: a real-time river/tide gage from USGS Water Services
and rainfall from Open-Meteo (live forecast, or a historical storm day via the
archive API). Maps rainfall to vkflood's RAIN input. Offline-friendly like
fetch_dem.py: fetch once with internet, drive the flood sim offline from the
printed RAIN value.

Usage: fetch_live.py [lat lon usgs_site_id] [YYYY-MM-DD]
  lat/lon/usgs_site_id default to the Potomac River at Washington, DC.
  YYYY-MM-DD (optional): a historical storm day instead of live conditions,
  e.g. 2021-09-01 (Hurricane Ida remnants, a real DC flash-flood event) — use
  this to demo the pipeline on real rain when today happens to be dry.
"""

from __future__ import annotations

import json
import sys
import urllib.request

DEFAULT_LAT, DEFAULT_LON = 38.90, -77.03
DEFAULT_USGS_SITE = "01646500"  # Potomac River near Washington DC (Little Falls Pump Station)


def get(url: str):
    with urllib.request.urlopen(url, timeout=25) as r:
        return json.load(r)


def usgs_gage(site: str):
    url = f"https://waterservices.usgs.gov/nwis/iv/?sites={site}&parameterCd=00065&format=json"  # 00065 = gage height (ft)
    d = get(url)
    ts = d["value"]["timeSeries"][0]
    vals = ts["values"][0]["value"]
    return ts["sourceInfo"]["siteName"], float(vals[-1]["value"]), vals[-1]["dateTime"]


def open_meteo_rain(lat: float, lon: float, date: str | None):
    if date:
        url = (f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}"
               f"&longitude={lon}&start_date={date}&end_date={date}"
               "&hourly=precipitation&timezone=auto")
    else:
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}"
               f"&longitude={lon}&hourly=precipitation&past_days=2&forecast_days=2"
               "&timezone=auto")
    d = get(url)
    p = [x for x in d["hourly"]["precipitation"] if x is not None]
    return sum(p), (max(p) if p else 0.0), len(p)


def main() -> None:
    if len(sys.argv) >= 4:
        lat, lon, site = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
        date = sys.argv[4] if len(sys.argv) > 4 else None
    else:
        lat, lon, site = DEFAULT_LAT, DEFAULT_LON, DEFAULT_USGS_SITE
        date = sys.argv[1] if len(sys.argv) > 1 else None

    total, peak, hours = open_meteo_rain(lat, lon, date)
    try:
        name, ft, when = usgs_gage(site)
        gage = f"usgs_gage='{name}'  height_ft={ft:.2f}  at={when}"
    except Exception as e:  # gage fetch can fail; rain is the sim driver either way
        gage = f"usgs_gage=UNAVAILABLE ({e})"

    # Map rainfall to vkflood's RAIN (m/step). RAIN=0.006 (the tuned demo storm
    # level) corresponds to roughly 50 mm of driving rain; scale linearly, floor
    # at a trickle. Illustrative only: vkflood has no drainage, so absolute
    # depths run high — the spatial pattern is the meaningful output.
    rain_mm = max(total, peak * 3.0)
    rain = round(max(0.0005, 0.006 * rain_mm / 50.0), 5)

    src = f"historical {date}" if date else "live (past 2d + forecast 2d)"
    print(f"rain_source={src}  precip_total_mm={total:.1f}  peak_hourly_mm={peak:.1f}  hours={hours}")
    print(gage)
    print(f"RAIN={rain}")


if __name__ == "__main__":
    main()
