"""Step 55: build the five-town sales table (Cambridge, Somerville, Arlington, Newton, Brookline).

WHAT THIS DOES (plain words)
  Uses the state's standardized assessor files (MassGIS L3 parcels, downloaded in Phase 1). They
  give each property's MOST RECENT sale only, with basic features (type, living area, rooms, year
  built, lot size). Steps:
    - keep residential sales since 2016 and apply the cleaning rules in SPEC_PHASE4.md, logging
      the rows removed at each step;
    - locate each property (centre of its tax parcel), find its census tract and tract income,
      and its distance to the nearest MBTA rapid-transit station open on the sale date;
    - check the source: Cambridge sales in this file are matched to the city's own sales data.
  Owner name and address fields are never read.

OUTPUTS
  data/processed/hedonic/crosstown_sales.csv, results/hedonic/crosstown_cleaning_log.csv,
  results/hedonic/crosstown_source_check.csv

RUN
  uv run python analysis/hedonic/55_crosstown_build.py
"""
import io
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "hedonic"
PROC = ROOT / "data" / "processed" / "hedonic"
RES = ROOT / "results" / "hedonic"
METRIC = 26986
TOWNS = {"M049": "Cambridge", "M274": "Somerville", "M010": "Arlington", "M207": "Newton",
         "M046": "Brookline"}
COLS = ["PROP_ID", "LOC_ID", "TOTAL_VAL", "FY", "LOT_SIZE", "LOT_UNITS", "LS_DATE", "LS_PRICE",
        "USE_CODE", "LS_BOOK", "LS_PAGE", "YEAR_BUILT", "RES_AREA", "NUM_ROOMS"]   # no owner fields
USE = {"101": "single_family", "102": "condo", "104": "two_family", "105": "three_family"}
GLX = {"Lechmere": "2022-03-21", "Union Square": "2022-03-21", "East Somerville": "2022-12-12",
       "Gilman Square": "2022-12-12", "Magoun Square": "2022-12-12", "Ball Square": "2022-12-12",
       "Medford/Tufts": "2022-12-12"}
log = []


def note(step, d_before, d_after, rule):
    row = {"step": step, "rule": rule, "rows_before": len(d_before), "rows_after": len(d_after),
           "rows_removed": len(d_before) - len(d_after)}
    for t in TOWNS.values():
        row[f"after_{t}"] = int((d_after["town"] == t).sum())
    log.append(row)


# ------------------------------------------------------------------ read
parts, parcels = [], []
for code, town in TOWNS.items():
    z = next(RAW.glob(f"L3_SHP_{code}_*.zip"))
    names = zipfile.ZipFile(z).namelist()
    a = next(n for n in names if "Assess" in n and n.endswith(".dbf"))
    t = next(n for n in names if "TaxPar" in n and n.endswith(".shp"))
    d = gpd.read_file(f"zip://{z}!{a}", columns=COLS, ignore_geometry=True)
    d["town"], d["source_file"] = town, a.split("/")[-1]
    parts.append(pd.DataFrame(d))
    p = gpd.read_file(f"zip://{z}!{t}", columns=["LOC_ID"]).to_crs(METRIC)
    p = p.dissolve("LOC_ID").reset_index()           # a few LOC_IDs have several polygons
    c = p.geometry.centroid
    parcels.append(pd.DataFrame({"town": town, "LOC_ID": p["LOC_ID"], "x": c.x, "y": c.y}))
raw = pd.concat(parts, ignore_index=True)
loc = pd.concat(parcels, ignore_index=True)
raw["saledate"] = pd.to_datetime(raw["LS_DATE"], format="%Y%m%d", errors="coerce")
raw["use3"] = raw["USE_CODE"].astype(str).str.strip().str[:3]
log.append({"step": "0", "rule": "all assessor records, 5 towns", "rows_before": len(raw),
            "rows_after": len(raw), "rows_removed": 0,
            **{f"after_{t}": int((raw.town == t).sum()) for t in TOWNS.values()}})

