"""Step 60: is a Cambridge-Somerville boundary comparison feasible? (counts only, no model)

WHAT THIS DOES (plain words)
  Model 5 would compare similar homes just either side of the Cambridge-Somerville city line.
  Before any model is run, PLAN.md asks for the counts: how many sales lie near the line, on each
  side, along which stretches of it, and whether the homes on the two sides look alike.
    - The city line is the outline of Cambridge (union of the city's neighborhood polygons), kept
      only where Somerville parcels lie right next to it.
    - Each sale (MassGIS last-sale data, both cities, same fields; from 55_crosstown_build.py) gets
      its distance to the line and its position along it (for segment fixed effects).
    - Counts by distance band, side, home type and 500 m / 1 km segment; a balance table; a map.

OUTPUTS
  results/hedonic/boundary_counts.csv, boundary_segments.csv, boundary_balance.csv,
  data/processed/hedonic/boundary_line.geojson, figures/hedonic/fig_h17_boundary_map (PNG + PDF)

RUN
  uv run python analysis/hedonic/60_boundary_feasibility.py
"""
import zipfile
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
from shapely.geometry import LineString, MultiLineString
from shapely.ops import linemerge

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RAW, PROC = ROOT / "data" / "raw" / "hedonic", ROOT / "data" / "processed" / "hedonic"
RES, FIG = ROOT / "results" / "hedonic", ROOT / "figures" / "hedonic"
METRIC = 26986
ADJ = 60          # a stretch of the Cambridge outline counts as the Somerville line if Somerville
                  # parcels lie within 60 m (street widths); other stretches border Boston, etc.
BANDS = [100, 250, 500]

# ------------------------------------------------------------------ the line
cam = gpd.read_file(RAW / "cambridge_neighborhoods.geojson").to_crs(METRIC).union_all()
z = next(RAW.glob("L3_SHP_M274_*.zip"))
tp = next(n for n in zipfile.ZipFile(z).namelist() if "TaxPar" in n and n.endswith(".shp"))
som = gpd.read_file(f"zip://{z}!{tp}").to_crs(METRIC).union_all()
outline = cam.exterior
shared = outline.intersection(som.buffer(ADJ))
parts = [g for g in getattr(shared, "geoms", [shared]) if isinstance(g, LineString)]
merged = linemerge(MultiLineString(parts))
lines = [g for g in getattr(merged, "geoms", [merged]) if g.length > 100]   # drop slivers
lines.sort(key=lambda g: -g.length)
border = MultiLineString(lines)
gpd.GeoDataFrame({"part": range(len(lines)), "length_m": [g.length for g in lines]},
                 geometry=lines, crs=METRIC).to_crs(4326).to_file(PROC / "boundary_line.geojson",
                                                                   driver="GeoJSON")
print(f"shared line: {border.length / 1000:.2f} km in {len(lines)} piece(s): "
      f"{[round(g.length) for g in lines]} m")

# ------------------------------------------------------------------ sales near the line
d = pd.read_csv(PROC / "crosstown_sales.csv", parse_dates=["saledate"])
d = d[d["town"].isin(["Cambridge", "Somerville"])].reset_index(drop=True)
pts = gpd.GeoSeries(gpd.points_from_xy(d["x"], d["y"]), crs=METRIC)
d["dist_m"] = pts.distance(border).to_numpy()
inside = pts.within(cam).to_numpy()
d["side_check"] = np.where(inside, "Cambridge", "Somerville")
mismatch = int((d["side_check"] != d["town"]).sum())
offset = np.cumsum([0] + [g.length for g in lines[:-1]])
pos = []
for p in pts:
    k = int(np.argmin([g.distance(p) for g in lines]))
    pos.append(offset[k] + lines[k].project(p))
