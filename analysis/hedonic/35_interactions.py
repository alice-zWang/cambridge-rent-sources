"""Step 35: Model 2, interaction terms (as fixed in SPEC_PHASE3.md before this was run).

WHAT THIS DOES (plain words)
  An interaction asks whether one factor's link with price DEPENDS on another factor. Example:
  is being close to the T associated with a bigger price difference in lower-income tracts than
  in higher-income ones? Each interaction is added on its own to Model 1:
    I1 income x transit, I2 bedrooms x transit, I3 violent crime x income,
    I4 living area x after-COVID (and year by year).
  Exploratory (not in PLAN.md): E1 transit x house (vs condo), E2 = E1 without West Cambridge.
  Uncertainty: clustered by tract, plus the wild cluster bootstrap by neighborhood, plus a Holm
  correction because four interactions are tested. All results are ASSOCIATIONS.

OUTPUTS
  results/hedonic/model2_*.csv, figures/hedonic/fig_h7_*, fig_h8_* (PNG + PDF)

RUN
  uv run python analysis/hedonic/35_interactions.py
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from model_common import FIG, HEAD, RES, fit, formula, load, pct  # noqa: E402
from wildboot import WildClusterBootstrap  # noqa: E402

N_BOOT = 9999
POST = pd.Timestamp("2020-04-01")

df_all, df = load()
for v, c in [("log_income", "c_income"), ("transit_km", "c_transit"), ("bedrooms", "c_bed"),
             ("crime_violent_500", "c_violent"), ("crime_property_500", "c_property"),
             ("log_area", "c_area")]:
    df[c] = df[v] - df[v].mean()
df["post"] = (df["saledate"] >= POST).astype(int)
df["house"] = df["group"].isin(["single_family", "two_family", "three_family"]).astype(int)
df["I1_income_x_transit"] = df["c_income"] * df["c_transit"]
df["I2_bedrooms_x_transit"] = df["c_bed"] * df["c_transit"]
df["I3_violent_x_income"] = df["c_violent"] * df["c_income"]
df["I3b_property_x_income"] = df["c_property"] * df["c_income"]
df["I4_area_x_post"] = df["c_area"] * df["post"]
df["E1_transit_x_house"] = df["c_transit"] * df["house"]
years = sorted(df["sale_year"].unique())
for y in years[1:]:
    df[f"area_x_{y}"] = df["c_area"] * (df["sale_year"] == y)

PRE = ["I1_income_x_transit", "I2_bedrooms_x_transit", "I3_violent_x_income", "I4_area_x_post"]
TITLE = {"I1_income_x_transit": "I1 income × transit", "I2_bedrooms_x_transit": "I2 bedrooms × transit",
         "I3_violent_x_income": "I3 violent crime × income",
         "I3b_property_x_income": "I3 check: property crime × income",
         "I4_area_x_post": "I4 living area × after-COVID", "E1_transit_x_house": "E1 transit × house",
         "E2_transit_x_house_noWC": "E2 transit × house, without West Cambridge"}


def one(data, term, extra_terms=None, boot=True):
    terms = extra_terms or [term]
    res = fit(data, formula(extra=" + " + " + ".join(terms)))
    ci = res.conf_int()
    row = {"term": term, "label": TITLE.get(term, term), "n": int(res.nobs), "coef": res.params[term],
           "se_tract": res.bse[term], "ci_low_tract": ci.loc[term, 0], "ci_high_tract": ci.loc[term, 1],
           "p_tract": res.pvalues[term]}
    if boot:
        wb = WildClusterBootstrap(res.model.exog, res.model.endog, data["neighborhood"],
                                  n_boot=N_BOOT, seed=20261122)
        j = res.model.exog_names.index(term)
        lo, hi = wb.ci(j, res.bse[term])
        row.update({"p_wild_bootstrap": wb.pvalue(j), "ci_low_boot": lo, "ci_high_boot": hi})
    for v in HEAD:
        row[f"main_{v}"] = res.params[v]
    return row, res


rows, fits = [], {}
for term in PRE + ["I3b_property_x_income", "E1_transit_x_house"]:
    r, res = one(df, term)
    rows.append(r)
    fits[term] = res
noWC = df[df["neighborhood"] != "West Cambridge"].reset_index(drop=True)
r, res = one(noWC, "E1_transit_x_house")
r["term"], r["label"] = "E2_transit_x_house_noWC", TITLE["E2_transit_x_house_noWC"]
rows.append(r)
fits["E2"] = res
tab = pd.DataFrame(rows)

# Holm correction over the four pre-registered bootstrap p-values
pre = tab[tab["term"].isin(PRE)].sort_values("p_wild_bootstrap")
m = len(pre)
adj, running = [], 0.0
for i, p in enumerate(pre["p_wild_bootstrap"]):
    running = max(running, min(1.0, (m - i) * p))
    adj.append(running)
tab.loc[pre.index, "p_holm"] = adj
tab["status"] = np.where(tab["term"].isin(PRE), "pre-registered",
                         np.where(tab["term"].str.startswith("I3b"), "check", "exploratory"))
tab.to_csv(RES / "model2_interactions.csv", index=False)
cols = ["label", "n", "coef", "se_tract", "p_tract", "p_wild_bootstrap", "p_holm", "ci_low_boot",
        "ci_high_boot"]
print(tab[cols].round(4).to_string(index=False))

# all four together (check)
together = fit(df, formula(extra=" + " + " + ".join(PRE)))
tog = pd.DataFrame({"coef_together": together.params[PRE], "se_tract": together.bse[PRE],
                    "coef_alone": tab.set_index("term").loc[PRE, "coef"]})
tog.to_csv(RES / "model2_all_four_together.csv")
print("\nAll four together vs alone\n" + tog.round(4).to_string())


# ------------------------------------------------------------------ marginal effects
def lincomb(res, weights):
    names = res.params.index
    w = np.array([weights.get(n, 0.0) for n in names])
    est = w @ res.params.to_numpy()
    se = np.sqrt(w @ res.cov_params().to_numpy() @ w)
    return est, est - 1.96 * se, est + 1.96 * se


q = df[["transit_km", "log_income", "bedrooms", "crime_violent_500"]].quantile([0.10, 0.25, 0.50, 0.75, 0.90])
iqr = lambda v: q.loc[0.75, v] - q.loc[0.25, v]  # noqa: E731
SPECS = [  # (interaction, factor whose effect is shown, its main-effect term, moderator, centred moderator)
    ("I1_income_x_transit", "transit_km", "log_income", "c_income"),
    ("I2_bedrooms_x_transit", "transit_km", "bedrooms", "c_bed"),
    ("I3_violent_x_income", "crime_violent_500", "log_income", "c_income"),
]
me_rows = []
for term, x, z, cz in SPECS:
    res = fits[term]
    d = iqr(x)
    for lvl in (0.10, 0.50, 0.90):
        zc = q.loc[lvl, z] - df[z].mean()
        est, lo, hi = lincomb(res, {x: d, term: d * zc})
        me_rows.append({"interaction": term, "effect_of": x, "change": f"p25->p75 ({d:.3f})",
                        "moderator": z, "moderator_level": f"p{int(lvl * 100)}",
                        "moderator_value": q.loc[lvl, z], "pct": pct(est, 1),
                        "pct_ci_low": pct(lo, 1), "pct_ci_high": pct(hi, 1)})
for name, res, sub in [("E1", fits["E1_transit_x_house"], df), ("E2", fits["E2"], noWC)]:
    d = iqr("transit_km")
    for h, lab in [(0, "condo"), (1, "house")]:
        est, lo, hi = lincomb(res, {"transit_km": d, "E1_transit_x_house": d * h})
        me_rows.append({"interaction": name, "effect_of": "transit_km", "change": f"p25->p75 ({d:.3f})",
                        "moderator": "home type", "moderator_level": lab, "moderator_value": h,
                        "pct": pct(est, 1), "pct_ci_low": pct(lo, 1), "pct_ci_high": pct(hi, 1)})
me = pd.DataFrame(me_rows)
me.to_csv(RES / "model2_marginal_effects.csv", index=False)
print("\nMarginal effects (typical low -> high change, 95% CI clustered by tract)\n"
      + me[["interaction", "effect_of", "moderator", "moderator_level", "moderator_value", "pct",
            "pct_ci_low", "pct_ci_high"]].round(3).to_string(index=False))

# living area by year
yr_terms = [f"area_x_{y}" for y in years[1:]]
res_y = fit(df, formula(extra=" + " + " + ".join(yr_terms)))
yr_rows = []
for y in years:
    w = {"log_area": 1.0}
    if y != years[0]:
        w[f"area_x_{y}"] = 1.0
    est, lo, hi = lincomb(res_y, w)
    yr_rows.append({"year": y, "area_elasticity": est, "ci_low": lo, "ci_high": hi,
                    "n_sales": int((df["sale_year"] == y).sum())})
yr = pd.DataFrame(yr_rows)
yr.to_csv(RES / "model2_area_by_year.csv", index=False)
print("\nLiving-area elasticity by year\n" + yr.round(3).to_string(index=False))

# ------------------------------------------------------------------ figures
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10.5,
                     "axes.spines.top": False, "axes.spines.right": False})
BLUE = "#2a78d6"
fig, axes = plt.subplots(1, 4, figsize=(14, 4.2), sharey=True)
panels = [("I1_income_x_transit", "Distance to station\n(514 → 911 m), by tract income",
           lambda v: f"${np.exp(v) / 1000:.0f}k".replace("$", "\\$")),
          ("I2_bedrooms_x_transit", "Distance to station\n(514 → 911 m), by bedrooms",
           lambda v: f"{v:.0f} BR"),
          ("I3_violent_x_income", "Violent crime\n(10 → 36 /km²/yr), by tract income",
           lambda v: f"${np.exp(v) / 1000:.0f}k".replace("$", "\\$")),
          ("E1", "Distance to station (514 → 911 m),\nby home type (exploratory)", lambda v: v)]
for ax, (term, title, fmt) in zip(axes, panels):
    d = me[me["interaction"] == term].reset_index(drop=True)
    xs = np.arange(len(d))
    ax.errorbar(xs, d["pct"], yerr=[d["pct"] - d["pct_ci_low"], d["pct_ci_high"] - d["pct"]],
                fmt="o", color=BLUE, capsize=4, lw=1.8, ms=6)
    ax.axhline(0, color="#52514e", lw=0.8)
    if term == "E1":
        labels = ["Condo", "House"]
    else:
        labels = [f"{lv}\n{fmt(v)}" for lv, v in zip(["low (p10)", "mid (p50)", "high (p90)"],
                                                     d["moderator_value"])]
    ax.set_xticks(xs, labels, fontsize=9)
    ax.set_xlim(-0.5, len(d) - 0.5)
    ax.set_title(title, fontsize=10)
axes[0].set_ylabel("Price difference (%), 95% CI")
fig.suptitle("Model 2: does one factor's price association depend on another?", fontsize=12)
fig.text(0.01, 0.01, "CIs clustered by census tract (31); bootstrap by neighborhood is wider. "
         "Associations, not causes.", fontsize=7.5, color="#52514e")
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(FIG / "fig_h7_interactions.png", dpi=200)
fig.savefig(FIG / "fig_h7_interactions.pdf")
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 4))
ax.fill_between(yr["year"], yr["ci_low"], yr["ci_high"], color=BLUE, alpha=0.18, lw=0)
ax.plot(yr["year"], yr["area_elasticity"], "o-", color=BLUE)
ax.axvline(2020.25, color="#52514e", lw=0.8, ls="--")
ax.text(2020.3, ax.get_ylim()[1], " COVID (Apr 2020)", va="top", fontsize=8.5, color="#52514e")
ax.set_ylabel("% price per 1% more living area")
ax.set_title("I4: value of living area by sale year (95% CI, clustered by tract)", fontsize=11)
fig.tight_layout()
fig.savefig(FIG / "fig_h8_area_by_year.png", dpi=200)
fig.savefig(FIG / "fig_h8_area_by_year.pdf")
plt.close(fig)
print("\nwrote results/hedonic/model2_*.csv and figures fig_h7, fig_h8")
