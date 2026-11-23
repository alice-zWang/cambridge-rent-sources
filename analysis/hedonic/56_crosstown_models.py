"""Step 56: cross-town comparison (Cambridge, Somerville, Arlington, Newton, Brookline).

WHAT THIS DOES (plain words)
  Cambridge assigns schools by Controlled Choice, so schools cannot be studied inside the city.
  Here five towns are compared:
    C1  For comparable homes (same type, size, rooms, age, lot, distance to the T, tract income,
        sale quarter), how much more or less do they sell for in each town than in Cambridge?
        That "town premium" is a BUNDLE: schools, taxes, services, location, everything else.
    C2  Is extra living space worth more in some towns than others?
    C3  The same comparison with gradient boosting (a flexible model), as a check.
  Then a 5-row table puts school measures (state MCAS tests, spending per pupil) and tax rates
  next to the town premiums. With five towns, a school pattern cannot be separated from a town
  pattern, so no line is fitted.
  Pre-specified in SPEC_PHASE4.md, Part B.

OUTPUTS
  results/hedonic/crosstown_c1_town_premium.csv, crosstown_c2_area_by_town.csv,
  crosstown_c3_boosting.csv, crosstown_school_context.csv; figures fig_h15, fig_h16

RUN
  uv run python analysis/hedonic/56_crosstown_models.py
"""
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import shap
import statsmodels.formula.api as smf

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from sklearn.model_selection import GroupKFold  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from boost_common import make_model  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RAW, PROC = ROOT / "data" / "raw" / "hedonic", ROOT / "data" / "processed" / "hedonic"
RES, FIG = ROOT / "results" / "hedonic", ROOT / "figures" / "hedonic"
TOWNS = ["Cambridge", "Somerville", "Arlington", "Newton", "Brookline"]
SEED = 20261122

d = pd.read_csv(PROC / "crosstown_sales.csv", parse_dates=["saledate"])
groups = pd.factorize(d["tract"])[0]
TOWN = "C(town, Treatment('Cambridge'))"
X_HOME = ("C(group, Treatment('condo')) + log_area + rooms + C(age_group, Treatment('1900-1939'))"
          " + house_log_lot")
F_MAIN = f"log_price ~ {X_HOME} + transit_km + log_income + {TOWN} + C(sale_quarter)"
F_NOINC = f"log_price ~ {X_HOME} + transit_km + {TOWN} + C(sale_quarter)"


def fit(f):
    return smf.ols(f, data=d).fit(cov_type="cluster", cov_kwds={"groups": groups})


def pct(b):
    return 100 * (np.exp(b) - 1)


# ------------------------------------------------------------------ C1 town premium
rows = []
for spec, f in [("main (with tract income)", F_MAIN), ("check: without tract income", F_NOINC)]:
    r = fit(f)
    ci = r.conf_int()
    for t in TOWNS[1:]:
        k = f"{TOWN}[T.{t}]"
        rows.append({"spec": spec, "town": t, "n": int(r.nobs), "r2": r.rsquared, "coef": r.params[k],
                     "se_tract": r.bse[k], "p": r.pvalues[k], "premium_pct": pct(r.params[k]),
                     "ci_low_pct": pct(ci.loc[k, 0]), "ci_high_pct": pct(ci.loc[k, 1])})
    if spec.startswith("main"):
        main = r
c1 = pd.DataFrame(rows)
c1.to_csv(RES / "crosstown_c1_town_premium.csv", index=False)
print(c1.round(3).to_string(index=False))
print("\nother coefficients (main):")
for k in ["log_area", "rooms", "house_log_lot", "transit_km", "log_income"]:
    print(f"  {k:15s} {main.params[k]:+.4f}  (se {main.bse[k]:.4f})")

# ------------------------------------------------------------------ C2 area x town (rooms x town check)
rows, tests = [], []
for var in ["log_area", "rooms"]:
    r = fit(F_MAIN.replace(f"+ {TOWN}", f"+ {TOWN} + {var}:{TOWN}"))
    names = [n for n in r.params.index if n.startswith(f"{var}:")]
    w = r.wald_test(" , ".join(f"{n} = 0" for n in names), scalar=True)
    tests.append({"variable": var, "wald_F": float(w.statistic), "df": len(names), "p": float(w.pvalue)})
    for t in TOWNS:
        L = np.zeros(len(r.params))
        L[list(r.params.index).index(var)] = 1
        if t != "Cambridge":
            L[list(r.params.index).index(f"{var}:{TOWN}[T.{t}]")] = 1
        est = float(L @ r.params.to_numpy())
        se = float(np.sqrt(L @ r.cov_params().to_numpy() @ L))
        rows.append({"variable": var, "town": t, "slope": est, "se_tract": se,
                     "ci_low": est - 1.96 * se, "ci_high": est + 1.96 * se})
