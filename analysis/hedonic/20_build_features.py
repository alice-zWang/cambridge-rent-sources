"""Step 20: attach neighborhood, census tract income, crime and transit distance to every sale.

WHAT THIS DOES (plain words)
  For each cleaned sale it works out, following the rules fixed in SPEC_MODEL1.md:
    - which of Cambridge's neighborhoods it is in, and which census tract;
    - the median household income of that tract (Census ACS 2020-2024) and its margin of error;
    - how many violent crimes and property crimes against residents were reported nearby
      (within 500 m, also 300 m and 800 m) in the three years before the sale, per year per km2;
    - the straight-line distance to the nearest MBTA rapid-transit station that was open on the
      sale date (so a 2019 sale is not credited with a Green Line station that opened in 2022);
    - tidy versions of the home features (age group, condition, grade, parking).
  It writes data/processed/hedonic/sales_features.csv and logs every row lost in
  results/hedonic/feature_log.csv.

RUN
  uv run python analysis/hedonic/20_build_features.py
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
METRIC = 26986  # Massachusetts State Plane (metres)

VIOLENT = ["Homicide", "Kidnapping", "Aggravated Assault", "Simple Assault", "Street Robbery",
           "Commercial Robbery"]
PROPERTY = ["Housebreak", "Larceny from Residence", "Larceny from MV", "Auto Theft",
            "Larceny of Plate", "Larceny of Bicycle", "Mal. Dest. Property", "Arson"]
RADII = (300, 500, 800)
CRIME_YEARS_BEFORE = 3
SQUARES = ["Harvard", "Central", "Kendall/MIT", "Porter", "Alewife"]  # commercial-square proxy
SQUARE_RADIUS = 300

# stations north of the Charles River, with opening/closing dates (SPEC_MODEL1.md section 4)
ALWAYS = ["Alewife", "Davis", "Porter", "Harvard", "Central", "Kendall/MIT",
          "Science Park/West End", "Assembly", "Sullivan Square", "Community College"]
STATION_WINDOWS = {name: (None, None) for name in ALWAYS}
STATION_WINDOWS["Lechmere (old)"] = (None, "2020-05-23")      # last day open
STATION_WINDOWS["Lechmere"] = ("2022-03-21", None)            # first day open
STATION_WINDOWS["Union Square"] = ("2022-03-21", None)
for s in ["East Somerville", "Gilman Square", "Magoun Square", "Ball Square", "Medford/Tufts"]:
    STATION_WINDOWS[s] = ("2022-12-12", None)
GLX_ALL = {"Lechmere": "2022-03-21", "Union Square": "2022-03-21", "East Somerville": "2022-12-12",
           "Gilman Square": "2022-12-12", "Magoun Square": "2022-12-12", "Ball Square": "2022-12-12",
           "Medford/Tufts": "2022-12-12"}

log = []


def note(step, before, after, rule):
    log.append({"step": step, "rule": rule, "rows_before": before, "rows_after": after,
                "rows_removed": before - after})


# ------------------------------------------------------------------ sales
sales = pd.read_csv(PROC / "sales_clean.csv", parse_dates=["saledate"])
n0 = len(sales)
sales = sales[sales["main_sample"]].copy()
note("1", n0, len(sales), "keep main_sample (not multi-parcel, not below 10% of assessed value)")
# flagged sales are kept in a separate file for the robustness check
all_sales = pd.read_csv(PROC / "sales_clean.csv", parse_dates=["saledate"])

pts = gpd.GeoDataFrame(all_sales, geometry=gpd.points_from_xy(all_sales.longitude, all_sales.latitude),
                       crs=4326).to_crs(METRIC)
xy = np.column_stack([pts.geometry.x, pts.geometry.y])

# ------------------------------------------------------------------ neighborhood
hoods = gpd.read_file(RAW / "cambridge_neighborhoods.geojson").to_crs(METRIC)
name_col = "name" if "name" in hoods.columns else hoods.columns[0]
j = gpd.sjoin(pts[["geometry"]], hoods[[name_col, "geometry"]], how="left", predicate="within")
j = j[~j.index.duplicated()]
all_sales["neighborhood"] = j[name_col]

# ------------------------------------------------------------------ tract + income
tracts = gpd.read_file(f"zip://{RAW / 'cb_2023_25_tract_500k.zip'}").to_crs(METRIC)
j = gpd.sjoin(pts[["geometry"]], tracts[["GEOID", "geometry"]], how="left", predicate="within")
j = j[~j.index.duplicated()]
all_sales["tract"] = j["GEOID"]
acs = pd.read_csv(next(RAW.glob("acs5_2024_b19013_*.dat")), sep="|", dtype=str)
acs = acs[acs["GEO_ID"].str.startswith("1400000US25")].copy()
acs["tract"] = acs["GEO_ID"].str[-11:]
acs["income"] = pd.to_numeric(acs["B19013_E001"], errors="coerce")
acs["income_moe"] = pd.to_numeric(acs["B19013_M001"], errors="coerce")
acs.loc[acs["income"] < 0, "income"] = np.nan          # Census codes for "not available"
acs.loc[acs["income_moe"] < 0, "income_moe"] = np.nan
all_sales = all_sales.merge(acs[["tract", "income", "income_moe"]], on="tract", how="left")
all_sales["log_income"] = np.log(all_sales["income"])

# ------------------------------------------------------------------ crime
crime = pd.read_csv(RAW / "cambridge_crime_reports.csv", dtype=str)
crime["date"] = pd.to_datetime(crime["Date of Report"], format="%m/%d/%Y %I:%M:%S %p", errors="coerce")
crime["year"] = crime["date"].dt.year
crime["lat"] = pd.to_numeric(crime["Reporting Area Lat"], errors="coerce")
crime["lon"] = pd.to_numeric(crime["Reporting Area Lon"], errors="coerce")
crime["cat"] = np.select([crime["Crime"].isin(VIOLENT), crime["Crime"].isin(PROPERTY)],
                         ["violent", "property"], "excluded")
crime_counts = {"reports": len(crime), "no_date": int(crime["date"].isna().sum()),
                "no_location": int(crime[["lat", "lon"]].isna().any(axis=1).sum()),
                **crime["cat"].value_counts().to_dict()}
crime = crime.dropna(subset=["year", "lat", "lon"])
crime = crime[crime["cat"] != "excluded"]
areas = crime.groupby(["lat", "lon"]).size().reset_index()[["lat", "lon"]]
ag = gpd.GeoSeries(gpd.points_from_xy(areas.lon, areas.lat), crs=4326).to_crs(METRIC)
areas["x"], areas["y"] = ag.x.values, ag.y.values
areas["area_id"] = range(len(areas))
crime = crime.merge(areas, on=["lat", "lon"])

# GTFS stations
with zipfile.ZipFile(RAW / "MBTA_GTFS.zip") as z:
    stops = pd.read_csv(io.BytesIO(z.read("stops.txt")), dtype=str)
    routes = pd.read_csv(io.BytesIO(z.read("routes.txt")), dtype=str)
    trips = pd.read_csv(io.BytesIO(z.read("trips.txt")), dtype=str, usecols=["route_id", "trip_id"])
    stop_times = pd.read_csv(io.BytesIO(z.read("stop_times.txt")), dtype=str,
                             usecols=["trip_id", "stop_id"])
stations = stops[stops["location_type"] == "1"].copy()
stations["stop_lat"] = stations["stop_lat"].astype(float)
stations["stop_lon"] = stations["stop_lon"].astype(float)
sg = gpd.GeoSeries(gpd.points_from_xy(stations.stop_lon, stations.stop_lat), crs=4326).to_crs(METRIC)
stations["x"], stations["y"] = sg.x.values, sg.y.values
st_xy = stations.set_index("stop_name")[["x", "y"]]

# commercial-square flag for reporting areas
sq = st_xy.loc[SQUARES].to_numpy()
d_sq = np.sqrt(((areas[["x", "y"]].to_numpy()[:, None, :] - sq[None, :, :]) ** 2).sum(-1)).min(axis=1)
areas["square"] = d_sq <= SQUARE_RADIUS
crime = crime.merge(areas[["area_id", "square"]], on="area_id")

# counts per area x year x category (all, and without squares)
cnt = crime.groupby(["area_id", "year", "cat"]).size().unstack("cat", fill_value=0)
full_idx = pd.MultiIndex.from_product([areas["area_id"], range(2009, 2027)], names=["area_id", "year"])
cnt = cnt.reindex(full_idx, fill_value=0)
area_xy = areas.set_index("area_id")[["x", "y"]].to_numpy()
d_area = np.sqrt(((xy[:, None, :] - area_xy[None, :, :]) ** 2).sum(-1))   # sales x areas, metres
square_mask = areas.set_index("area_id")["square"].to_numpy()

years = all_sales["sale_year"].to_numpy()
for cat in ("violent", "property"):
    mat = cnt[cat].unstack("year")                                     # areas x years
    win = np.zeros((len(all_sales), len(areas)))
    for y in np.unique(years):
        cols = [c for c in range(y - CRIME_YEARS_BEFORE, y) if c in mat.columns]
        win[years == y] = mat[cols].sum(axis=1).to_numpy()[None, :]
    for r in RADII:
        within = d_area <= r
        km2 = np.pi * (r / 1000) ** 2
        all_sales[f"crime_{cat}_{r}"] = (win * within).sum(1) / CRIME_YEARS_BEFORE / km2
        if r == 500:
            all_sales[f"crime_{cat}_500_nosq"] = ((win * (within & ~square_mask[None, :])).sum(1)
                                                  / CRIME_YEARS_BEFORE / km2)
# report per 100 per km2 per year for readable coefficients later
for c in [c for c in all_sales.columns if c.startswith("crime_")]:
    all_sales[c] = all_sales[c] / 100.0

# ------------------------------------------------------------------ transit
dates = all_sales["saledate"]
names, open_mask = [], []
for name, (start, end) in STATION_WINDOWS.items():
    src = "Lechmere" if name == "Lechmere (old)" else name
    names.append(src)
    m = np.ones(len(all_sales), bool)
    if start:
        m &= (dates >= pd.Timestamp(start)).to_numpy()
    if end:
        m &= (dates <= pd.Timestamp(end)).to_numpy()
    open_mask.append(m)
open_mask = np.column_stack(open_mask)
sxy = st_xy.loc[names].to_numpy()
d_st = np.sqrt(((xy[:, None, :] - sxy[None, :, :]) ** 2).sum(-1))
d_st = np.where(open_mask, d_st, np.inf)
all_sales["transit_km"] = d_st.min(1) / 1000
all_sales["nearest_station"] = np.array(list(STATION_WINDOWS))[d_st.argmin(1)]

# sensitivity: all rapid-transit stations in the feed (both sides of the river), GLX gated by date
rt_routes = routes.loc[routes["route_type"].isin(["0", "1"]) & (routes["route_id"] != "Mattapan"),
                       "route_id"]
rt_stop_ids = stop_times.merge(trips[trips["route_id"].isin(rt_routes)], on="trip_id")["stop_id"].unique()
parent = stops.set_index("stop_id")["parent_station"]
rt_parents = pd.Series(rt_stop_ids).map(parent).dropna().unique()
rt = stations[stations["stop_id"].isin(rt_parents)]
d_all = np.sqrt(((xy[:, None, :] - rt[["x", "y"]].to_numpy()[None, :, :]) ** 2).sum(-1))
for k, nm in enumerate(rt["stop_name"]):
    if nm in GLX_ALL:
        d_all[(dates < pd.Timestamp(GLX_ALL[nm])).to_numpy(), k] = np.inf
    if nm == "Lechmere":  # old Lechmere open until 2020-05-23
        old = (dates <= pd.Timestamp("2020-05-23")).to_numpy()
        d_all[old, k] = np.sqrt(((xy[old] - st_xy.loc["Lechmere"].to_numpy()) ** 2).sum(-1))
all_sales["transit_km_allstations"] = d_all.min(1) / 1000
all_sales["transit_band"] = pd.cut(all_sales["transit_km"], [0, 0.4, 0.8, 1.2, np.inf],
                                   labels=["<400m", "400-800m", "800-1200m", ">1200m"], right=False)

# ------------------------------------------------------------------ home features (tidy)
yb = all_sales["condition_yearbuilt"].where(all_sales["condition_yearbuilt"].between(1700, 2027))
all_sales["age_group"] = pd.cut(yb, [1699, 1899, 1939, 1979, 1999, 2027],
                                labels=["pre1900", "1900-1939", "1940-1979", "1980-1999", "2000+"]
                                ).astype(object).fillna("unknown")
cond_map = {"Superior": "Excellent+", "Excellent": "Excellent+", "Very Good": "Very Good",
            "Good": "Good", "Average": "Average", "Fair": "Below average", "Poor": "Below average",
            "Very Poor": "Below average"}
grade_map = {"Estate Quality": "Excellent+", "Excellent": "Excellent+", "Very Good Ex": "Excellent+",
             "Very Good": "Very Good", "Good Very Good": "Very Good", "Good": "Good",
             "Average Plus": "Average", "Average": "Average", "Average Minus": "Average",
             "Fair": "Below average", "Poor": "Below average"}
all_sales["condition"] = all_sales["condition_overallcondition"].map(cond_map)
all_sales["grade"] = all_sales["condition_overallgrade"].map(grade_map)
all_sales["log_area"] = np.log(all_sales["interior_livingarea"])
all_sales["bedrooms"] = all_sales["interior_bedrooms"].clip(upper=6)
all_sales["fullbaths"] = all_sales["interior_fullbaths"].clip(upper=4)
all_sales["halfbaths"] = all_sales["interior_halfbaths"].clip(upper=2)
all_sales["parking"] = (all_sales[["parking_open", "parking_covered", "parking_garage"]]
                        .fillna(0).sum(axis=1).clip(upper=4))
all_sales["floor"] = pd.to_numeric(all_sales["exterior_floorlocation"], errors="coerce")
all_sales["log_land"] = np.log(all_sales["landarea"].where(all_sales["landarea"] > 0))

# ------------------------------------------------------------------ likely deed-restricted sales
# Added in Phase 3 after seeing Model 1 residuals (not pre-specified): a group of condo sales at
# about $250/sq ft, whose assessed values are just as low (often one flat value for every unit in a
# building). This is the pattern of deed-restricted affordable homes, whose resale price is capped,
# so they are not market sales. The flag needs BOTH a low assessment and a low price, each below
# half the median per sq ft for the same home type (assessment: same fiscal year; price: same sale
# year), so a genuine bargain with a normal assessment is not flagged. It does not change
# model_sample (Phases 2-3, as pre-specified; re-run without the flag in 45_restricted_check.py).
# Decision 2026-11-22 (user): from Phase 4 on the main sample is market_sample = model_sample
# without flagged sales (see below).
RESTRICT_REL = 0.5
a_ppsf = all_sales["assessedvalue"] / all_sales["interior_livingarea"]
all_sales["rel_assessed_ppsf"] = a_ppsf / a_ppsf.groupby(
    [all_sales["group"], all_sales["yearofassessment"]]).transform("median")
all_sales["rel_price_ppsf"] = all_sales["price_per_sqft"] / all_sales.groupby(
    ["group", "sale_year"])["price_per_sqft"].transform("median")
all_sales["flag_restricted_likely"] = ((all_sales["rel_assessed_ppsf"] < RESTRICT_REL)
                                       & (all_sales["rel_price_ppsf"] < RESTRICT_REL))

# ------------------------------------------------------------------ sample accounting + write
keep_cols = ["neighborhood", "tract", "log_income"]
for flagged in (False, True):
    d = all_sales if flagged else all_sales[all_sales["main_sample"]]
    if not flagged:
        n = len(d)
        d = d[d["neighborhood"].notna()]
        note("2", n, len(d), "inside a Cambridge neighborhood polygon")
        n = len(d)
        d = d[d["tract"].notna()]
        note("3", n, len(d), "inside a census tract")
        n = len(d)
        d = d[d["log_income"].notna()]
        note("4", n, len(d), "tract has an ACS income estimate")
        n = len(d)
        d = d[d["condition"].notna() & d["grade"].notna()]
        note("5", n, len(d), "condition and grade recorded")
        model_ids = set(d["pid"].astype(str) + d["saledate"].astype(str))

all_sales["model_sample"] = (all_sales["pid"].astype(str) + all_sales["saledate"].astype(str)).isin(model_ids)
# Phase 4 on: main sample without likely deed-restricted sales (decided after seeing results).
all_sales["market_sample"] = all_sales["model_sample"] & ~all_sales["flag_restricted_likely"]
note("6", int(all_sales["model_sample"].sum()), int(all_sales["market_sample"].sum()),
     "Phase 4 on only: drop likely deed-restricted sales (market_sample)")
all_sales["robust_sample"] = (all_sales[keep_cols].notna().all(axis=1) & all_sales["condition"].notna()
                              & all_sales["grade"].notna())
out = all_sales.drop(columns=[c for c in all_sales.columns if c == "geometry"])
out.to_csv(PROC / "sales_features.csv", index=False)
pd.DataFrame(log).to_csv(RES / "feature_log.csv", index=False)

m = out[out["model_sample"]]
print(pd.DataFrame(log).to_string(index=False))
print("crime reports:", crime_counts)
print(f"reporting areas: {len(areas)}, of which near a commercial square: {int(areas['square'].sum())}")
print(f"market sample (Phase 4 on): {int(out['market_sample'].sum()):,}")
print(f"model sample: {len(m):,}; tracts {m['tract'].nunique()}; neighborhoods {m['neighborhood'].nunique()}")
print(m[["crime_violent_500", "crime_property_500", "income", "transit_km",
         "transit_km_allstations"]].describe().round(2).to_string())
print(m["nearest_station"].value_counts().to_string())
print(m["age_group"].value_counts().to_string())
print(f"likely deed-restricted (flag only): {int(m['flag_restricted_likely'].sum())} sales at "
      f"{m.loc[m['flag_restricted_likely']].groupby(['latitude', 'longitude']).ngroups} locations")
