"""Step 50: Model 4, gradient boosting with spatial cross-validation and SHAP (Cambridge).

WHAT THIS DOES (plain words)
  A flexible machine-learning model (gradient boosting: many small decision trees, each fixing
  the errors of the ones before) predicts log price from the same information as Model 1. It is
  allowed to find curves and interactions on its own. Then:
    1. ACCURACY, tested honestly: the model is trained without one neighborhood and tested on
       that neighborhood (spatial cross-validation), and compared with a linear regression on
       the same folds.
    2. SHAP: each prediction is split into contributions from each factor. Averaging them shows
       which factors the model relies on; plotting them shows the shape of each relationship.
    3. "Typical change" numbers comparable to Model 1 (partial-dependence contrasts), with
       ranges from 30 refits on neighborhood-bootstrap samples.
    4. SHAP interaction values for the four planned Model 2 pairs.
  All results describe what the model learned: associations, not causes. Pre-specified in
  SPEC_PHASE4.md.

OUTPUTS
  results/hedonic/model4_cv.csv, model4_importance.csv, model4_pd_contrasts.csv,
  model4_interactions.csv; figures/hedonic/fig_h11 to fig_h14 (PNG + PDF)

RUN
  uv run python analysis/hedonic/50_boosting_shap.py      (about 10-20 minutes)
"""
import sys
import time
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
import patsy
import shap

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from sklearn.model_selection import GroupKFold, KFold, LeaveOneGroupOut  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from boost_common import (HEAD, NICE, binned_curve, build_X, feature_interactions,  # noqa: E402
                          feature_shap, make_model, pct, pd_contrast)
from model_common import CONTROLS, FIG, RES, formula, load  # noqa: E402

SEED = 20261122
N_REFIT = 30
T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:6.0f}s] {msg}", flush=True)


df_all, df = load("market_sample")
_, m1 = load("model_sample")
q = m1[HEAD].quantile([0.25, 0.75])                      # same "typical change" as Model 1
P = gpd.GeoSeries(gpd.points_from_xy(df.longitude, df.latitude), crs=4326).to_crs(26986)
xy = np.column_stack([P.x, P.y])
y = df["log_price"].to_numpy()
Xs = {v: build_X(df, v, xy) for v in ["G1", "G2", "G3"]}
log(f"sample {len(df):,}; features G1 {Xs['G1'][0].shape[1]}, G2 {Xs['G2'][0].shape[1]}, "
    f"G3 {Xs['G3'][0].shape[1]}")

# ------------------------------------------------------------------ 1. cross-validation
OLS_F = {"G1": f"log_price ~ {' + '.join(HEAD)} + {CONTROLS} + C(sale_quarter)",
         "G2": formula(),                                  # Model 1 itself
         "G3": f"log_price ~ {' + '.join(HEAD)} + {CONTROLS} + C(sale_quarter) + x + y"}
dfx = df.assign(x=xy[:, 0], y=xy[:, 1])
SPLITS = {"G1": ("leave one neighborhood out", LeaveOneGroupOut(), df["neighborhood"]),
          "G2": ("tracts held out (10 folds)", GroupKFold(n_splits=10), df["tract"]),
          "G3": ("leave one neighborhood out", LeaveOneGroupOut(), df["neighborhood"])}
rows = []
for v in ["G1", "G2", "G3"]:
    X = Xs[v][0]
    _, D = patsy.dmatrices(OLS_F[v], dfx, return_type="matrix")   # full-data design: all levels
    D = np.asarray(D)
    name, splitter, grp = SPLITS[v]
    for cv_name, folds in [(name, list(splitter.split(X, y, grp))),
                           ("random 10-fold", list(KFold(10, shuffle=True, random_state=SEED).split(X)))]:
        oof = {"boosting": np.zeros(len(y)), "OLS": np.zeros(len(y))}
        for k, (tr, te) in enumerate(folds):
            gb = make_model().fit(X.iloc[tr], y[tr])
            beta = np.linalg.lstsq(D[tr], y[tr], rcond=None)[0]
            for mname, pred in [("boosting", gb.predict(X.iloc[te])), ("OLS", D[te] @ beta)]:
                oof[mname][te] = pred
                rows.append({"version": v, "cv": cv_name, "model": mname, "fold": k,
                             "n_test": len(te), "rmse": np.sqrt(np.mean((y[te] - pred) ** 2)),
                             "r2": 1 - np.sum((y[te] - pred) ** 2) / np.sum((y[te] - y[te].mean()) ** 2)})
        for mname, pred in oof.items():
            rows.append({"version": v, "cv": cv_name, "model": mname, "fold": "pooled", "n_test": len(y),
                         "rmse": np.sqrt(np.mean((y - pred) ** 2)),
                         "r2": 1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2),
                         "median_abs_pct_error": 100 * np.median(np.abs(np.exp(pred - y) - 1))})
        log(f"CV {v} / {cv_name} done")
