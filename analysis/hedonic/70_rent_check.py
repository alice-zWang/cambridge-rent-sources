"""Step 70: small tract-level rent check (SPEC_RENTCHECK.md).

WHAT THIS DOES (plain words)
  The Census gives each census tract's median gross rent (rent plus utilities, ACS 2020-2024).
  For the ~31 Cambridge tracts, this compares that rent with the same neighborhood factors used
  for sale prices (crime nearby, tract income, distance to a station) and with condo sale prices
  per square foot. It describes tracts; it is not a model of individual apartments.

OUTPUTS
  results/hedonic/rentcheck_tracts.csv, rentcheck_correlations.csv, rentcheck_regressions.csv,
  figures/hedonic/fig_h19_rent_check (PNG + PDF)

RUN
  uv run python analysis/hedonic/70_rent_check.py
"""
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import spearmanr

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from model_common import FIG, RES, ROOT, load  # noqa: E402

RAW = ROOT / "data" / "raw" / "hedonic"
_, d = load("market_sample")
d = d[d["sale_year"].between(2020, 2024)]
d["tract"] = d["tract"].astype(str).str.zfill(11)
t = d.groupby("tract").agg(sales=("log_price", "size"), violent=("crime_violent_500", "mean"),
                           property=("crime_property_500", "mean"), transit_km=("transit_km", "mean"),
                           income=("income", "first"))
t["condo_ppsf"] = d[d["group"] == "condo"].groupby("tract")["price_per_sqft"].median()
acs = pd.read_csv(next(RAW.glob("acs5_2024_b25064_*.dat")), sep="|", dtype=str)
acs = acs[acs["GEO_ID"].str.startswith("1400000US25")].copy()
acs["tract"] = acs["GEO_ID"].str[-11:]
acs["rent"] = pd.to_numeric(acs["B25064_E001"], errors="coerce")
acs["rent_moe"] = pd.to_numeric(acs["B25064_M001"], errors="coerce")
acs.loc[acs["rent"] < 0, "rent"] = np.nan
acs.loc[acs["rent_moe"] < 0, "rent_moe"] = np.nan
t = t.join(acs.set_index("tract")[["rent", "rent_moe"]], how="left")
n_all = len(t)
t = t[t["rent"].notna()].copy()
t["log_rent"] = np.log(t["rent"])
t["log_income"] = np.log(t["income"])
t["moe_flag"] = t["rent_moe"] / t["rent"] > 0.20
t.to_csv(RES / "rentcheck_tracts.csv")
print(f"tracts with sales 2020-2024: {n_all}; with a rent estimate: {len(t)}; "
      f"flagged (MOE > 20%): {int(t['moe_flag'].sum())}")
print(t[["rent", "rent_moe", "income", "violent", "property", "transit_km", "condo_ppsf"]].describe().round(2).to_string())

FACT = {"violent": "Violent crime nearby", "property": "Property crime nearby",
        "log_income": "Tract income (log)", "transit_km": "Distance to station (km)",
        "condo_ppsf": "Condo price per sq ft"}
cor = []
rng = np.random.default_rng(20261123)
for v, lab in FACT.items():
    s = t[["log_rent", v]].dropna()
    rho, p = spearmanr(s["log_rent"], s[v])
    n = len(s)
    # 95% CI, Fisher z with the Bonett-Wright (2000) standard error for Spearman's rho
    se = np.sqrt((1 + rho ** 2 / 2) / (n - 3))
    lo, hi = np.tanh(np.arctanh(rho) + np.array([-1.96, 1.96]) * se)
    # check: percentile bootstrap over tracts (10,000 resamples)
    a, b = s["log_rent"].to_numpy(), s[v].to_numpy()
    boot = []
    for _ in range(10000):
        i = rng.integers(0, n, n)
        boot.append(spearmanr(a[i], b[i])[0])
    blo, bhi = np.nanpercentile(boot, [2.5, 97.5])
    cor.append({"factor": v, "label": lab, "n_tracts": n, "spearman_rho": rho, "p": p,
                "ci_low_fisher_bw": lo, "ci_high_fisher_bw": hi, "ci_low_boot": blo, "ci_high_boot": bhi})
cor = pd.DataFrame(cor)
cor.to_csv(RES / "rentcheck_correlations.csv", index=False)
print("\n" + cor.round(3).to_string(index=False))

reg = []
for sample, s in [("all tracts", t), ("without MOE-flagged tracts", t[~t["moe_flag"]])]:
    for v in ["violent", "property", "log_income", "transit_km"]:
        r = smf.ols(f"log_rent ~ {v}", data=s).fit(cov_type="HC3")
        reg.append({"sample": sample, "model": "one factor", "factor": v, "n": int(r.nobs),
                    "coef": r.params[v], "se_hc3": r.bse[v], "p": r.pvalues[v], "r2": r.rsquared})
    r = smf.ols("log_rent ~ violent + property + log_income + transit_km", data=s).fit(cov_type="HC3")
    for v in ["violent", "property", "log_income", "transit_km"]:
        reg.append({"sample": sample, "model": "all four", "factor": v, "n": int(r.nobs),
                    "coef": r.params[v], "se_hc3": r.bse[v], "p": r.pvalues[v], "r2": r.rsquared})
reg = pd.DataFrame(reg)
reg.to_csv(RES / "rentcheck_regressions.csv", index=False)
print("\n" + reg.round(4).to_string(index=False))

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False})
BLUE, GREY = "#2a78d6", "#52514e"
fig, axes = plt.subplots(1, 5, figsize=(17, 3.8), sharey=True)
for ax, (v, lab) in zip(axes, FACT.items()):
    s = t[["rent", v, "moe_flag"]].dropna()
    xv = np.exp(s[v]) / 1000 if v == "log_income" else s[v]
    ax.scatter(xv[~s.moe_flag], s.loc[~s.moe_flag, "rent"], color=BLUE, s=22)
    ax.scatter(xv[s.moe_flag], s.loc[s.moe_flag, "rent"], facecolor="none", edgecolor=BLUE, s=22)
    rho = cor.set_index("factor").loc[v, "spearman_rho"]
    ax.set_title(f"rank correlation {rho:+.2f}", fontsize=9.5)
    ax.set_xlabel(lab.replace("(log)", "(\\$ thousand)") if v == "log_income" else
                  (lab + " (\\$)" if v == "condo_ppsf" else lab), fontsize=9)
axes[0].set_ylabel("Tract median gross rent (\\$/month)")
fig.suptitle("Rent check: Cambridge census tracts (ACS 2020–2024). Open circles: margin of error > 20%. "
             "Descriptive only.", fontsize=11)
fig.tight_layout()
fig.savefig(FIG / "fig_h19_rent_check.png", dpi=200)
fig.savefig(FIG / "fig_h19_rent_check.pdf")
print("\nwrote rentcheck_*.csv and fig_h19")
