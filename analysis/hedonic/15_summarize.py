"""Step 15: first look at the cleaned sales, plus a usability check of every other raw source.

WHAT THIS DOES (plain words)
  - Places each sale in its Cambridge neighborhood (point-in-polygon).
  - Writes summary tables: number of sales, median price and median price per sq ft, by home
    type and year, and by neighborhood.
  - Draws four charts (PNG + PDF in figures/hedonic/): sales per year, the price distribution,
    a map of price per sq ft, and the price-per-sq-ft trend.
  - Opens every other raw file (crime, Census, MBTA, MassGIS parcels, DESE) and records what is
    inside (columns, date ranges, counts) in results/hedonic/source_checks.md, so problems show
    up now rather than in the middle of modeling.
  Nothing here is a model or a finding; it is a description of the data.

RUN
  uv run python analysis/hedonic/15_summarize.py
"""
import io
import zipfile
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "hedonic"
PROC = ROOT / "data" / "processed" / "hedonic"
RES = ROOT / "results" / "hedonic"
FIG = ROOT / "figures" / "hedonic"
FIG.mkdir(parents=True, exist_ok=True)

BLUE, ORANGE, AQUA, YELLOW, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#8a8984"
GROUP_ORDER = ["condo", "condo_lux", "single_family", "two_family", "three_family"]
GROUP_LABEL = {"condo": "Condo", "condo_lux": "Luxury condo", "single_family": "Single-family",
               "two_family": "Two-family", "three_family": "Three-family"}
GROUP_COLOR = dict(zip(GROUP_ORDER, [BLUE, AQUA, ORANGE, YELLOW, GREY]))
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "axes.spines.top": False, "axes.spines.right": False})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / f"{name}.png", dpi=200)
    fig.savefig(FIG / f"{name}.pdf")
    plt.close(fig)


# ------------------------------------------------------------------ sales + neighborhoods
sales = pd.read_csv(PROC / "sales_clean.csv", parse_dates=["saledate"])
main = sales[sales["main_sample"]].copy()
hoods = gpd.read_file(RAW / "cambridge_neighborhoods.geojson").to_crs(4326)
name_col = "name" if "name" in hoods.columns else hoods.columns[0]
pts = gpd.GeoDataFrame(main, geometry=gpd.points_from_xy(main["longitude"], main["latitude"]), crs=4326)
pts = gpd.sjoin(pts, hoods[[name_col, "geometry"]], how="left", predicate="within")
pts = pts.rename(columns={name_col: "neighborhood"}).drop(columns="index_right")
outside = int(pts["neighborhood"].isna().sum())


def summarize(g):
    return pd.Series({"sales": len(g), "median_price": g["saleprice"].median(),
                      "median_price_per_sqft": g["price_per_sqft"].median(),
                      "median_living_area": g["interior_livingarea"].median()})


by_gy = pts.groupby(["group", "sale_year"]).apply(summarize, include_groups=False).reset_index()
by_gy.to_csv(RES / "summary_by_group_year.csv", index=False)
by_hood = (pts.groupby("neighborhood").apply(summarize, include_groups=False)
           .sort_values("median_price_per_sqft", ascending=False).reset_index())
by_hood.to_csv(RES / "summary_by_neighborhood.csv", index=False)

# fig 1: sales per year by group (stacked)
piv = by_gy.pivot(index="sale_year", columns="group", values="sales").reindex(columns=GROUP_ORDER).fillna(0)
fig, ax = plt.subplots(figsize=(8, 4.2))
bottom = None
for g in GROUP_ORDER:
    ax.bar(piv.index, piv[g], bottom=bottom, color=GROUP_COLOR[g], label=GROUP_LABEL[g])
    bottom = piv[g] if bottom is None else bottom + piv[g]
ax.set_ylabel("Market sales (main sample)")
ax.set_title("Cambridge residential market sales per year")
ax.legend(frameon=False, ncol=3, fontsize=9)
save(fig, "fig_h1_sales_per_year")