cv = pd.DataFrame(rows)
cv.to_csv(RES / "model4_cv.csv", index=False)
pooled = cv[cv["fold"] == "pooled"].copy()
spread = (cv[cv["fold"] != "pooled"].groupby(["version", "cv", "model"])["r2"]
          .agg(r2_fold_min="min", r2_fold_max="max").reset_index())
pooled = pooled.merge(spread, on=["version", "cv", "model"])
print(pooled[["version", "cv", "model", "rmse", "r2", "median_abs_pct_error", "r2_fold_min",
              "r2_fold_max"]].round(3).to_string(index=False))


# ------------------------------------------------------------------ 2-3. full fits, SHAP, contrasts
def contrasts(model, X):
    out = {v: pd_contrast(model, X, v, q.loc[0.25, v], q.loc[0.75, v]) for v in HEAD}
    shifted = X.copy()
    shifted["log_area"] += np.log(1.1)                          # 10% more living area
    out["log_area (+10%)"] = float(np.mean(model.predict(shifted)) - np.mean(model.predict(X)))
    return out


rng = np.random.default_rng(SEED)
sub_idx = np.sort(rng.choice(len(df), 2000, replace=False))     # fixed SHAP subsample
CURVE_FEATS = HEAD + ["log_area", "sale_time"]
nb = df["neighborhood"].to_numpy()
hoods = np.unique(nb)
full, imp_rows, pdc_rows, curves, top5 = {}, [], [], {}, {}
for v in ["G1", "G2"]:
    X, groups = Xs[v]
    m = make_model().fit(X, y)
    e = shap.TreeExplainer(m)
    fs = feature_shap(e.shap_values(X), X, groups)
    full[v] = (m, e, fs)
    imp = fs.abs().mean().sort_values(ascending=False)
    edges = {f: np.unique(np.nanquantile(X[f], np.linspace(0, 1, 11))) for f in CURVE_FEATS}
    curves[v] = {"edges": edges, "full": {f: binned_curve(X[f].to_numpy(), fs[f].to_numpy(), edges[f])
                                         for f in CURVE_FEATS}, "boot": {f: [] for f in CURVE_FEATS}}
    base = contrasts(m, X)
    log(f"{v} full fit: {m.n_iter_} trees; SHAP done")
    boot_c, ranks = [], []
    Xsub = X.iloc[sub_idx]
    for r in range(N_REFIT):
        draw = rng.choice(hoods, len(hoods), replace=True)
        idx = np.concatenate([np.flatnonzero(nb == h) for h in draw])
        mb = make_model(seed=r + 1).fit(X.iloc[idx], y[idx])
        boot_c.append(contrasts(mb, X))
        fsb = feature_shap(shap.TreeExplainer(mb).shap_values(Xsub), Xsub, groups)
        ranks.append(fsb.abs().mean().rank(ascending=False))
        for f in CURVE_FEATS:
            curves[v]["boot"][f].append(binned_curve(Xsub[f].to_numpy(), fsb[f].to_numpy(),
                                                     edges[f]))
    log(f"{v}: {N_REFIT} neighborhood-bootstrap refits done")
    bc = pd.DataFrame(boot_c)
    rk = pd.DataFrame(ranks)
    for f, val in imp.items():
        imp_rows.append({"version": v, "feature": f, "label": NICE[f], "mean_abs_shap": val,
                         "share_top5_refits": float((rk[f] <= 5).mean())})
    for k, val in base.items():
        pdc_rows.append({"version": v, "variable": k, "pct": pct(val),
                         "pct_boot_low": pct(np.percentile(bc[k], 2.5)),
                         "pct_boot_high": pct(np.percentile(bc[k], 97.5))})
imp = pd.DataFrame(imp_rows)
imp.to_csv(RES / "model4_importance.csv", index=False)
pdc = pd.DataFrame(pdc_rows)
ref = pd.read_csv(RES / "check_restricted_model1.csv")
ref = ref[ref["sample"].str.startswith("without")].set_index("variable")
pdc["model1_same_sample_pct"] = pdc["variable"].map(ref["pct_typical"])
pdc["model1_same_sample_boot_ci"] = pdc["variable"].map(ref["pct_ci_boot"])
pdc.to_csv(RES / "model4_pd_contrasts.csv", index=False)
print("\n" + imp.round(4).to_string(index=False))
print("\n" + pdc.round(2).to_string(index=False))