c2 = pd.DataFrame(rows)
c2 = c2.merge(pd.DataFrame(tests), on="variable")
c2.to_csv(RES / "crosstown_c2_area_by_town.csv", index=False)
print("\n" + c2.round(4).to_string(index=False))

# ------------------------------------------------------------------ C3 gradient boosting
X = pd.DataFrame({"log_area": d["log_area"], "rooms": d["rooms"], "is_condo": d["is_condo"],
                  "year_built": d["year_built"].where(d["year_built"].between(1700, 2027)),
                  "house_log_lot": d["house_log_lot"], "transit_km": d["transit_km"],
                  "log_income": d["log_income"], "sale_time": d["sale_time"]})
X = pd.concat([X, pd.get_dummies(d["group"], prefix="group", dtype=float),
               pd.get_dummies(d["town"], prefix="town", dtype=float)], axis=1)
y = d["log_price"].to_numpy()
import patsy  # noqa: E402

_, D = patsy.dmatrices(F_MAIN, d, return_type="matrix")
D = np.asarray(D)
oof = {"boosting": np.zeros(len(y)), "OLS (C1)": np.zeros(len(y))}
for tr, te in GroupKFold(n_splits=10).split(X, y, d["tract"]):
    oof["boosting"][te] = make_model().fit(X.iloc[tr], y[tr]).predict(X.iloc[te])
    oof["OLS (C1)"][te] = D[te] @ np.linalg.lstsq(D[tr], y[tr], rcond=None)[0]
cvr = [{"model": k, "cv": "tracts held out (10 folds)", "rmse": np.sqrt(np.mean((y - p) ** 2)),
        "r2": 1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2),
        "median_abs_pct_error": 100 * np.median(np.abs(np.exp(p - y) - 1))} for k, p in oof.items()]
m = make_model().fit(X, y)
e = shap.TreeExplainer(m)
sv = e.shap_values(X)
tcols = [c for c in X.columns if c.startswith("town_")]
town_shap = sv[:, [list(X.columns).index(c) for c in tcols]].sum(1)
avg = pd.Series(town_shap).groupby(d["town"].to_numpy()).mean()
rng = np.random.default_rng(SEED)
sub = np.sort(rng.choice(len(X), 2000, replace=False))
iv = e.shap_interaction_values(X.iloc[sub])
ti = [list(X.columns).index(c) for c in tcols]
ia = list(X.columns).index("log_area")
town_area = 2 * iv[:, ti, :][:, :, [ia]].sum((1, 2))
# all feature-level pairs (town and group dummies summed) to rank town x area
feats = {c: [c] for c in X.columns if not c.startswith(("town_", "group_"))}
feats["town"] = tcols
feats["group"] = [c for c in X.columns if c.startswith("group_")]
fidx = {k: [list(X.columns).index(c) for c in v] for k, v in feats.items()}
names = list(feats)
pairs = sorted(((float(np.mean(np.abs(2 * iv[:, fidx[a]][:, :, fidx[b]].sum((1, 2))))), a, b)
                for i, a in enumerate(names) for b in names[i + 1:]), reverse=True)
rank = next(i + 1 for i, (_, a, b) in enumerate(pairs) if {a, b} == {"town", "log_area"})
c3 = pd.DataFrame([{**r, "town": "", "value": np.nan} for r in cvr] +
                  [{"model": "boosting", "cv": "SHAP town contribution vs Cambridge (%)", "town": t,
                    "value": pct(avg[t] - avg["Cambridge"])} for t in TOWNS] +
                  [{"model": "boosting", "cv": f"town x living-area interaction rank (of {len(pairs)} pairs)",
                    "town": "", "value": rank}])
c3.to_csv(RES / "crosstown_c3_boosting.csv", index=False)
print("\n" + c3.round(3).to_string(index=False))
print("top pairs:", [(round(s, 4), a, b) for s, a, b in pairs[:5]])

# ------------------------------------------------------------------ school + tax context
mc = pd.read_csv(RAW / "dese_mcas_district_5towns.csv", dtype={"sy": str})
mc = mc[(mc["stu_grp"] == "All Students") & mc["subject_code"].isin(["ELA", "MATH"])
        & mc["test_grade"].isin(["ALL (03-08)", "10"]) & mc["sy"].astype(int).between(2017, 2026)]
mcas = mc.groupby("dist_name").agg(mcas_meet_exceed=("m_plus_e_pct", "mean"), mcas_avg_sgp=("avg_sgp", "mean"),
                                   mcas_rows=("sy", "size"))
mcas["mcas_meet_exceed"] *= 100                   # DESE gives a share (0-1); report %
sp = pd.read_csv(RAW / "dese_per_pupil_spending_5towns.csv")
sp = sp[sp["sy"].between(2016, 2025)].groupby("dist_name")["in_dist_exp_per_pupil"].mean().rename(
    "spending_per_pupil_2016_2025")