# ------------------------------------------------------------------ cleaning (SPEC_PHASE4 Part B)
d0 = raw
d = d0[(d0["saledate"] >= "2016-01-01") & (d0["LS_PRICE"] > 1000)]
note("1", d0, d, "last sale on/after 2016-01-01 and price > $1,000")
d0, d = d, d[d["use3"].isin(USE)].copy()
note("2", d0, d, "residential use codes 101, 102, 104, 105")
d["group"] = d["use3"].map(USE)
bp = d["LS_BOOK"].astype(str).str.strip().replace({"": np.nan, "0": np.nan, "None": np.nan})
pg = d["LS_PAGE"].astype(str).str.strip().replace({"": np.nan, "0": np.nan, "None": np.nan})
key = d["town"] + "|" + bp + "|" + pg + "|" + d["LS_DATE"].astype(str)
multi = key.notna() & key.duplicated(keep=False)
d0, d = d, d[~multi]
note("3", d0, d, "drop multi-parcel sales (same town, book, page, date on several records)")
d0, d = d, d[~(d["LS_PRICE"] < 0.1 * d["TOTAL_VAL"])]
note("4", d0, d, "drop price below 10% of current total assessed value")
d0, d = d, d[d["RES_AREA"].between(300, 10000)].copy()
note("5", d0, d, "living area 300-10,000 sq ft")
d["sale_year"] = d["saledate"].dt.year
ppsf = d["LS_PRICE"] / d["RES_AREA"]
appsf = d["TOTAL_VAL"] / d["RES_AREA"]
d["rel_price_ppsf"] = ppsf / ppsf.groupby([d["town"], d["group"], d["sale_year"]]).transform("median")
d["rel_assessed_ppsf"] = appsf / appsf.groupby([d["town"], d["group"]]).transform("median")
restricted = (d["rel_price_ppsf"] < 0.5) & (d["rel_assessed_ppsf"] < 0.5)
d0, d = d, d[~restricted].copy()
note("6", d0, d, "drop likely deed-restricted (price and assessed $/sq ft both < 0.5 x median)")

# ------------------------------------------------------------------ location, tract, income
d = d.merge(loc, on=["town", "LOC_ID"], how="left")
pts = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d["x"], d["y"]), crs=METRIC)
tracts = gpd.read_file(f"zip://{RAW / 'cb_2023_25_tract_500k.zip'}").to_crs(METRIC)
j = gpd.sjoin(pts[["geometry"]], tracts[["GEOID", "geometry"]], how="left", predicate="within")
d["tract"] = j.loc[~j.index.duplicated(), "GEOID"].reindex(d.index).to_numpy()
acs = pd.read_csv(next(RAW.glob("acs5_2024_b19013_*.dat")), sep="|", dtype=str)
acs = acs[acs["GEO_ID"].str.startswith("1400000US25")].copy()
acs["tract"] = acs["GEO_ID"].str[-11:]
acs["income"] = pd.to_numeric(acs["B19013_E001"], errors="coerce")
acs.loc[acs["income"] < 0, "income"] = np.nan
d = d.merge(acs[["tract", "income"]], on="tract", how="left")
d0, d = d, d[d["x"].notna() & d["tract"].notna() & d["income"].notna()].copy()
note("7", d0, d, "parcel location found, inside a census tract with an ACS income estimate")

# ------------------------------------------------------------------ transit (all rapid-transit stations)
with zipfile.ZipFile(RAW / "MBTA_GTFS.zip") as z:
    stops = pd.read_csv(io.BytesIO(z.read("stops.txt")), dtype=str)
    routes = pd.read_csv(io.BytesIO(z.read("routes.txt")), dtype=str)
    trips = pd.read_csv(io.BytesIO(z.read("trips.txt")), dtype=str, usecols=["route_id", "trip_id"])
    stop_times = pd.read_csv(io.BytesIO(z.read("stop_times.txt")), dtype=str, usecols=["trip_id", "stop_id"])
stations = stops[stops["location_type"] == "1"].copy()
sg = gpd.GeoSeries(gpd.points_from_xy(stations.stop_lon.astype(float), stations.stop_lat.astype(float)),
                   crs=4326).to_crs(METRIC)
stations["sx"], stations["sy"] = sg.x.values, sg.y.values
rt_routes = routes.loc[routes["route_type"].isin(["0", "1"]) & (routes["route_id"] != "Mattapan"), "route_id"]
rt_ids = stop_times.merge(trips[trips["route_id"].isin(rt_routes)], on="trip_id")["stop_id"].unique()
parent = stops.set_index("stop_id")["parent_station"]
rt = stations[stations["stop_id"].isin(pd.Series(rt_ids).map(parent).dropna().unique())]
xy = d[["x", "y"]].to_numpy()
D = np.sqrt(((xy[:, None, :] - rt[["sx", "sy"]].to_numpy()[None, :, :]) ** 2).sum(-1))
dates = d["saledate"]
for k, nm in enumerate(rt["stop_name"]):
    if nm in GLX:
        closed = (dates < pd.Timestamp(GLX[nm])).to_numpy().copy()
        if nm == "Lechmere":            # old Lechmere station (same coordinates) open until 2020-05-23
            closed &= (dates > pd.Timestamp("2020-05-23")).to_numpy()
        D[closed, k] = np.inf