# ------------------------------------------------------------------ 4. interactions
PLANNED = {("log_income", "transit_km"): "I1 income × transit",
           ("bedrooms", "transit_km"): "I2 bedrooms × transit",
           ("crime_violent_500", "log_income"): "I3 violent crime × income",
           ("log_area", "sale_time"): "I4 living area × time"}
M2 = pd.read_csv(RES / "check_restricted_model2.csv")
M2 = M2[M2["sample"].str.startswith("without")].set_index("term")["coef"]
M2_TERM = {"I1 income × transit": "I1_income_x_transit", "I2 bedrooms × transit": "I2_bedrooms_x_transit",
           "I3 violent crime × income": "I3_violent_x_income", "I4 living area × time": "I4_area_x_post"}
int_rows, int_store = [], {}
for v in ["G1", "G2"]:
    m, e, _ = full[v]
    X, groups = Xs[v]
    Xsub = X.iloc[sub_idx]
    fi, names = feature_interactions(e.shap_interaction_values(Xsub), Xsub, groups)
    int_store[v] = (fi, names)
    pair_rows = []
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            pair_rows.append((names[a], names[b], float(np.mean(np.abs(2 * fi[:, a, b])))))
    pr = pd.DataFrame(pair_rows, columns=["a", "b", "strength"]).sort_values("strength", ascending=False)
    pr["rank"] = np.arange(1, len(pr) + 1)
    for _, r in pr.iterrows():
        key = (r["a"], r["b"]) if (r["a"], r["b"]) in PLANNED else (r["b"], r["a"])
        label = PLANNED.get(key, "")
        direction = np.nan
        if label:
            ia, ib = names.index(key[0]), names.index(key[1])
            va, vb = Xsub[key[0]].to_numpy(), Xsub[key[1]].to_numpy()
            ok = ~np.isnan(va) & ~np.isnan(vb)
            direction = np.corrcoef(2 * fi[ok, ia, ib], (va[ok] - va[ok].mean()) * (vb[ok] - vb[ok].mean()))[0, 1]
        int_rows.append({"version": v, "rank": r["rank"], "of_pairs": len(pr), "a": r["a"], "b": r["b"],
                         "mean_abs_interaction": r["strength"], "planned": label,
                         "direction_corr": direction,
                         "model2_coef_same_sample": M2.get(M2_TERM.get(label, ""), np.nan)})
    log(f"{v} interactions done")
ints = pd.DataFrame(int_rows)
ints.to_csv(RES / "model4_interactions.csv", index=False)
print("\n" + ints[(ints["rank"] <= 8) | (ints["planned"] != "")].round(4).to_string(index=False))

# ------------------------------------------------------------------ figures
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10.5,
                     "axes.spines.top": False, "axes.spines.right": False})
BLUE, ORANGE, GREY = "#2a78d6", "#d97a1f", "#52514e"


def save(fig, name):
    fig.savefig(FIG / f"{name}.png", dpi=200)
    fig.savefig(FIG / f"{name}.pdf")
    plt.close(fig)


# fig_h11: accuracy
fig, ax = plt.subplots(figsize=(10, 4.4))
lab = {"G1": "G1: no location", "G2": "G2: + neighborhood", "G3": "G3: + coordinates"}
CVS = {"leave one neighborhood out": "neighborhood held out", "tracts held out (10 folds)": "tracts held out",
       "random 10-fold": "random folds"}
order = [(v, c) for v in ["G1", "G2", "G3"] for c in [SPLITS[v][0], "random 10-fold"]]
xs = np.arange(len(order))
for off, mname, col in [(-0.18, "boosting", BLUE), (0.18, "OLS", ORANGE)]:
    vals = [pooled[(pooled.version == v) & (pooled.cv == c) & (pooled.model == mname)].iloc[0]
            for v, c in order]
    ax.bar(xs + off, [r["r2"] for r in vals], 0.34, color=col,
           label="Gradient boosting" if mname == "boosting" else "Linear regression (OLS)")
    for x, r in zip(xs + off, vals):
        ax.text(x, r["r2"] + 0.01, f"{r['r2']:.2f}", ha="center", fontsize=8)
ax.set_xticks(xs, [f"{lab[v]}\n{CVS[c]}" for v, c in order], fontsize=8.5)
ax.set_ylabel("Share of price variation predicted\nin held-out data (R²)")
ax.set_ylim(0, 1)
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.13), ncol=2)
fig.text(0.01, 0.01, "Spatial folds test on areas the model never saw; random folds are more "
         "optimistic. G2 benchmark = Model 1.", fontsize=7.5, color=GREY)
fig.tight_layout(rect=(0, 0.03, 1, 1))
save(fig, "fig_h11_cv_accuracy")