# fig 2: price distribution (log scale) by group
fig, ax = plt.subplots(figsize=(8, 4.2))
for g in GROUP_ORDER:
    v = pts.loc[pts["group"] == g, "saleprice"]
    if len(v):
        ax.hist(v, bins=[10 ** (x / 20) for x in range(100, 145)], histtype="step", lw=1.6,
                color=GROUP_COLOR[g], label=f"{GROUP_LABEL[g]} (n={len(v):,})")
ax.set_xscale("log")
ax.set_xlabel("Sale price (US$, log scale)")
ax.set_ylabel("Number of sales")
ax.set_title("Sale prices by home type (main sample)")
ax.legend(frameon=False, fontsize=9)
save(fig, "fig_h2_price_distribution")

# fig 3: map of price per sq ft (condos + 1-3 family), with neighborhood outlines
fig, ax = plt.subplots(figsize=(7.5, 7))
hoods.boundary.plot(ax=ax, color="#52514e", lw=0.6)
p = pts.dropna(subset=["neighborhood"])
clip_hi = p["price_per_sqft"].quantile(0.98)
sc = ax.scatter(p["longitude"], p["latitude"], c=p["price_per_sqft"].clip(upper=clip_hi), s=3,
                cmap="viridis", alpha=0.7)
cb = fig.colorbar(sc, ax=ax, shrink=0.7)
cb.set_label("Sale price per sq ft (US$; top 2% shown at the cap)")
for _, r in hoods.iterrows():
    c = r.geometry.representative_point()
    ax.annotate(str(r[name_col]), (c.x, c.y), fontsize=7, ha="center", color="#0b0b0b")
ax.set_axis_off()
ax.set_aspect(1 / __import__("math").cos(__import__("math").radians(42.37)))  # undistort lon/lat
ax.set_title(f"Price per sq ft of market sales, {int(p['sale_year'].min())}-{int(p['sale_year'].max())}")
save(fig, "fig_h3_map_price_per_sqft")

# fig 4: median price per sq ft by year and group
fig, ax = plt.subplots(figsize=(8, 4.2))
for g in GROUP_ORDER:
    d = by_gy[by_gy["group"] == g]
    ax.plot(d["sale_year"], d["median_price_per_sqft"], marker="o", ms=3.5, color=GROUP_COLOR[g],
            label=GROUP_LABEL[g])
ax.set_ylabel("Median price per sq ft (US$, nominal)")
ax.set_title("Price per sq ft over time (raw medians, not adjusted for home mix)")
ax.legend(frameon=False, ncol=3, fontsize=9)
save(fig, "fig_h4_price_per_sqft_trend")

# ------------------------------------------------------------------ other raw sources
lines = ["# Source checks (step 15)", "",
         "Automatic description of every raw file, to confirm it can be used in later phases.", "",
         "## Cleaned sales", "",
         f"- Main sample: {len(main):,} sales, {int(main['sale_year'].min())}-"
         f"{int(main['sale_year'].max())}; {outside} fall outside all neighborhood polygons.",
         f"- By group: " + ", ".join(f"{GROUP_LABEL[g]} {int((main['group'] == g).sum()):,}"
                                     for g in GROUP_ORDER), ""]

crime = pd.read_csv(RAW / "cambridge_crime_reports.csv", dtype=str)
crime.columns = [c.strip() for c in crime.columns]
dcol = next(c for c in crime.columns if "report" in c.lower() and "date" in c.lower())
yrs = pd.to_datetime(crime[dcol], format="%m/%d/%Y %I:%M:%S %p", errors="coerce").dt.year
acol = next(c for c in crime.columns if c.lower().replace(" ", "_") == "reporting_area")
lines += ["## Crime reports", "",
          f"- {len(crime):,} reports; columns: {', '.join(crime.columns)}",
          f"- Report years {int(yrs.min())}-{int(yrs.max())}; reports per year (median) "
          f"{int(yrs.value_counts().median()):,}; {crime[acol].nunique()} reporting areas.",
          f"- Rows without a reporting area: {int(crime[acol].isna().sum()):,}.",
          "- Most common types: " + "; ".join(f"{k} ({v:,})" for k, v in
                                              crime[crime.columns[3]].value_counts().head(8).items()), ""]

