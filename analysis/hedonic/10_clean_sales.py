"""Step 10: turn the raw Cambridge Property Database into a clean table of market sales.

WHAT THIS DOES (plain words)
  The city publishes one "snapshot" of every property per fiscal year (FY2016-FY2027). Each
  snapshot lists the property's features and its most recent sale. This script:
    1. removes owner names and mailing addresses, and (in the published file) street addresses and unit
       numbers, so the repository does not list who sold which home (not needed for any model);
    2. collects every sale that appears in any snapshot and removes duplicates;
    3. takes each home's features from the FIRST snapshot that shows the sale (closest after
       the sale), so the features describe the home as sold as closely as possible;
    4. keeps only the years where the snapshots capture (almost) every sale;
    5. removes non-market transfers ($0, $1, ... up to $1,000) and non-residential property;
    6. FLAGS (does not delete) suspicious sales so results can be shown with and without them.
  Every step writes a line to results/hedonic/cleaning_log.csv: the rule, rows before, rows
  after, rows removed. All thresholds are fixed here, before any model is run.

RUN
  uv run python analysis/hedonic/10_clean_sales.py
OUTPUT
  data/processed/hedonic/sales_clean.csv   (no owner fields)
  results/hedonic/cleaning_log.csv
"""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "hedonic" / "cambridge_property_db_fy2016_fy2027.csv"
OUT = ROOT / "data" / "processed" / "hedonic"
RES = ROOT / "results" / "hedonic"
OUT.mkdir(parents=True, exist_ok=True)
RES.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------- fixed rules
NON_MARKET_MAX_PRICE = 1_000          # sale price <= this is a non-market transfer
LOW_RATIO = 0.10                      # flag: price < 10% of assessed value
PPSF_TAIL = 0.005                     # flag: bottom/top 0.5% price per sq ft, within class
LAST_FULL_YEAR = 2025                 # 2026 has only a handful of sales so far
RESIDENTIAL = {                       # property class  -> analysis group
    "CONDOMINIUM": "condo",
    "CNDO LUX": "condo_lux",
    "SNGL-FAM-RES": "single_family",
    "SINGLE FAM W/AUXILIARY APT": "single_family",
    "TWO-FAM-RES": "two_family",
    "THREE-FM-RES": "three_family",
}

log = []


def step(name, rule, before, after, note=""):
    log.append(dict(step=len(log) + 1, name=name, rule=rule, rows_before=before,
                    rows_after=after, rows_removed=before - after, note=note))
    print(f"[{len(log):>2}] {name}: {before:,} -> {after:,} ({before - after:,} removed) {note}")


def norm(col):
    return re.sub(r"[^0-9a-z]+", "_", col.strip().lower()).strip("_")


# 1. load, normalise column names, drop owner fields --------------------------------
# The file writes missing values as the text "None"; read those (and blanks) as missing.
df = pd.read_csv(RAW, dtype=str, low_memory=False, na_values=["None", ""], keep_default_na=False)
df.columns = [norm(c) for c in df.columns]
n0 = len(df)
owner_cols = [c for c in df.columns if c.startswith("owner")]
df = df.drop(columns=owner_cols)
step("load", "all rows of all fiscal-year snapshots", n0, len(df),
     f"dropped owner columns: {', '.join(owner_cols)}; text 'None' read as missing; "
     "sale date 01/01/1900 and book/page '/' treated as no sale recorded")

num = ["saleprice", "assessedvalue", "previousassessedvalue", "buildingvalue", "landvalue",
       "landarea", "interior_livingarea", "interior_bedrooms", "interior_fullbaths",
       "interior_halfbaths", "interior_totalrooms", "interior_numunits", "condition_yearbuilt",
       "exterior_numstories", "latitude", "longitude", "yearofassessment",
       "parking_open", "parking_covered", "parking_garage"]
for c in num:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c].str.replace(",", "").str.replace("$", ""), errors="coerce")
df["saledate"] = pd.to_datetime(df["saledate"], format="%m/%d/%Y", errors="coerce")
# Placeholders used by the file: sale date 01/01/1900 = no sale recorded; book/page "/" = none.
df.loc[df["saledate"].dt.year <= 1900, "saledate"] = pd.NaT
df.loc[df["book_page"].str.strip().isin(["/", ""]), "book_page"] = pd.NA
df["yearofassessment"] = df["yearofassessment"].astype("Int64")

# 2. rows that carry a sale ---------------------------------------------------------
n = len(df)
s = df[df["saleprice"].notna() & df["saledate"].notna()].copy()
step("has_sale", "sale price and sale date both present", n, len(s))

# 3. one row per distinct sale, features from the first snapshot showing it -------------
n = len(s)
s = s.sort_values(["pid", "saledate", "saleprice", "yearofassessment"])
s = s.drop_duplicates(subset=["pid", "saledate", "saleprice"], keep="first")
step("dedupe", "same parcel + date + price seen in several snapshots -> keep the first snapshot",
     n, len(s), "features come from the snapshot closest after the sale")