# fig_h12: importance
fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharex=True)
for ax, v, title in zip(axes, ["G1", "G2"], ["G1: no location IDs", "G2: + neighborhood (like Model 1)"]):
    d = imp[imp.version == v].sort_values("mean_abs_shap")
    cols = [ORANGE if f in HEAD else BLUE for f in d.feature]
    ax.barh(d["label"], 100 * d["mean_abs_shap"], color=cols)
    ax.set_title(title, fontsize=10.5)
    ax.set_xlabel("Average size of contribution\n(≈ % of price, mean |SHAP|)")
axes[0].text(0.98, 0.02, "orange = the four headline factors", transform=axes[0].transAxes,
             ha="right", fontsize=8, color=ORANGE)
fig.suptitle("Model 4: which factors the boosting model relies on", fontsize=12)
fig.tight_layout()
save(fig, "fig_h12_shap_importance")

# fig_h13: dependence curves with bootstrap bands (G2), G1 dashed
fig, axes = plt.subplots(2, 3, figsize=(13, 7.2))
XL = {"crime_violent_500": "Violent crime (per 100 /km²/yr)",
      "crime_property_500": "Property crime (per 100 /km²/yr)",
      "log_income": "Tract median income", "transit_km": "Distance to station (km)",
      "log_area": "Living area (sq ft)", "sale_time": "Sale date"}
for ax, f in zip(axes.ravel(), CURVE_FEATS):
    for v, col, ls in [("G2", BLUE, "-"), ("G1", GREY, "--")]:
        ed = curves[v]["edges"][f]
        mid = (ed[:-1] + ed[1:]) / 2
        c0 = curves[v]["full"][f]
        ax.plot(mid, pct(c0), ls, color=col, marker="o", ms=3.5,
                label="G2 (+ neighborhood)" if v == "G2" else "G1 (no location IDs)")
        if v == "G2":
            B = np.array(curves[v]["boot"][f])
            ax.fill_between(mid, pct(np.nanpercentile(B, 2.5, 0)), pct(np.nanpercentile(B, 97.5, 0)),
                            color=col, alpha=0.18, lw=0)
    ax.axhline(0, color=GREY, lw=0.7)
    ax.set_xlabel(XL[f], fontsize=9)
    if f == "log_income":
        ax.set_xticks(ax.get_xticks(), [f"\\${np.exp(t) / 1000:.0f}k" for t in ax.get_xticks()])
    if f == "log_area":
        ax.set_xticks(ax.get_xticks(), [f"{np.exp(t):,.0f}" for t in ax.get_xticks()])
axes[0, 0].set_ylabel("Contribution to price (%)")
axes[1, 0].set_ylabel("Contribution to price (%)")
axes[0, 0].legend(frameon=False, fontsize=8)
fig.suptitle("Model 4: shape of each relationship (SHAP, averaged within 10 bins)", fontsize=12)
fig.text(0.01, 0.01, "Band: 95% range over 30 refits on neighborhood-bootstrap samples (G2). "
         "Contributions are relative to the average home. Associations, not causes.",
         fontsize=7.5, color=GREY)
fig.tight_layout(rect=(0, 0.03, 1, 1))
save(fig, "fig_h13_shap_dependence")

# fig_h14: planned interactions (G2)
fi, names = int_store["G2"]
Xsub = Xs["G2"][0].iloc[sub_idx]
fig, axes = plt.subplots(1, 4, figsize=(15, 4.2))
for ax, ((a, b), label) in zip(axes, PLANNED.items()):
    ia, ib = names.index(a), names.index(b)
    sc = ax.scatter(Xsub[a], 100 * 2 * fi[:, ia, ib], c=Xsub[b], cmap="viridis", s=6, alpha=0.7)
    cb = fig.colorbar(sc, ax=ax, pad=0.01)
    cb.set_label(NICE[b], fontsize=8)
    ax.axhline(0, color=GREY, lw=0.7)
    rk = ints[(ints.version == "G2") & (ints.planned == label)].iloc[0]
    ax.set_title(f"{label}\nrank {int(rk['rank'])} of {int(rk['of_pairs'])} pairs", fontsize=9.5)
    ax.set_xlabel(NICE[a], fontsize=9)
axes[0].set_ylabel("Interaction contribution (≈ % of price)")
fig.suptitle("Model 4: SHAP interaction values for the four planned Model 2 pairs (G2)", fontsize=12)
fig.text(0.01, 0.01, "Random subsample of 2,000 sales. Values near 0 = the pair adds little "
         "beyond each factor on its own.", fontsize=7.5, color=GREY)
fig.tight_layout(rect=(0, 0.03, 1, 1))
save(fig, "fig_h14_shap_interactions")
log("wrote model4_*.csv and fig_h11-fig_h14")