d["pos_m"] = pos
d["seg500"] = (d["pos_m"] // 500).astype(int)
d["seg1000"] = (d["pos_m"] // 1000).astype(int)
near = d[d["dist_m"] <= max(BANDS)].copy()
near.to_csv(PROC / "boundary_sales_500m.csv", index=False)
print(f"sales whose location is on the wrong side of the outline: {mismatch} "
      f"(of {len(d):,}; parcel centroids on the line itself)")

rows = []
for b in BANDS:
    s = d[d["dist_m"] <= b]
    for town in ["Cambridge", "Somerville"]:
        t = s[s["town"] == town]
        rows.append({"band_m": b, "town": town, "sales": len(t),
                     **{f"n_{g}": int((t["group"] == g).sum()) for g in
                        ["condo", "single_family", "two_family", "three_family"]},
                     "first_sale": t["saledate"].min().date(), "last_sale": t["saledate"].max().date()})
counts = pd.DataFrame(rows)
counts.to_csv(RES / "boundary_counts.csv", index=False)
print("\n" + counts.to_string(index=False))

seg = []
for col, size in [("seg500", 500), ("seg1000", 1000)]:
    for b in [250, 500]:
        s = d[d["dist_m"] <= b]
        tab = s.groupby([col, "town"]).size().unstack(fill_value=0).reindex(columns=["Cambridge", "Somerville"],
                                                                         fill_value=0)
        for k, r in tab.iterrows():
            seg.append({"segment_m": size, "band_m": b, "segment": k, "cambridge": r["Cambridge"],
                        "somerville": r["Somerville"], "both_sides_ge_20": bool(min(r) >= 20)})
segs = pd.DataFrame(seg)
segs.to_csv(RES / "boundary_segments.csv", index=False)
for size in [500, 1000]:
    for b in [250, 500]:
        s = segs[(segs.segment_m == size) & (segs.band_m == b)]
        usable = s[s.both_sides_ge_20]
        print(f"{size} m segments, within {b} m: {len(s)} segments, {len(usable)} with >= 20 sales on each "
              f"side, covering {usable[['cambridge', 'somerville']].sum().to_dict()}")

bal = []
for b in [250, 500]:
    s = d[d["dist_m"] <= b]
    for v in ["log_area", "rooms", "is_condo", "year_built", "house_log_lot", "sale_time", "transit_km",
              "log_income", "log_price"]:
        a = s.loc[s.town == "Cambridge", v].astype(float)
        c = s.loc[s.town == "Somerville", v].astype(float)
        a = a[a > 1700] if v == "year_built" else a
        c = c[c > 1700] if v == "year_built" else c
        sd = np.sqrt((a.var() + c.var()) / 2)
        bal.append({"band_m": b, "variable": v, "mean_cambridge": a.mean(), "mean_somerville": c.mean(),
                    "std_difference": (a.mean() - c.mean()) / sd if sd > 0 else np.nan})
bal = pd.DataFrame(bal)
bal.to_csv(RES / "boundary_balance.csv", index=False)
print("\n" + bal.round(3).to_string(index=False))

# ------------------------------------------------------------------ map
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
fig, ax = plt.subplots(figsize=(8, 8))
gpd.GeoSeries([cam], crs=METRIC).plot(ax=ax, color="#eef3fb", edgecolor="#9aa7b8", lw=0.6)
gpd.GeoSeries([som], crs=METRIC).plot(ax=ax, color="#fbf1e6", edgecolor="none")
gpd.GeoSeries(lines, crs=METRIC).plot(ax=ax, color="#222222", lw=2)
s = d[d["dist_m"] <= 500]
for town, col in [("Cambridge", "#2a78d6"), ("Somerville", "#d97a1f")]:
    t = s[s.town == town]
    ax.scatter(t.x, t.y, s=4, color=col, alpha=0.6, label=f"{town}: {len(t):,} sales within 500 m")
for k in range(int(d.loc[d.dist_m <= 500, "seg1000"].max()) + 1):
    target = k * 1000 + 500
    k_line = int(np.searchsorted(offset, target, side="right") - 1)
    if target - offset[k_line] <= lines[k_line].length:
        p = lines[k_line].interpolate(target - offset[k_line])
        ax.annotate(f"S{k}", (p.x, p.y), fontsize=8, weight="bold", ha="center",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="#222222", lw=0.5))
ax.set_xlim(s.x.min() - 800, s.x.max() + 800)
ax.set_ylim(s.y.min() - 800, s.y.max() + 800)
ax.set_axis_off()
ax.legend(loc="lower left", frameon=True, fontsize=8.5, markerscale=3)
ax.set_title("Cambridge–Somerville line (black) and last sales within 500 m\n"
             "S0, S1, ... = 1 km segments along the line", fontsize=11)
fig.text(0.01, 0.01, "MassGIS last-sale data, 2016 onward. Blue area: Cambridge; tan: Somerville parcels.",
         fontsize=7.5, color="#52514e")
fig.tight_layout()
fig.savefig(FIG / "fig_h17_boundary_map.png", dpi=200)
fig.savefig(FIG / "fig_h17_boundary_map.pdf")
print("\nwrote boundary_*.csv, boundary_line.geojson, boundary_sales_500m.csv, fig_h17")