# 3b. same parcel + date but a different price in a later snapshot = a correction: keep the
#     most recent snapshot's version (the corrected price).
n = len(s)
s = s.sort_values(["pid", "saledate", "yearofassessment"])
s = s.drop_duplicates(subset=["pid", "saledate"], keep="last")
step("price_corrections", "same parcel + date with different prices in different snapshots -> "
     "keep the most recent snapshot (treated as a correction)", n, len(s))

# 4. coverage window: sales are complete only after the first snapshot's cut-off ---------
cutoff = df.loc[df["yearofassessment"] == df["yearofassessment"].min(), "saledate"].max()
start = (cutoff + pd.offsets.MonthBegin(1)).normalize()
# use whole calendar years for year fixed effects
start_year = start.year if start.month == 1 else start.year + 1
n = len(s)
s = s[(s["saledate"].dt.year >= start_year) & (s["saledate"].dt.year <= LAST_FULL_YEAR)]
step("window", f"sale year {start_year}-{LAST_FULL_YEAR}", n, len(s),
     f"first snapshot (FY{int(df['yearofassessment'].min())}) records sales up to "
     f"{cutoff.date()}; earlier years only show each home's last sale as of then (incomplete)")

# 5. non-market transfers ------------------------------------------------------------------
n = len(s)
zero, one = int((s["saleprice"] == 0).sum()), int((s["saleprice"] == 1).sum())
s = s[s["saleprice"] > NON_MARKET_MAX_PRICE]
step("non_market", f"sale price <= ${NON_MARKET_MAX_PRICE:,}", n, len(s),
     f"of which $0: {zero:,}, $1: {one:,}")

# 6. residential classes -----------------------------------------------------------------
n = len(s)
dropped = s.loc[~s["propertyclass"].isin(RESIDENTIAL), "propertyclass"].value_counts()
s = s[s["propertyclass"].isin(RESIDENTIAL)].copy()
s["group"] = s["propertyclass"].map(RESIDENTIAL)
step("residential", "keep condo, luxury condo, 1-3 family", n, len(s),
     "largest removed classes: " + "; ".join(f"{k} ({v})" for k, v in dropped.head(6).items()))

# 7. usable size and location --------------------------------------------------------------
n = len(s)
s = s[(s["interior_livingarea"] > 0) & s["latitude"].notna() & s["longitude"].notna()]
step("size_location", "living area > 0 and coordinates present", n, len(s))

# 8. flags (rows are kept; models report results with and without flagged sales) --------
s["flag_low_ratio"] = s["saleprice"] < LOW_RATIO * s["assessedvalue"]
key = s["book_page"].fillna("") + "|" + s["saledate"].dt.strftime("%Y-%m-%d")
multi = s[s["book_page"].notna()].groupby(key)["pid"].transform("nunique")
s["flag_multi_parcel"] = False
s.loc[multi.index, "flag_multi_parcel"] = multi > 1
s["price_per_sqft"] = s["saleprice"] / s["interior_livingarea"]
lo = s.groupby("group")["price_per_sqft"].transform(lambda x: x.quantile(PPSF_TAIL))
hi = s.groupby("group")["price_per_sqft"].transform(lambda x: x.quantile(1 - PPSF_TAIL))
s["flag_ppsf_extreme"] = (s["price_per_sqft"] < lo) | (s["price_per_sqft"] > hi)
s["flag_bedrooms_missing"] = s["interior_bedrooms"].isna()
s["main_sample"] = ~(s["flag_low_ratio"] | s["flag_multi_parcel"])
for f, why in (("flag_low_ratio", f"price < {LOW_RATIO:.0%} of assessed value"),
               ("flag_multi_parcel", "several parcels recorded on the same deed and date "
                                     "(price is often a total for all of them)"),
               ("flag_ppsf_extreme", f"price per sq ft in bottom/top {PPSF_TAIL:.1%} of its group"),
               ("flag_bedrooms_missing", "bedroom count missing")):
    log.append(dict(step=len(log) + 1, name=f, rule=why, rows_before=len(s), rows_after=len(s),
                    rows_removed=0, note=f"flagged {int(s[f].sum()):,} rows (kept)"))
    print(f"     flag {f}: {int(s[f].sum()):,}")
log.append(dict(step=len(log) + 1, name="main_sample",
                rule="main sample excludes flag_low_ratio and flag_multi_parcel",
                rows_before=len(s), rows_after=int(s["main_sample"].sum()),
                rows_removed=int((~s["main_sample"]).sum()),
                note="excluded rows stay in the file for robustness checks"))

