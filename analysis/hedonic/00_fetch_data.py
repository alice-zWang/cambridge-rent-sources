"""Step 00: download every raw data source for the hedonic study, unedited.

WHAT THIS DOES (plain words)
  Downloads each public dataset listed in SOURCES below into data/raw/hedonic/, exactly as the
  publisher serves it. For every file it records where it came from, when, how big it is, a
  SHA-256 checksum (a fingerprint that changes if even one byte changes) and, for tables, the
  number of rows. It then writes data/raw/hedonic/SOURCES.md, the human-readable source note.

  The raw files are NOT committed to git: they are large, and the property file contains owner
  names. Anyone can re-create them by running this script. Data published later will differ,
  and the checksums in SOURCES.md show whether a re-download matches the version used.

RUN
  uv run python analysis/hedonic/00_fetch_data.py            # skips files already present
  uv run python analysis/hedonic/00_fetch_data.py --force    # re-download everything

No API keys are needed. (The Census API now requires a key, so ACS tables come from the
Census bulk "table-based summary files" instead, which are the same estimates.)
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import ssl
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import certifi

# uv's bundled Python does not read the macOS certificate store; use certifi's CA bundle so
# HTTPS certificates are still fully verified.
SSL_CTX = ssl.create_default_context(cafile=certifi.where())

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "hedonic"
RAW.mkdir(parents=True, exist_ok=True)

CAM = "https://data.cambridgema.gov"
E2C = "https://educationtocareer.data.mass.gov"
MASSGIS = "https://s3.us-east-1.amazonaws.com/download.massgis.digital.mass.gov/shapefiles/l3parcels"
ACS = "https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData"
DESE_DISTRICTS = "('Cambridge','Somerville','Arlington','Newton','Brookline')"


def soda(base, ident, query):
    return f"{base}/resource/{ident}.csv?" + urllib.parse.urlencode(query)


SOURCES = [
    dict(file="cambridge_property_db_fy2016_fy2027.csv",
         url=f"{CAM}/api/views/eey2-rv59/rows.csv?accessType=DOWNLOAD",
         publisher="City of Cambridge, Assessing Department (Cambridge Open Data)",
         dataset="Cambridge Property Database FY2016-FY2027 (eey2-rv59), "
                 "https://data.cambridgema.gov/d/eey2-rv59",
         what="One row per parcel (or condo unit) per fiscal year, FY2016-FY2027: latest sale price "
              "and date, assessed values, building characteristics (living area, bedrooms, baths, "
              "year built, condition), property class, coordinates. Contains owner names and "
              "mailing addresses: these are dropped in step 10 and never committed.",
         terms="Public record. Cambridge Open Data portal terms of use apply (see portal)."),
    dict(file="cambridge_crime_reports.csv",
         url=f"{CAM}/api/views/xuad-73uj/rows.csv?accessType=DOWNLOAD",
         publisher="Cambridge Police Department (Cambridge Open Data)",
         dataset="Crime Reports (xuad-73uj), https://data.cambridgema.gov/d/xuad-73uj",
         what="One row per reported crime since 2009: type, date, police reporting area (117 areas), "
              "neighborhood, reporting-area centroid coordinates. Locations are reporting areas, not "
              "addresses.",
         terms="Cambridge Open Data portal terms of use apply (see portal)."),
    dict(file="cambridge_neighborhoods.geojson",
         url=f"{CAM}/api/geospatial/k3pi-9823?method=export&format=GeoJSON",
         publisher="City of Cambridge, Community Development Department (Cambridge Open Data)",
         dataset="Cambridge Neighborhood Polygons (k3pi-9823), https://data.cambridgema.gov/d/k3pi-9823",
         what="Boundaries of Cambridge's 13 official neighborhoods.",
         terms="Cambridge Open Data portal terms of use apply (see portal)."),
    dict(file="acs5_2024_b19013_median_household_income.dat",
         url=f"{ACS}/acsdt5y2024-b19013.dat",
         publisher="U.S. Census Bureau, American Community Survey",
         dataset="ACS 5-year 2020-2024 table-based summary file, table B19013 (median household income)",
         what="National file, every geography. Step 20 keeps Massachusetts census tracts. "
              "Estimates with 90% margins of error, in 2024 dollars.",
         terms="U.S. federal government data (public domain)."),
    dict(file="acs5_2024_b25064_median_gross_rent.dat",
         url=f"{ACS}/acsdt5y2024-b25064.dat",
         publisher="U.S. Census Bureau, American Community Survey",
         dataset="ACS 5-year 2020-2024 table-based summary file, table B25064 (median gross rent)",
         what="National file, every geography. Used only for the small tract-level rent check.",
         terms="U.S. federal government data (public domain)."),
    dict(file="cb_2023_25_tract_500k.zip",
         url="https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_25_tract_500k.zip",
         publisher="U.S. Census Bureau, Cartographic Boundary Files",
         dataset="2023 census tracts, Massachusetts, 1:500,000 (2020 tract definitions)",
         what="Tract boundaries, to attach each sale to its census tract.",
         terms="U.S. federal government data (public domain)."),
    dict(file="MBTA_GTFS.zip",
         url="https://cdn.mbta.com/MBTA_GTFS.zip",
         publisher="Massachusetts Bay Transportation Authority (MBTA)",
         dataset="MBTA GTFS static feed (current schedule), https://www.mbta.com/developers",
         what="Current stops and stations (stops.txt) and routes. A current snapshot: stations that "
              "opened recently (Green Line Extension, 2022) are present; opening dates are handled "
              "in step 20.",
         terms="MBTA developer license agreement (see https://www.mbta.com/developers)."),
]
for code, town in (("M049", "CAMBRIDGE"), ("M274", "SOMERVILLE"), ("M010", "ARLINGTON"),
                   ("M207", "NEWTON"), ("M046", "BROOKLINE")):
    SOURCES.append(dict(
        file=f"L3_SHP_{code}_{town}.zip",
        url=f"{MASSGIS}/L3_SHP_{code}_{town}.zip",
        publisher="MassGIS (Bureau of Geographic Information), from municipal assessors",
        dataset=f"MassGIS Property Tax Parcels, standardized parcels + assessor table, {town.title()}",
        what="Parcel polygons and a standardized assessor table (last sale only, no bedroom count). "
             "Used for cross-town comparisons (models 4 and 5).",
        terms="MassGIS data, free public download (see mass.gov MassGIS terms)."))
SOURCES += [
    dict(file="dese_mcas_district_5towns.csv",
         url=soda(E2C, "i9w6-niyt", {"$where": f"dist_name in{DESE_DISTRICTS} AND "
                                               "org_type='Public School District'",
                                     "$limit": "500000"}),
         publisher="Massachusetts DESE, via the Education-to-Career Research and Data Hub",
         dataset="MCAS Achievement Results (i9w6-niyt), "
                 "https://educationtocareer.data.mass.gov/d/i9w6-niyt",
         what="District-level MCAS rows for Cambridge, Somerville, Arlington, Newton and Brookline: "
              "all years, grades, subjects and student groups, with % meeting/exceeding, average "
              "scaled score and average student growth percentile (SGP). Filtered on the server; "
              "the exact query is the URL.",
         terms="Commonwealth of Massachusetts open data portal terms apply (see portal)."),
    dict(file="dese_per_pupil_spending_5towns.csv",
         url=soda(E2C, "8szy-v4ed", {"$where": f"dist_name in{DESE_DISTRICTS}", "$limit": "50000"}),
         publisher="Massachusetts DESE, via the Education-to-Career Research and Data Hub",
         dataset="Elementary and Secondary District Expenditures Per Pupil (8szy-v4ed)",
         what="Per-pupil spending by school year for the five districts. Filtered on the server.",
         terms="Commonwealth of Massachusetts open data portal terms apply (see portal)."),
]


def download(url, dest, tries=3):
    req = urllib.request.Request(url, headers={"User-Agent": "research-script/1.0"})
    for attempt in range(1, tries + 1):
        try:
            tmp = dest.with_suffix(dest.suffix + ".part")
            with urllib.request.urlopen(req, timeout=600, context=SSL_CTX) as r, open(tmp, "wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            tmp.rename(dest)
            return
        except Exception as e:  # noqa: BLE001
            print(f"  attempt {attempt} failed: {e}", file=sys.stderr)
            time.sleep(5 * attempt)
    raise SystemExit(f"could not download {url}")


def describe(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    info = {"bytes": path.stat().st_size, "sha256": h.hexdigest()}
    if path.suffix == ".csv":
        with open(path, newline="", encoding="utf-8", errors="replace") as f:
            info["rows"] = sum(1 for _ in csv.reader(f)) - 1
    elif path.suffix == ".dat":
        with open(path, encoding="utf-8", errors="replace") as f:
            info["rows"] = sum(1 for _ in f) - 1
    elif path.suffix == ".zip":
        with zipfile.ZipFile(path) as z:
            info["zip_members"] = len(z.namelist())
    elif path.suffix == ".geojson":
        info["features"] = len(json.load(open(path))["features"])
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    manifest_path = RAW / "manifest.json"
    manifest = json.load(open(manifest_path)) if manifest_path.exists() else {}
    for s in SOURCES:
        dest = RAW / s["file"]
        if dest.exists() and not args.force and s["file"] in manifest:
            print(f"skip (present): {s['file']}")
            continue
        print(f"download: {s['file']}", flush=True)
        download(s["url"], dest)
        manifest[s["file"]] = {**s, **describe(dest),
                               "downloaded_utc": dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M")}
        json.dump(manifest, open(manifest_path, "w"), indent=1)
        print(f"  ok: {manifest[s['file']]['bytes']:,} bytes", flush=True)
    write_sources_md(manifest)


def write_sources_md(manifest):
    lines = ["# Raw data sources (hedonic study)", "",
             "Every file in this folder is an **unedited** download, made by "
             "`analysis/hedonic/00_fetch_data.py`. The files themselves are git-ignored (size; the "
             "property file contains owner names). Re-create them by running the script. The SHA-256 "
             "checksum shows whether a new download is byte-identical to the one used here. "
             "Publishers update their data, so a later download will usually differ.", ""]
    for s in SOURCES:
        m = manifest.get(s["file"])
        if not m:
            continue
        size = f"{m['bytes'] / 1e6:,.1f} MB"
        count = (f"{m['rows']:,} rows" if "rows" in m else
                 f"{m['features']} features" if "features" in m else
                 f"{m['zip_members']} files in zip" if "zip_members" in m else "")
        lines += [f"## `{s['file']}`", "",
                  f"- **Publisher:** {s['publisher']}",
                  f"- **Dataset:** {s['dataset']}",
                  f"- **Download URL:** <{s['url']}>",
                  f"- **Downloaded:** {m['downloaded_utc']} UTC. **Size:** {size}. **Contents:** {count}",
                  f"- **SHA-256:** `{m['sha256']}`",
                  f"- **What it is:** {s['what']}",
                  f"- **Terms:** {s['terms']}", ""]
    (RAW / "SOURCES.md").write_text("\n".join(lines))
    print("wrote data/raw/hedonic/SOURCES.md")


if __name__ == "__main__":
    main()