for t in ("b19013", "b25064"):
    f = next(RAW.glob(f"acs5_2024_{t}_*.dat"))
    acs = pd.read_csv(f, sep="|", dtype=str)
    ma_tracts = acs[acs["GEO_ID"].str.startswith("1400000US25")]
    cam = ma_tracts[ma_tracts["GEO_ID"].str.startswith("1400000US25017")]
    lines += [f"## ACS 2020-2024 table {t.upper()}", "",
              f"- Columns: {', '.join(acs.columns[:6])} ...; Massachusetts tracts: {len(ma_tracts):,}; "
              f"Middlesex County tracts: {len(cam):,}.", ""]

with zipfile.ZipFile(RAW / "MBTA_GTFS.zip") as z:
    stops = pd.read_csv(io.BytesIO(z.read("stops.txt")), dtype=str)
    routes = pd.read_csv(io.BytesIO(z.read("routes.txt")), dtype=str)
stations = stops[stops["location_type"] == "1"]
lines += ["## MBTA GTFS", "",
          f"- {len(stops):,} stops; {len(stations):,} parent stations (location_type = 1); "
          f"route types: {routes['route_type'].value_counts().to_dict()} "
          "(0 = light rail, 1 = subway, 2 = commuter rail, 3 = bus, 4 = ferry).",
          f"- Feed columns: {', '.join(stops.columns[:12])} ...", ""]

lines += ["## MassGIS parcels (5 towns)", ""]
for f in sorted(RAW.glob("L3_SHP_*.zip")):
    with zipfile.ZipFile(f) as z:
        names = z.namelist()
    dbf = next((n for n in names if n.lower().endswith(".dbf") and "assess" in n.lower()), None)
    if dbf is None:
        lines.append(f"- {f.name}: no assessor .dbf found; members: {', '.join(names[:12])}")
        continue
    a = gpd.read_file(f"zip://{f}!{dbf}", ignore_geometry=True)
    sale_cols = [c for c in a.columns if c.upper().startswith(("LS_", "FY", "USE_CODE", "BLD_AREA",
                                                             "RES_AREA", "UNITS", "NUM_ROOMS",
                                                             "YEAR_BUILT", "STYLE"))]
    ls_date = pd.to_datetime(a.get("LS_DATE", pd.Series(dtype=str)).astype(str), format="%Y%m%d",
                             errors="coerce")
    price = pd.to_numeric(a.get("LS_PRICE", pd.Series(dtype=float)), errors="coerce")
    recent = int(((ls_date.dt.year >= 2016) & (price > 1000)).sum())
    fy = a["FY"].mode().iat[0] if "FY" in a.columns else "?"
    lines.append(f"- **{f.name}**: assessor table `{dbf}`, {len(a):,} rows, fiscal year {fy}; "
                 f"sale fields present: {', '.join(sale_cols)}; last sales since 2016 with price > "
                 f"$1,000: {recent:,}.")
lines.append("")

mcas = pd.read_csv(RAW / "dese_mcas_district_5towns.csv", dtype=str)
spend = pd.read_csv(RAW / "dese_per_pupil_spending_5towns.csv", dtype=str)
lines += ["## DESE", "",
          f"- MCAS district rows: {len(mcas):,}; districts {sorted(mcas['dist_name'].unique())}; "
          f"school years {mcas['sy'].min()}-{mcas['sy'].max()}; "
          f"rows with average SGP: {int(pd.to_numeric(mcas['avg_sgp'], errors='coerce').notna().sum()):,}.",
          f"- Per-pupil spending rows: {len(spend):,}; years {spend['sy'].min()}-{spend['sy'].max()}.", ""]

(RES / "source_checks.md").write_text("\n".join(lines))
print("\n".join(lines))
