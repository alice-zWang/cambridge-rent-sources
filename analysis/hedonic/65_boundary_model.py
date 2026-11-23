"""Step 65: Model 5, the price jump at the Cambridge-Somerville line (SPEC_PHASE5.md).

WHAT THIS DOES (plain words)
  Compares similar homes within 250 m of the city line, on the same 1 km stretch of the line and
  sold in the same quarter. Prices may drift gradually with distance on each side; the model
  allows for that and asks whether there is an extra JUMP exactly at the line. That jump is the
  price difference of being in Cambridge rather than Somerville for otherwise similar homes,
  right next to each other: schools (choice of district), taxes, services, all together.
  Checks change one thing at a time. Placebo lines 400 m inside each city should show no jump.

OUTPUTS
  results/hedonic/boundary_model.csv, figures/hedonic/fig_h18_boundary_jump (PNG + PDF)

RUN
  uv run python analysis/hedonic/65_boundary_model.py
"""
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from wildboot import WildClusterBootstrap  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PROC, RES, FIG = (ROOT / "data" / "processed" / "hedonic", ROOT / "results" / "hedonic",
                  ROOT / "figures" / "hedonic")
METRIC = 26986
N_BOOT, SEED = 9999, 20261123
END = pd.Timestamp("2024-07-31")       # last date both cities' files cover

line = gpd.read_file(PROC / "boundary_line.geojson").to_crs(METRIC).geometry.iloc[0]
d = pd.read_csv(PROC / "crosstown_sales.csv", parse_dates=["saledate"])
d = d[d["town"].isin(["Cambridge", "Somerville"]) & (d["saledate"] <= END)].reset_index(drop=True)
pts = gpd.GeoSeries(gpd.points_from_xy(d["x"], d["y"]), crs=METRIC)
d["dist_m"] = pts.distance(line).to_numpy()
d["pos_m"] = [line.project(p) for p in pts]
d["seg"] = (d["pos_m"] // 1000).astype(int)
d["cambridge"] = (d["town"] == "Cambridge").astype(int)
d["dist_cam"] = d["dist_m"] / 100 * d["cambridge"]           # per 100 m, Cambridge side
d["dist_som"] = d["dist_m"] / 100 * (1 - d["cambridge"])     # per 100 m, Somerville side
HOME = ("C(group, Treatment('condo')) + log_area + rooms + C(age_group, Treatment('1900-1939'))"
        " + house_log_lot")
FE = "C(seg) + C(sale_quarter)"


def run(name, s, treat, f, label):
    s = s.reset_index(drop=True)
    groups = pd.factorize(s["tract"])[0]
    r = smf.ols(f, data=s).fit(cov_type="cluster", cov_kwds={"groups": groups})
    j = r.model.exog_names.index(treat)
    wb = WildClusterBootstrap(r.model.exog, r.model.endog, s["tract"].to_numpy(), n_boot=N_BOOT, seed=SEED)
    lo_b, hi_b = wb.ci(j, r.bse[treat])
    ci = r.conf_int().loc[treat]
    pct = lambda b: 100 * (np.exp(b) - 1)  # noqa: E731
    row = {"model": name, "description": label, "n": int(r.nobs), "n_treated_side": int(s[treat].sum())
           if treat in s else np.nan, "tracts": len(np.unique(groups)), "segments": s["seg"].nunique(),
           "coef": r.params[treat], "se_tract": r.bse[treat], "p_tract": r.pvalues[treat],
           "p_wild_bootstrap": wb.pvalue(j), "jump_pct": pct(r.params[treat]),
           "ci_tract": f"{pct(ci[0]):+.1f} to {pct(ci[1]):+.1f}",
           "ci_boot": f"{pct(lo_b):+.1f} to {pct(hi_b):+.1f}", "ci_boot_low": pct(lo_b), "ci_boot_high": pct(hi_b),
           "r2": r.rsquared}
    print(f"{name:28s} n={row['n']:5d}  jump {row['jump_pct']:+6.1f}%  tract CI {row['ci_tract']:>15s}  "
          f"boot CI {row['ci_boot']:>15s}  p_boot={row['p_wild_bootstrap']:.3f}", flush=True)
    return row, r


B1 = f"log_price ~ cambridge + dist_cam + dist_som + {HOME} + transit_km + {FE}"
w250 = d[d["dist_m"] <= 250]
rows = []
row, main = run("B1 main (250 m)", w250, "cambridge", B1, "within 250 m, all controls")
rows.append(row)
rows.append(run("check 1a: 100 m", d[d["dist_m"] <= 100], "cambridge", B1, "within 100 m")[0])
rows.append(run("check 1b: 500 m", d[d["dist_m"] <= 500], "cambridge", B1, "within 500 m")[0])
rows.append(run("check 2: + tract income", w250, "cambridge", B1.replace("transit_km", "transit_km + log_income"),
                "adds log tract income")[0])
rows.append(run("check 3: no transit", w250, "cambridge", B1.replace(" + transit_km", ""),
                "without distance to station")[0])
rows.append(run("check 4: condos only", w250[w250["group"] == "condo"], "cambridge",
                B1.replace("C(group, Treatment('condo')) + ", "").replace(" + house_log_lot", ""), "condos only")[0])
east = d["seg"].max()
rows.append(run("check 6: no eastern segment", w250[w250["seg"] != east], "cambridge", B1,
                f"drops 1 km segment S{east}")[0])

# placebo lines: the 400 m distance contour inside each city, same model on that city's sales only
for town, nm in [("Cambridge", "check 5a: placebo in Cambridge"), ("Somerville", "check 5b: placebo in Somerville")]:
    s = d[(d["town"] == town) & ((d["dist_m"] - 400).abs() <= 250)].copy()
    s["deeper"] = (s["dist_m"] > 400).astype(int)
    s["dist_in"] = (s["dist_m"] - 400) / 100 * s["deeper"]
    s["dist_out"] = (400 - s["dist_m"]) / 100 * (1 - s["deeper"])
    f = f"log_price ~ deeper + dist_in + dist_out + {HOME} + transit_km + {FE}"
    rows.append(run(nm, s, "deeper", f, f"fake line 400 m inside {town}; 'jump' = deeper side vs nearer side")[0])

out = pd.DataFrame(rows)
tax = (10.91 - 6.35) / 1000
out.attrs = {}
out.to_csv(RES / "boundary_model.csv", index=False)
print(f"\ntax-only benchmark: {100 * tax / 0.06:.1f}% (6% discount rate) to {100 * tax / 0.04:.1f}% (4%)")
print("distance slopes (B1, per 100 m): Cambridge side "
      f"{main.params['dist_cam']:+.4f} (se {main.bse['dist_cam']:.4f}), Somerville side "
      f"{main.params['dist_som']:+.4f} (se {main.bse['dist_som']:.4f})")
print("sales per segment and side (B1):\n" + w250.groupby(["seg", "town"]).size().unstack().to_string())

# ------------------------------------------------------------------ figure: adjusted price by distance
# Points: B1 residuals plus B1's own side/distance terms, i.e. price adjusted for the controls
# with B1's coefficients. Lines: B1's fitted jump and distance slopes. Same vertical shift for both.
s = w250.reset_index(drop=True)
P = main.params
side_part = P["cambridge"] * s["cambridge"] + P["dist_cam"] * s["dist_cam"] + P["dist_som"] * s["dist_som"]
shift = side_part[s["cambridge"] == 0].mean() + main.resid[s["cambridge"] == 0].mean()
s["adj"] = main.resid.to_numpy() + side_part.to_numpy() - shift
s["signed"] = np.where(s["cambridge"] == 1, s["dist_m"], -s["dist_m"])
edges = np.arange(-250, 251, 25)
s["bin"] = pd.cut(s["signed"], edges)
b = s.groupby("bin", observed=True)["adj"].agg(["mean", "count", "std"]).reset_index()
b["mid"] = [iv.mid for iv in b["bin"]]
b["se"] = b["std"] / np.sqrt(b["count"])
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10.5,
                     "axes.spines.top": False, "axes.spines.right": False})
