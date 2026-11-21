"""Download Census ACS 1-year median gross rent by bedrooms (table B25031) for
Cambridge city, MA, and write data/raw/census_acs1_gross_rent_by_bedroom.csv.

Needs a free API key (https://api.census.gov/data/key_signup.html), set as an
environment variable so it never ends up in the repository:

    export CENSUS_API_KEY=your_key_here
    python analysis/00_fetch_census.py

The committed CSV was made this way on Nov 21, 2026; run_all.py does not re-download.
"""
import csv
import json
import os
import urllib.request

from common import RAW

KEY = os.environ.get("CENSUS_API_KEY")
if not KEY:
    raise SystemExit("Set CENSUS_API_KEY first (see the docstring).")

YEARS = [2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024]  # no standard 2020 1-year release
VARS = {"br1": "B25031_003", "br2": "B25031_004", "br3": "B25031_005"}
TOPCODED_MOE = "-333333333"  # Census code: median falls in an open-ended interval


def get(year, names):
    url = (f"https://api.census.gov/data/{year}/acs/acs1?get={','.join(names)}"
           f"&for=place:11000&in=state:25&key={KEY}")
    with urllib.request.urlopen(url, timeout=60) as r:
        header, row = json.load(r)[:2]
    return dict(zip(header, row))


out = []
for year in YEARS:
    est = get(year, [v + "E" for v in VARS.values()])
    moe = get(year, [v + "M" for v in VARS.values()])
    row, notes = {"year": year}, []
    for short, var in VARS.items():
        row[f"{short}_median_gross_rent"] = est[var + "E"]
        m = moe[var + "M"]
        if m == TOPCODED_MOE:
            notes.append(f"{short} value is top-coded; Census returned no margin of error")
            m = ""
        row[f"{short}_moe"] = m
    row["note"] = "; ".join(notes)
    out.append(row)
    print(year, row)

with open(RAW / "census_acs1_gross_rent_by_bedroom.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)
