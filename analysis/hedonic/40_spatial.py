"""Step 40: Model 3, spatial autocorrelation check and spatial model (SPEC_PHASE3.md).

WHAT THIS DOES (plain words)
  If Model 1's leftover errors (residuals) are similar for homes close to each other, something
  local is missing from the model and its uncertainty is understated. Moran's I measures this:
  0 = no pattern, positive = similar residuals sit next to each other.
    1. Moran's I of Model 1 residuals, each sale's 8 nearest other sales as neighbours
       (checked with 5 and 15), with a permutation test.
    2. Separates a "same building" effect (condo units share coordinates) from clustering
       between buildings: share of residual variance between locations, and Moran's I of
       residuals averaged per location.
    3. If clearly positive: Lagrange-multiplier tests pick a spatial error and/or spatial lag
       model, estimated with GMM (robust to heteroskedasticity), and compared with Model 1.
  All results are ASSOCIATIONS.

OUTPUTS
  results/hedonic/model3_*.csv, figures/hedonic/fig_h9_*, fig_h10_* (PNG + PDF)

RUN
  uv run python analysis/hedonic/40_spatial.py
"""
import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from esda.moran import Moran  # noqa: E402
from libpysal.weights import KNN  # noqa: E402
import spreg  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from model_common import FIG, HEAD, LABEL, RES, ROOT, fit, formula, load  # noqa: E402
from wildboot import WildClusterBootstrap  # noqa: E402

warnings.filterwarnings("ignore", category=FutureWarning)
PERM = 999
SEED = 20261122

df_all, df = load()
m1 = fit(df, formula())
df["resid"] = m1.resid.to_numpy()
pts = gpd.GeoSeries(gpd.points_from_xy(df.longitude, df.latitude), crs=4326).to_crs(26986)
xy = np.column_stack([pts.x, pts.y])

# ------------------------------------------------------------------ 1. Moran's I, all sales
rows = []
W = {}
components = {}
for k in (5, 8, 15):
    w = KNN.from_array(xy, k=k, silence_warnings=True)
    components[("sales", k)] = w.n_components
    w.transform = "r"
    W[k] = w
    np.random.seed(SEED)
    mi = Moran(df["resid"].to_numpy(), w, permutations=PERM)
    rows.append({"level": "sales", "k": k, "n": len(df), "moran_I": mi.I, "expected_I": mi.EI,
                 "z_perm": mi.z_sim, "p_perm": mi.p_sim, "weight_components": w.n_components})

# ------------------------------------------------------------------ 2. building vs between
df["loc"] = df.groupby([df.latitude.round(7), df.longitude.round(7)]).ngroup()
loc = df.groupby("loc").agg(resid=("resid", "mean"), n=("resid", "size"), lat=("latitude", "first"),
                            lon=("longitude", "first"))
ss_tot = ((df["resid"] - df["resid"].mean()) ** 2).sum()
ss_within = ((df["resid"] - df.groupby("loc")["resid"].transform("mean")) ** 2).sum()
share_between = 1 - ss_within / ss_tot
multi = df["loc"].map(loc["n"]) > 1
lpts = gpd.GeoSeries(gpd.points_from_xy(loc.lon, loc.lat), crs=4326).to_crs(26986)
lxy = np.column_stack([lpts.x, lpts.y])
for k in (5, 8, 15):
    wl = KNN.from_array(lxy, k=k, silence_warnings=True)
    wl.transform = "r"
    np.random.seed(SEED)
    mi = Moran(loc["resid"].to_numpy(), wl, permutations=PERM)
    rows.append({"level": "locations (residuals averaged per point)", "k": k, "n": len(loc),
                 "moran_I": mi.I, "expected_I": mi.EI, "z_perm": mi.z_sim, "p_perm": mi.p_sim,
                 "weight_components": wl.n_components})
moran = pd.DataFrame(rows)
moran.to_csv(RES / "model3_moran.csv", index=False)
print(moran.round(4).to_string(index=False))
print(f"\nDistinct locations: {len(loc):,}; sales at a shared location: {int(multi.sum()):,}; "
      f"share of residual variance BETWEEN locations: {share_between:.3f}")

# ------------------------------------------------------------------ 3. LM tests, spatial models
X = m1.model.exog
names = m1.model.exog_names
keep = [i for i, n in enumerate(names) if n != "Intercept"]
Xs, xnames = X[:, keep], [names[i] for i in keep]
y = m1.model.endog.reshape(-1, 1)
w8 = W[8]
main_moran = moran.query("level == 'sales' and k == 8").iloc[0]
decision = {"moran_I_k8": main_moran["moran_I"], "moran_p_k8": main_moran["p_perm"]}
comp = {"Model 1 (OLS)": {v: m1.params[v] for v in HEAD}}
comp_se = {"Model 1 (OLS)": {v: m1.bse[v] for v in HEAD}}
extra_rows = [{"model": "Model 1 (OLS)", "spatial_param": np.nan, "spatial_param_se": np.nan,
               "residual_moran_I_k8": main_moran["moran_I"], "note": "SE clustered by tract"}]