tax = pd.read_csv(RAW / "manual" / "dls_tax_rates_by_class.csv")
tax = tax[tax["fiscal_year"] == 2025].set_index("municipality")["residential"].rename("res_tax_rate_fy2025")
ctx = pd.concat([mcas, sp, tax], axis=1).reindex(TOWNS)
prem = c1[c1["spec"].str.startswith("main")].set_index("town")
ctx["town_premium_pct"] = prem["premium_pct"]
ctx["premium_ci_low"] = prem["ci_low_pct"]
ctx["premium_ci_high"] = prem["ci_high_pct"]
ctx.loc["Cambridge", ["town_premium_pct", "premium_ci_low", "premium_ci_high"]] = 0.0
ctx["boosting_town_pct"] = [pct(avg[t] - avg["Cambridge"]) for t in TOWNS]
ctx.index.name = "town"
ctx.to_csv(RES / "crosstown_school_context.csv")
print("\n" + ctx.round(2).to_string())

# ------------------------------------------------------------------ figures
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10.5,
                     "axes.spines.top": False, "axes.spines.right": False})
BLUE, ORANGE, GREY = "#2a78d6", "#d97a1f", "#52514e"
fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), gridspec_kw={"width_ratios": [1.1, 1]})
ax = axes[0]
xs = np.arange(len(TOWNS))
for off, spec, col in [(-0.15, "main (with tract income)", BLUE), (0.15, "check: without tract income", ORANGE)]:
    dd = c1[c1["spec"] == spec].set_index("town").reindex(TOWNS[1:])
    vals = np.r_[0, dd["premium_pct"]]
    lo = np.r_[0, dd["premium_pct"] - dd["ci_low_pct"]]
    hi = np.r_[0, dd["ci_high_pct"] - dd["premium_pct"]]
    ax.errorbar(xs + off, vals, yerr=[lo, hi], fmt="o", color=col, capsize=4, lw=1.8,
                label="with tract income" if spec.startswith("main") else "without tract income")
ax.axhline(0, color=GREY, lw=0.8)
ax.set_xticks(xs, ["Cambridge\n(reference)"] + TOWNS[1:])
ax.set_ylabel("Price vs a comparable Cambridge home (%)")
ax.set_title("C1: town premium (a bundle: schools, taxes,\nservices, location)", fontsize=10.5)
ax.legend(frameon=False, fontsize=8.5)
ax = axes[1]
dd = c2[c2["variable"] == "log_area"].set_index("town").reindex(TOWNS)
ax.errorbar(xs, dd["slope"], yerr=[dd["slope"] - dd["ci_low"], dd["ci_high"] - dd["slope"]], fmt="o",
            color=BLUE, capsize=4, lw=1.8)
ax.set_xticks(xs, TOWNS)
ax.set_ylabel("Area elasticity: % price per 1% more space")
pv = dd["p"].iloc[0]
ax.set_title("C2: value of space by town\n(joint test " + ("p < 0.001" if pv < 0.001 else f"p = {pv:.3f}") + ")",
             fontsize=10.5)
fig.text(0.01, 0.01, "95% CIs clustered by census tract. MassGIS last-sale data, 2016 onward. "
         "Associations, not causes.", fontsize=7.5, color=GREY)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(FIG / "fig_h15_crosstown_premium.png", dpi=200)
fig.savefig(FIG / "fig_h15_crosstown_premium.pdf")
plt.close(fig)

fig, axes = plt.subplots(1, 4, figsize=(15, 3.8), sharey=True)
for ax, (col, lab) in zip(axes, [("mcas_meet_exceed", "MCAS: % meeting or exceeding"),
                                 ("mcas_avg_sgp", "MCAS: average student growth (SGP)"),
                                 ("spending_per_pupil_2016_2025", "Spending per pupil (\\$)"),
                                 ("res_tax_rate_fy2025", "Residential tax rate FY2025 (\\$/1,000)")]):
    ax.errorbar(ctx[col], ctx["town_premium_pct"],
                yerr=[ctx["town_premium_pct"] - ctx["premium_ci_low"], ctx["premium_ci_high"] - ctx["town_premium_pct"]],
                fmt="o", color=BLUE, capsize=3)
    for t, r in ctx.iterrows():
        ax.annotate(t, (r[col], r["town_premium_pct"]), xytext=(4, 4), textcoords="offset points", fontsize=8)
    ax.set_xlabel(lab, fontsize=9)
    ax.axhline(0, color=GREY, lw=0.6)
axes[0].set_ylabel("Town premium vs Cambridge (%)")
fig.suptitle("Five towns: town premium next to school and tax measures. Not evidence of a school "
             "effect (only 5 points; schools are bundled with everything else about a town).",
             fontsize=10.5)
fig.tight_layout()
fig.savefig(FIG / "fig_h16_crosstown_context.png", dpi=200)
fig.savefig(FIG / "fig_h16_crosstown_context.pdf")
plt.close(fig)
print("\nwrote crosstown_*.csv and fig_h15, fig_h16")