BLUE, ORANGE, GREY = "#2a78d6", "#d97a1f", "#52514e"
fig, ax = plt.subplots(figsize=(9, 4.6))
for side, col in [(1, BLUE), (0, ORANGE)]:
    bb = b[(b["mid"] > 0) == bool(side)]
    ax.errorbar(bb["mid"], 100 * bb["mean"], yerr=196 * bb["se"], fmt="o", color=col, capsize=3, ms=5,
                label="Cambridge side" if side else "Somerville side")
    xx = np.array([0, 250]) if side else np.array([-250, 0])
    yy = (P["cambridge"] + P["dist_cam"] * xx / 100) if side else (P["dist_som"] * -xx / 100)
    ax.plot(xx, 100 * (yy - shift), color=col, lw=1.5)
ax.axvline(0, color=GREY, lw=1, ls="--")
ax.text(3, ax.get_ylim()[1], " city line", va="top", fontsize=8.5, color=GREY)
ax.axhline(0, color=GREY, lw=0.6)
ax.set_xlabel("Distance from the line (m): Somerville ← | → Cambridge")
ax.set_ylabel("Adjusted log price × 100\n(Somerville side average = 0)")
r0 = out.iloc[0]
ax.set_title(f"Model 5: price jump at the Cambridge–Somerville line ≈ {r0['jump_pct']:+.0f}% "
             f"(cautious 95% range {r0['ci_boot']}%)", fontsize=11)
ax.legend(frameon=False, loc="upper left")
fig.text(0.01, 0.01, "Points: 25 m averages adjusted (main model) for home features, station distance, "
         "1 km stretch, sale quarter. Lines: model fit. Bars: 95% CI. Sales 2016–Jul 2024.",
         fontsize=7.5, color=GREY)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(FIG / "fig_h18_boundary_jump.png", dpi=200)
fig.savefig(FIG / "fig_h18_boundary_jump.pdf")
print("\nwrote boundary_model.csv and fig_h18")