if main_moran["moran_I"] > 0 and main_moran["p_perm"] < 0.01:
    ols = spreg.OLS(y, Xs, w=w8, spat_diag=True, moran=True, name_x=xnames, name_y="log_price")
    lm = {"LM_error": ols.lm_error, "LM_lag": ols.lm_lag, "robust_LM_error": ols.rlm_error,
          "robust_LM_lag": ols.rlm_lag, "LM_SARMA": ols.lm_sarma}
    lm_tab = pd.DataFrame([{"test": t, "statistic": v[0], "p": v[1]} for t, v in lm.items()])
    lm_tab.to_csv(RES / "model3_lm_tests.csv", index=False)
    print("\nLagrange-multiplier tests (k = 8)\n" + lm_tab.round(4).to_string(index=False))
    r_err = ols.rlm_error[1] < 0.01
    r_lag = ols.rlm_lag[1] < 0.01
    decision.update({"robust_LM_error_sig": r_err, "robust_LM_lag_sig": r_lag})
    fit_err = r_err or (not r_err and not r_lag)   # fall back to error model if neither robust test
    fit_lag = r_lag
    decision["models_fitted"] = ", ".join(n for n, f in [("error", fit_err), ("lag", fit_lag),
                                                        ("combo", fit_err and fit_lag)] if f)
    ix = {v: xnames.index(v) + 1 for v in HEAD}   # +1: spreg adds the constant first

    def resid_moran(u):
        np.random.seed(SEED)
        return Moran(np.asarray(u).ravel(), w8, permutations=PERM).I

    if fit_err:
        err = spreg.GM_Error_Het(y, Xs, w=w8, name_x=xnames, name_y="log_price")
        comp["Spatial error (GMM)"] = {v: err.betas[ix[v], 0] for v in HEAD}
        comp_se["Spatial error (GMM)"] = {v: err.std_err[ix[v]] for v in HEAD}
        lam = err.betas[-1, 0]
        extra_rows.append({"model": "Spatial error (GMM)", "spatial_param": lam,
                           "spatial_param_se": err.std_err[-1],
                           "residual_moran_I_k8": resid_moran(err.e_filtered),
                           "note": "lambda = spatial error parameter; het-robust SE"})
        # Added after seeing results (not in SPEC_PHASE3.md): spreg's standard errors are not
        # clustered, so they ignore correlation across a whole tract or neighborhood. Re-estimate
        # the error model as "spatially filtered" OLS (y - lambda*Wy on X - lambda*WX, which gives
        # the same coefficients idea as the GMM error model) and use Model 1's uncertainty methods.
        Wsp = w8.sparse
        yf = y.ravel() - lam * (Wsp @ y.ravel())
        Xf = X - lam * (Wsp @ X)
        import statsmodels.api as sm
        filt = sm.OLS(yf, Xf).fit(cov_type="cluster",
                                  cov_kwds={"groups": pd.factorize(df["tract"])[0]})
        wbf = WildClusterBootstrap(Xf, yf, df["neighborhood"], n_boot=9999, seed=SEED)
        frows = []
        for v in HEAD:
            j = names.index(v)
            lo, hi = wbf.ci(j, filt.bse[j])
            frows.append({"variable": v, "coef": filt.params[j], "se_tract": filt.bse[j],
                          "p_tract": filt.pvalues[j], "p_wild_bootstrap": wbf.pvalue(j),
                          "ci_low_boot": lo, "ci_high_boot": hi})
        filt_tab = pd.DataFrame(frows)
        filt_tab.to_csv(RES / "model3_filtered_clustered.csv", index=False)
        print(f"\nSpatially filtered OLS (lambda = {lam:.3f}), clustered inference\n"
              + filt_tab.round(4).to_string(index=False))
        comp["Spatially filtered OLS (clustered SE)"] = {v: filt.params[names.index(v)] for v in HEAD}
        comp_se["Spatially filtered OLS (clustered SE)"] = {v: filt.bse[names.index(v)] for v in HEAD}
        extra_rows.append({"model": "Spatially filtered OLS (clustered SE)", "spatial_param": lam,
                           "spatial_param_se": np.nan,
                           "residual_moran_I_k8": resid_moran(filt.resid),
                           "note": "uses lambda from the GMM error model; SE clustered by tract"})
    if fit_lag:
        lag = spreg.GM_Lag(y, Xs, w=w8, robust="white", name_x=xnames, name_y="log_price")
        rho = lag.betas[-1, 0]
        comp["Spatial lag (GMM), total impact"] = {v: lag.betas[ix[v], 0] / (1 - rho) for v in HEAD}
        comp_se["Spatial lag (GMM), total impact"] = {v: lag.std_err[ix[v]] / (1 - rho) for v in HEAD}
        comp["Spatial lag (GMM), direct coef"] = {v: lag.betas[ix[v], 0] for v in HEAD}
        comp_se["Spatial lag (GMM), direct coef"] = {v: lag.std_err[ix[v]] for v in HEAD}
        extra_rows.append({"model": "Spatial lag (GMM), total impact", "spatial_param": rho,
                           "spatial_param_se": lag.std_err[-1],
                           "residual_moran_I_k8": resid_moran(lag.u),
                           "note": "rho = spatial lag parameter; total = beta/(1-rho); SE approx."})
    if fit_err and fit_lag:
        combo = spreg.GM_Combo_Het(y, Xs, w=w8, name_x=xnames, name_y="log_price")
        rho_c, lam_c = combo.betas[-2, 0], combo.betas[-1, 0]
        comp["SARAR (GMM), total impact"] = {v: combo.betas[ix[v], 0] / (1 - rho_c) for v in HEAD}
        comp_se["SARAR (GMM), total impact"] = {v: combo.std_err[ix[v]] / (1 - rho_c) for v in HEAD}
        extra_rows.append({"model": "SARAR (GMM), total impact", "spatial_param": rho_c,
                           "spatial_param_se": combo.std_err[-2],
                           "residual_moran_I_k8": resid_moran(combo.e_filtered),
                           "note": f"rho = {rho_c:.3f}, lambda = {lam_c:.3f}"})
