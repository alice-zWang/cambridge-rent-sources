"""Step 30: Model 1, the hedonic regression, with collinearity checks and robustness table.

WHAT THIS DOES (plain words)
  A hedonic regression treats a home's price as the sum of the values of its parts. It compares
  homes that are alike in size, type, age, condition and neighborhood, sold in the same quarter,
  and asks how price differs with nearby crime, tract income and distance to the T.
  Prices are in logs, so each estimate reads as "about X% higher or lower price".

  Exactly as fixed in SPEC_MODEL1.md (written before this script was run), it:
    1. fits the main model, with standard errors clustered by census tract;
    2. checks collinearity: correlation matrix, variance inflation factors, "drop one" table;
    3. re-checks the uncertainty with a wild cluster bootstrap over the 12 neighborhoods;
    4. carries the Census margin of error of tract income through (200 re-draws);
    5. fits the robustness variants (other samples, other crime and transit measures).
  Every result is an ASSOCIATION, not a cause.

OUTPUTS
  results/hedonic/model1_*.csv, figures/hedonic/fig_h5_*, fig_h6_* (PNG + PDF)

RUN
  uv run python analysis/hedonic/30_hedonic_ols.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import statsmodels.formula.api as smf  # noqa: E402
from statsmodels.stats.outliers_influence import variance_inflation_factor  # noqa: E402

import sys  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from wildboot import WildClusterBootstrap  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed" / "hedonic"
RES = ROOT / "results" / "hedonic"
FIG = ROOT / "figures" / "hedonic"
RNG = np.random.default_rng(20261122)
N_BOOT = 9999
N_MOE = 200

HEAD = ["crime_violent_500", "crime_property_500", "log_income", "transit_km"]
LABEL = {"crime_violent_500": "Violent crime nearby", "crime_property_500": "Property crime nearby",
         "log_income": "Tract median income", "transit_km": "Distance to nearest station"}
CONTROLS = ("C(group, Treatment('condo')) + log_area + bedrooms + fullbaths + halfbaths"
            " + C(age_group, Treatment('1900-1939')) + C(condition, Treatment('Average'))"
            " + C(grade, Treatment('Average')) + parking")
FE = "C(neighborhood) + C(sale_quarter)"


def formula(head=HEAD, extra=""):
    return f"log_price ~ {' + '.join(head)} + {CONTROLS}{extra} + {FE}"


def fit(df, f, cluster="tract"):
    groups = pd.factorize(df[cluster])[0]
    return smf.ols(f, data=df).fit(cov_type="cluster", cov_kwds={"groups": groups})


df_all = pd.read_csv(PROC / "sales_features.csv", parse_dates=["saledate"])
df = df_all[df_all["model_sample"]].reset_index(drop=True)
print(f"model sample: {len(df):,} sales, {df['tract'].nunique()} tracts, "
      f"{df['neighborhood'].nunique()} neighborhoods")

# "typical change" for each headline variable: 25th -> 75th percentile of the model sample
q = df[HEAD].quantile([0.25, 0.75])
DELTA = (q.loc[0.75] - q.loc[0.25]).to_dict()


def pct(b, d):
    return 100 * (np.exp(b * d) - 1)


# ------------------------------------------------------------------ 1. main model
main = fit(df, formula())
ci = main.conf_int()
coef = pd.DataFrame({"coef": main.params, "se_tract": main.bse, "ci_low": ci[0], "ci_high": ci[1],
                     "p_tract": main.pvalues})
coef.to_csv(RES / "model1_coefficients.csv")
rows = []
for v in HEAD:
    d = DELTA[v]
    rows.append({"variable": v, "label": LABEL[v], "p25": q.loc[0.25, v], "p75": q.loc[0.75, v],
                 "coef": main.params[v], "se_tract": main.bse[v], "p_tract": main.pvalues[v],
                 "pct_change_p25_to_p75": pct(main.params[v], d),
                 "pct_ci_low": pct(ci.loc[v, 0], d), "pct_ci_high": pct(ci.loc[v, 1], d)})
head = pd.DataFrame(rows)
print(f"\nMain model: n={int(main.nobs):,}, R2={main.rsquared:.3f}, adj R2={main.rsquared_adj:.3f}")
print(head[["label", "coef", "se_tract", "p_tract", "pct_change_p25_to_p75", "pct_ci_low",
            "pct_ci_high"]].round(4).to_string(index=False))
ctrl = [c for c in main.params.index if c.startswith(("log_area", "bedrooms", "fullbaths", "halfbaths",
                                                      "parking", "C(group"))]
print(coef.loc[ctrl, ["coef", "ci_low", "ci_high"]].round(3).to_string())

# ------------------------------------------------------------------ 2. collinearity
cont = HEAD + ["log_area", "bedrooms", "fullbaths", "parking"]
corr = df[cont].corr()
corr.to_csv(RES / "model1_correlations.csv")


def within(df, cols):
    """Remove neighborhood and quarter fixed effects (the variation Model 1 actually uses)."""
    D = pd.get_dummies(df[["neighborhood", "sale_quarter"]], drop_first=True).astype(float)
    D.insert(0, "const", 1.0)
    Dm = D.to_numpy()
    beta, *_ = np.linalg.lstsq(Dm, df[cols].to_numpy(float), rcond=None)
    return pd.DataFrame(df[cols].to_numpy(float) - Dm @ beta, columns=cols)


W = within(df, cont)
Wc = np.column_stack([np.ones(len(W)), W.to_numpy()])
Rc = np.column_stack([np.ones(len(df)), df[cont].to_numpy(float)])
vif = pd.DataFrame({"variable": cont,
                    "vif_raw": [variance_inflation_factor(Rc, i + 1) for i in range(len(cont))],
                    "vif_within_fe": [variance_inflation_factor(Wc, i + 1) for i in range(len(cont))],
                    "share_of_variance_left_after_fe": (W.var() / df[cont].var()).to_numpy()})
vif.to_csv(RES / "model1_vif.csv", index=False)
print("\nVIF\n" + vif.round(2).to_string(index=False))
print("\nCorrelations (raw)\n" + corr.loc[HEAD, HEAD].round(2).to_string())
print("\nCorrelations within neighborhood and quarter\n" + W[HEAD].corr().round(2).to_string())
W[HEAD].corr().to_csv(RES / "model1_correlations_within_fe.csv")

drop_rows = []
for dropped in [None] + HEAD:
    h = [v for v in HEAD if v != dropped]
    r = fit(df, formula(h))
    row = {"dropped": dropped or "(none)", "r2": r.rsquared}
    for v in HEAD:
        row[v] = r.params.get(v, np.nan)
    drop_rows.append(row)
drop = pd.DataFrame(drop_rows)
drop.to_csv(RES / "model1_drop_one.csv", index=False)
print("\nDrop one (coefficients)\n" + drop.round(4).to_string(index=False))

# ------------------------------------------------------------------ 3. wild cluster bootstrap
# (fast algebra in wildboot.py, checked against brute-force refits by verify_wild_bootstrap.py)
y = main.model.endog
X = main.model.exog
names = main.model.exog_names
wb = WildClusterBootstrap(X, y, df["neighborhood"], n_boot=N_BOOT, seed=20261122)
G = wb.G

boot_rows = []
for v in HEAD:
    j = names.index(v)
    p, t = wb.pvalue(j), wb.t_stat(j)
    lo, hi = wb.ci(j, main.bse[v])
    boot_rows.append({"variable": v, "label": LABEL[v], "coef": main.params[v], "t_neighborhood_cr1": t,
                      "p_wild_bootstrap": p, "ci_low": lo, "ci_high": hi,
                      "pct_ci_low": pct(lo, DELTA[v]), "pct_ci_high": pct(hi, DELTA[v])})
boot = pd.DataFrame(boot_rows)
boot.to_csv(RES / "model1_wild_bootstrap.csv", index=False)
print(f"\nWild cluster bootstrap, {G} neighborhood clusters, {N_BOOT} Webb draws\n"
      + boot.round(4).to_string(index=False))

# diagnostic added after seeing the bootstrap results (not in SPEC_MODEL1.md): leave one
# neighborhood out, to see whether a few neighborhoods drive each estimate
loo = []
for hood in sorted(df["neighborhood"].unique()):
    sub = df[df["neighborhood"] != hood]
    r = fit(sub, formula())
    loo.append({"left_out": hood, "n_left_out": int((df["neighborhood"] == hood).sum()),
                **{v: r.params[v] for v in HEAD}})
loo = pd.DataFrame(loo)
loo.to_csv(RES / "model1_leave_one_neighborhood_out.csv", index=False)
print("\nLeave one neighborhood out (diagnostic)\n" + loo.round(4).to_string(index=False))

# ------------------------------------------------------------------ 4. income margin of error
tr = df.groupby("tract")[["income", "income_moe"]].first()
j_inc = names.index("log_income")
heads_idx = [names.index(v) for v in HEAD]
draws = []
X_moe = X.copy()
tract_pos = df["tract"].map({t: i for i, t in enumerate(tr.index)}).to_numpy()
for _ in range(N_MOE):
    inc = RNG.normal(tr["income"], tr["income_moe"] / 1.645).clip(min=10000)
    X_moe[:, j_inc] = np.log(np.asarray(inc)[tract_pos])
    b, *_ = np.linalg.lstsq(X_moe, y, rcond=None)
    draws.append(b[heads_idx])
draws = pd.DataFrame(draws, columns=HEAD)
moe = pd.DataFrame({"main_coef": main.params[HEAD], "mean_over_draws": draws.mean(),
                    "sd_over_draws": draws.std(), "p2.5": draws.quantile(0.025),
                    "p97.5": draws.quantile(0.975)})
moe.to_csv(RES / "model1_income_moe.csv")
print(f"\nIncome margin of error, {N_MOE} re-draws\n" + moe.round(4).to_string())

# ------------------------------------------------------------------ 5. robustness
rob = []


def add(name, res, mapping=None, note=""):
    mapping = mapping or {}
    row = {"spec": name, "n": int(res.nobs), "r2": res.rsquared, "note": note}
    for v in HEAD:
        key = mapping.get(v, v)
        if key in res.params:
            row[v] = res.params[key]
            row[v + "_se"] = res.bse[key]
    rob.append(row)


add("1 main", main)
rs = df_all[df_all["robust_sample"]].reset_index(drop=True)
add("2 include flagged sales", fit(rs, formula()), note="multi-parcel and low-ratio sales added")
add("3 drop extreme price/sqft", fit(df[~df["flag_ppsf_extreme"]], formula()))
r = fit(df, formula([v for v in HEAD if v != "transit_km"]
                    + ["C(transit_band, Treatment('<400m'))"]))
rci = r.conf_int()
band_txt = []
for b in ["400-800m", "800-1200m", ">1200m"]:
    t = f"C(transit_band, Treatment('<400m'))[T.{b}]"
    band_txt.append(f"{b} {pct(r.params[t], 1):+.1f}% [{pct(rci.loc[t, 0], 1):+.1f}, "
                    f"{pct(rci.loc[t, 1], 1):+.1f}]")
add("4 transit bands", r, note="vs <400 m (95% CI, tract clusters): " + "; ".join(band_txt))
add("5 all stations (both river sides)",
    fit(df, formula([v if v != "transit_km" else "transit_km_allstations" for v in HEAD])),
    {"transit_km": "transit_km_allstations"})
for rad in (300, 800):
    hv = [v.replace("_500", f"_{rad}") for v in HEAD]
    add(f"{6 if rad == 300 else 7} crime radius {rad} m", fit(df, formula(hv)),
        {v: v.replace("_500", f"_{rad}") for v in HEAD[:2]})
hv = [v.replace("_500", "_500_nosq") if v.startswith("crime") else v for v in HEAD]
add("8 crime without commercial squares", fit(df, formula(hv)),
    {v: v + "_nosq" for v in HEAD[:2]})
condo = df[df["group"].isin(["condo", "condo_lux"])].copy()
condo["floor_c"] = condo["floor"].clip(upper=10).fillna(condo["floor"].median())
condo["floor_missing"] = condo["floor"].isna().astype(int)
condo["view"] = condo["exterior_view"].fillna("Average").replace({"Fair": "Below", "Poor": "Below",
                                                                   "Very Good": "Good+",
                                                                   "Excellent": "Good+",
                                                                   "Good": "Good+"})
condo["laundry"] = condo["interior_laundryinunit"].astype(str).eq("True").astype(int)
add("9a condos only", fit(condo, formula(extra=" + floor_c + floor_missing + C(view, Treatment('Average'))"
                                              " + laundry")))
fam = df[df["group"].isin(["single_family", "two_family", "three_family"])].copy()
fam = fam[fam["log_land"].notna()]
add("9b 1-3 family only", fit(fam, formula(extra=" + log_land").replace("Treatment('condo')",
                                                                        "Treatment('single_family')")))
rob = pd.DataFrame(rob)
rob.to_csv(RES / "model1_robustness.csv", index=False)
show = rob[["spec", "n"] + HEAD].copy()
print("\nRobustness (coefficients)\n" + show.round(4).to_string(index=False))
print(rob.loc[rob["note"] != "", ["spec", "note"]].to_string(index=False))
head.to_csv(RES / "model1_headline.csv", index=False)

# ------------------------------------------------------------------ figures
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "axes.spines.top": False, "axes.spines.right": False})
BLUE, ORANGE = "#2a78d6", "#eb6834"
fig, ax = plt.subplots(figsize=(9, 4.6))
ypos = np.arange(len(HEAD))[::-1]
for i, v in enumerate(HEAD):
    h = head.iloc[i]
    b = boot.iloc[i]
    ax.plot([h.pct_ci_low, h.pct_ci_high], [ypos[i] + 0.12] * 2, color=BLUE, lw=2.2)
    ax.plot([b.pct_ci_low, b.pct_ci_high], [ypos[i] - 0.12] * 2, color=ORANGE, lw=2.2)
    ax.plot(h.pct_change_p25_to_p75, ypos[i] + 0.12, "o", color=BLUE, ms=6)
    ax.plot(h.pct_change_p25_to_p75, ypos[i] - 0.12, "o", color=ORANGE, ms=6)
ax.axvline(0, color="#52514e", lw=0.8)
units = {"crime_violent_500": lambda a: f"{100 * a:.0f}/km²/yr",
         "crime_property_500": lambda a: f"{100 * a:.0f}/km²/yr",
         "log_income": lambda a: f"\\${np.exp(a) / 1000:.0f}k", "transit_km": lambda a: f"{1000 * a:.0f} m"}
ax.set_yticks(ypos, [f"{LABEL[v]}\n{units[v](q.loc[0.25, v])} → {units[v](q.loc[0.75, v])}"
                     for v in HEAD], fontsize=9.5)
ax.set_xlabel("Difference in sale price (%), typical low → typical high value (25th → 75th percentile)")
ax.set_title("Model 1: price differences for similar homes in the same neighborhood", fontsize=11.5,
             pad=30)
ax.plot([], [], color=BLUE, lw=2.2, marker="o", label="95% CI, clustered by tract (31)")
ax.plot([], [], color=ORANGE, lw=2.2, marker="o", label="95% CI, wild bootstrap by neighborhood (12)")
ax.legend(frameon=False, fontsize=8.5, ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.0))
fig.text(0.01, 0.01, "Crime: reports per km² per year within 500 m, 3 years before sale. Associations, "
         "not causes.", fontsize=7.5, color="#52514e")
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(FIG / "fig_h5_model1_effects.png", dpi=200)
fig.savefig(FIG / "fig_h5_model1_effects.pdf")
plt.close(fig)

lab = {**LABEL, "log_area": "Living area (log)", "bedrooms": "Bedrooms", "fullbaths": "Full baths",
       "parking": "Parking spaces"}
fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
for ax, (m, title) in zip(axes, [(corr, "Raw"), (W.corr(), "Within neighborhood and quarter")]):
    im = ax.imshow(m.to_numpy(), vmin=-1, vmax=1, cmap="RdBu_r")
    ax.set_xticks(range(len(cont)), [lab[c] for c in cont], rotation=60, ha="right", fontsize=8)
    ax.set_yticks(range(len(cont)), [lab[c] for c in cont], fontsize=8)
    for a in range(len(cont)):
        for b in range(len(cont)):
            ax.text(b, a, f"{m.iat[a, b]:.2f}", ha="center", va="center", fontsize=6.5,
                    color="white" if abs(m.iat[a, b]) > 0.6 else "black")
    ax.set_title(f"{title} correlations", fontsize=10.5)
fig.colorbar(im, ax=axes, shrink=0.8)
fig.savefig(FIG / "fig_h6_model1_correlations.png", dpi=200, bbox_inches="tight")
fig.savefig(FIG / "fig_h6_model1_correlations.pdf", bbox_inches="tight")
plt.close(fig)
print("\nwrote results/hedonic/model1_*.csv and figures fig_h5, fig_h6")