d["transit_km"] = D.min(1) / 1000
d["nearest_station"] = rt["stop_name"].to_numpy()[D.argmin(1)]

# ------------------------------------------------------------------ features
d["price"] = d["LS_PRICE"].astype(float)
d["log_price"] = np.log(d["price"])
d["log_area"] = np.log(d["RES_AREA"].astype(float))
d["rooms"] = d["NUM_ROOMS"].where(d["NUM_ROOMS"] > 0).clip(upper=15)
yb = d["YEAR_BUILT"].where(d["YEAR_BUILT"].between(1700, 2027))
d["age_group"] = pd.cut(yb, [1699, 1899, 1939, 1979, 1999, 2027],
                        labels=["pre1900", "1900-1939", "1940-1979", "1980-1999", "2000+"]
                        ).astype(object).fillna("unknown")
lot_sqft = d["LOT_SIZE"].astype(float) * np.where(d["LOT_UNITS"].astype(str).str.upper() == "A", 43560, 1)
d["is_condo"] = (d["group"] == "condo").astype(int)
d["house_log_lot"] = np.where(d["is_condo"] == 0, np.log(lot_sqft.where(lot_sqft > 0)), 0.0)
d["log_income"] = np.log(d["income"])
d["sale_quarter"] = d["saledate"].dt.year.astype(str) + "Q" + d["saledate"].dt.quarter.astype(str)
d["sale_time"] = d["saledate"].dt.year + (d["saledate"].dt.dayofyear - 1) / 365.25
d0, d = d, d[d["rooms"].notna() & ~((d["is_condo"] == 0) & d["house_log_lot"].isna())].copy()
note("8", d0, d, "rooms recorded, and lot size recorded for houses")

keep = ["town", "PROP_ID", "LOC_ID", "group", "is_condo", "saledate", "sale_year", "sale_quarter",
        "sale_time", "price", "log_price", "RES_AREA", "log_area", "rooms", "YEAR_BUILT", "age_group",
        "house_log_lot", "TOTAL_VAL", "FY", "x", "y", "tract", "income", "log_income", "transit_km",
        "nearest_station", "source_file"]
out = d[keep].rename(columns={"RES_AREA": "living_area", "YEAR_BUILT": "year_built",
                              "TOTAL_VAL": "assessed_total", "FY": "assessment_fy"})
out.to_csv(PROC / "crosstown_sales.csv", index=False)
cl = pd.DataFrame(log)
cl.to_csv(RES / "crosstown_cleaning_log.csv", index=False)
print(cl.to_string(index=False))

# ------------------------------------------------------------------ source check (Cambridge)
city = pd.read_csv(PROC / "sales_clean.csv", usecols=["pid", "saledate", "saleprice", "group"],
                   parse_dates=["saledate"])
cam = out[out["town"] == "Cambridge"]
k_city = set(zip(city["saledate"], city["saleprice"].round(0)))
matched = np.array([(s, p) in k_city for s, p in zip(cam["saledate"], cam["price"].round(0))])
same_day = cam["saledate"].isin(set(city["saledate"]))
chk = pd.DataFrame([{
    "massgis_cambridge_sales_in_sample": len(cam),
    "matched_same_date_and_price_in_city_data": int(matched.sum()),
    "share_matched": matched.mean(),
    "share_with_any_city_sale_that_day": same_day.mean(),
    "massgis_last_sale_max_date": str(cam["saledate"].max().date()),
    "city_sales_max_date": str(city["saledate"].max().date())}])
chk.to_csv(RES / "crosstown_source_check.csv", index=False)
print("\n" + chk.T.to_string())
print("\n" + out.groupby("town").agg(n=("price", "size"), median_price=("price", "median"),
                                    condo_share=("is_condo", "mean"), median_area=("living_area", "median"),
                                    median_transit_km=("transit_km", "median"),
                                    first=("saledate", "min"), last=("saledate", "max")).round(2).to_string())
print(out.groupby("town")["nearest_station"].agg(lambda s: s.value_counts().head(3).to_dict()).to_string())