else:
    decision["models_fitted"] = "none (no clear positive autocorrelation)"

cmp = pd.DataFrame(comp).T
cmp_se = pd.DataFrame(comp_se).T.add_suffix("_se")
out = pd.concat([cmp, cmp_se], axis=1).reset_index(names="model").merge(
    pd.DataFrame(extra_rows), on="model", how="left")
out.to_csv(RES / "model3_comparison.csv", index=False)
pd.Series(decision).to_csv(RES / "model3_decision.csv", header=["value"])
print("\nDecision:", decision)
print("\nComparison of headline coefficients\n" + out[["model"] + HEAD + ["spatial_param",
                                                                        "residual_moran_I_k8"]]
      .round(4).to_string(index=False))
print(out[["model"] + [v + "_se" for v in HEAD]].round(4).to_string(index=False))

# ------------------------------------------------------------------ figures
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10.5,
                     "axes.spines.top": False, "axes.spines.right": False})
hoods = gpd.read_file(ROOT / "data" / "raw" / "hedonic" / "cambridge_neighborhoods.geojson").to_crs(4326)
fig, ax = plt.subplots(figsize=(7.5, 7))
hoods.boundary.plot(ax=ax, color="#52514e", lw=0.6)
lim = np.quantile(np.abs(loc["resid"]), 0.95)
sc = ax.scatter(loc.lon, loc.lat, c=loc["resid"].clip(-lim, lim), cmap="RdBu_r", vmin=-lim, vmax=lim,
                s=np.clip(loc["n"], 1, 30) * 2 + 2, alpha=0.8, lw=0)
cb = fig.colorbar(sc, ax=ax, shrink=0.7)
cb.set_label("Model 1 residual, averaged per location\n(red = sold above model, blue = below)")
ax.set_axis_off()
ax.set_aspect(1 / np.cos(np.radians(42.37)))
ax.set_title(f"Where Model 1 under- and over-predicts\n(Moran's I = {main_moran['moran_I']:.2f} "
             f"for sales, {moran.query('level != \"sales\" and k == 8').iloc[0]['moran_I']:.2f} "
             "between locations, k = 8)", fontsize=11)
fig.tight_layout()
fig.savefig(FIG / "fig_h9_residual_map.png", dpi=200)
fig.savefig(FIG / "fig_h9_residual_map.pdf")
plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(10, 4.4))
for ax, (vals, w, title) in zip(axes, [(df["resid"].to_numpy(), w8, "All sales"),
                                       (loc["resid"].to_numpy(), None, "Locations (between buildings)")]):
    if w is None:
        w = KNN.from_array(lxy, k=8, silence_warnings=True)
        w.transform = "r"
    z = (vals - vals.mean()) / vals.std()
    lagz = w.sparse @ z
    ax.scatter(z, lagz, s=3, alpha=0.25, color="#2a78d6", lw=0)
    b = np.polyfit(z, lagz, 1)
    xs = np.array([z.min(), z.max()])
    ax.plot(xs, b[1] + b[0] * xs, color="#eb6834", lw=1.8, label=f"slope = Moran's I = {b[0]:.2f}")
    ax.axhline(0, color="#52514e", lw=0.6)
    ax.axvline(0, color="#52514e", lw=0.6)
    ax.set_xlabel("Residual (standardised)")
    ax.set_ylabel("Average residual of 8 nearest neighbours")
    ax.set_title(title, fontsize=10.5)
    ax.legend(frameon=False, fontsize=9)
fig.suptitle("Moran scatterplots of Model 1 residuals", fontsize=11.5)
fig.tight_layout()
fig.savefig(FIG / "fig_h10_moran_scatter.png", dpi=200)
fig.savefig(FIG / "fig_h10_moran_scatter.pdf")
plt.close(fig)
print("\nwrote results/hedonic/model3_*.csv and figures fig_h9, fig_h10")