# 9. write --------------------------------------------------------------------------------
s["sale_year"] = s["saledate"].dt.year
s["sale_quarter"] = s["saledate"].dt.to_period("Q").astype(str)
s["log_price"] = s["saleprice"].apply(lambda v: __import__("math").log(v))
# Street address and unit number are left out of the published file (privacy; no model uses them).
keep = ["pid", "latitude", "longitude", "propertyclass", "group",
        "saledate", "sale_year", "sale_quarter", "saleprice", "log_price", "price_per_sqft",
        "book_page", "yearofassessment", "assessedvalue", "interior_livingarea",
        "interior_bedrooms", "interior_fullbaths", "interior_halfbaths", "interior_totalrooms",
        "interior_numunits", "condition_yearbuilt", "condition_overallcondition",
        "condition_overallgrade", "condition_interiorcondition", "exterior_numstories",
        "exterior_floorlocation", "exterior_view", "systems_centralair", "interior_laundryinunit",
        "parking_open", "parking_covered", "parking_garage", "landarea", "zoning",
        "flag_low_ratio", "flag_multi_parcel", "flag_ppsf_extreme", "flag_bedrooms_missing",
        "main_sample"]
keep = [c for c in keep if c in s.columns]
s = s[keep].sort_values("saledate")
s["saledate"] = s["saledate"].dt.strftime("%Y-%m-%d")
s.to_csv(OUT / "sales_clean.csv", index=False)
pd.DataFrame(log).to_csv(RES / "cleaning_log.csv", index=False)

DESCRIPTIONS = {
    "pid": "Cambridge parcel ID (condo units have their own ID)",
    "latitude": "Latitude (WGS84)", "longitude": "Longitude (WGS84)",
    "propertyclass": "Assessor property class, as published",
    "group": "Analysis group: condo, condo_lux, single_family (incl. with auxiliary apartment), "
             "two_family, three_family",
    "saledate": "Sale date (YYYY-MM-DD)", "sale_year": "Calendar year of sale",
    "sale_quarter": "Calendar quarter of sale (e.g. 2021Q3), used for time fixed effects",
    "saleprice": "Recorded sale price, US$ (nominal)", "log_price": "Natural log of saleprice",
    "price_per_sqft": "saleprice / interior_livingarea",
    "book_page": "Registry of Deeds book/page of the sale",
    "yearofassessment": "Fiscal-year snapshot the home's features were taken from "
                        "(first snapshot that shows this sale)",
    "assessedvalue": "Assessed value in that snapshot, US$",
    "interior_livingarea": "Living area, sq ft", "interior_bedrooms": "Bedrooms",
    "interior_fullbaths": "Full bathrooms", "interior_halfbaths": "Half bathrooms",
    "interior_totalrooms": "Total rooms", "interior_numunits": "Number of units in the building/parcel",
    "condition_yearbuilt": "Year built", "condition_overallcondition": "Assessor overall condition rating",
    "condition_overallgrade": "Assessor construction grade",
    "condition_interiorcondition": "Assessor interior condition rating",
    "exterior_numstories": "Number of stories", "exterior_floorlocation": "Floor (condos)",
    "exterior_view": "Assessor view rating (condos)", "systems_centralair": "Central air (yes/no)",
    "interior_laundryinunit": "In-unit laundry (yes/no)",
    "parking_open": "Open parking spaces", "parking_covered": "Covered parking spaces",
    "parking_garage": "Garage spaces", "landarea": "Land area, sq ft (parcel)",
    "zoning": "Zoning district",
    "flag_low_ratio": f"TRUE if price < {LOW_RATIO:.0%} of assessed value (likely not arm's-length)",
    "flag_multi_parcel": "TRUE if several parcels share this deed (book/page) and date",
    "flag_ppsf_extreme": f"TRUE if price per sq ft is in the bottom/top {PPSF_TAIL:.1%} of its group",
    "flag_bedrooms_missing": "TRUE if bedroom count is missing",
    "main_sample": "TRUE unless flag_low_ratio or flag_multi_parcel (main analysis sample)",
}
dd = ["# Data dictionary: `sales_clean.csv`", "",
      "Built by `analysis/hedonic/10_clean_sales.py` from the Cambridge Property Database "
      "(see `data/raw/hedonic/SOURCES.md`). One row per market sale. Owner names, mailing addresses, "
      "street addresses and unit numbers are removed. Cleaning steps and row counts: `results/hedonic/cleaning_log.csv`.", "",
      "| Column | Meaning | Non-missing |", "|---|---|---|"]
for c in s.columns:
    dd.append(f"| `{c}` | {DESCRIPTIONS.get(c, '')} | {int(s[c].notna().sum()):,} |")
# Replace only this section; keep the sections other scripts document below it.
dd_path = OUT / "DATA_DICTIONARY.md"
old = dd_path.read_text() if dd_path.exists() else ""
tail = old[old.index("\n# ", 1):] if "\n# " in old[1:] else ""
dd_path.write_text("\n".join(dd) + "\n" + tail)
print(f"\nwrote {len(s):,} sales ({int(s['main_sample'].sum()):,} in main sample) "
      f"-> data/processed/hedonic/sales_clean.csv")
