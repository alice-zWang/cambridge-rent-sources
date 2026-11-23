"""Step 45: do the Model 1-3 results change without likely deed-restricted sales?

WHAT THIS DOES (plain words)
  Phase 3 found about 200 condo sales whose price AND assessed value are both under half the usual
  level per sq ft. That is the pattern of deed-restricted affordable homes (resale price capped),
  which are not market sales. This script re-runs the key results without them:
    - Model 1 headline estimates (tract-clustered and wild-bootstrap uncertainty);
    - Model 2 interactions (bootstrap p-values with Holm correction);
    - Moran's I of the residuals.
  The flag was defined after seeing results, so this is a robustness check, labeled as such.

OUTPUTS
  results/hedonic/check_restricted_model1.csv, check_restricted_model2.csv, check_restricted_moran.csv

RUN
  uv run python analysis/hedonic/45_restricted_check.py
"""
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from esda.moran import Moran
from libpysal.weights import KNN

sys.path.insert(0, str(Path(__file__).parent))
from model_common import HEAD, LABEL, RES, fit, formula, load, pct  # noqa: E402
from wildboot import WildClusterBootstrap  # noqa: E402

N_BOOT = 9999
SEED = 20261122
df_all, full = load()
q = full[HEAD].quantile([0.25, 0.75])
DELTA = (q.loc[0.75] - q.loc[0.25]).to_dict()       # same "typical change" as Model 1
samples = {"main (Model 1 sample)": full,
           "without likely deed-restricted": full[~full["flag_restricted_likely"]].reset_index(drop=True)}

# ------------------------------------------------------------------ Model 1
rows = []
for name, d in samples.items():
    res = fit(d, formula())
    wb = WildClusterBootstrap(res.model.exog, res.model.endog, d["neighborhood"], n_boot=N_BOOT,
                              seed=SEED)
    ci = res.conf_int()
    for v in HEAD:
        j = res.model.exog_names.index(v)
        lo, hi = wb.ci(j, res.bse[v])
        rows.append({"sample": name, "n": int(res.nobs), "r2": res.rsquared, "variable": v,
                     "label": LABEL[v], "coef": res.params[v], "se_tract": res.bse[v],
                     "p_tract": res.pvalues[v], "p_wild_bootstrap": wb.pvalue(j),
                     "pct_typical": pct(res.params[v], DELTA[v]),
                     "pct_ci_tract": f"{pct(ci.loc[v, 0], DELTA[v]):+.1f} to {pct(ci.loc[v, 1], DELTA[v]):+.1f}",
                     "pct_ci_boot": f"{pct(lo, DELTA[v]):+.1f} to {pct(hi, DELTA[v]):+.1f}"})
m1 = pd.DataFrame(rows)
m1.to_csv(RES / "check_restricted_model1.csv", index=False)
print(m1[["sample", "n", "r2", "label", "coef", "p_tract", "p_wild_bootstrap", "pct_typical",
          "pct_ci_tract", "pct_ci_boot"]].round(4).to_string(index=False))

# ------------------------------------------------------------------ Model 2
PRE = ["I1_income_x_transit", "I2_bedrooms_x_transit", "I3_violent_x_income", "I4_area_x_post"]
rows = []
for name, d in samples.items():
    d = d.copy()
    for v, c in [("log_income", "c_income"), ("transit_km", "c_transit"), ("bedrooms", "c_bed"),
                 ("crime_violent_500", "c_violent"), ("log_area", "c_area")]:
        d[c] = d[v] - d[v].mean()
    d["I1_income_x_transit"] = d["c_income"] * d["c_transit"]
    d["I2_bedrooms_x_transit"] = d["c_bed"] * d["c_transit"]
    d["I3_violent_x_income"] = d["c_violent"] * d["c_income"]
    d["I4_area_x_post"] = d["c_area"] * (d["saledate"] >= pd.Timestamp("2020-04-01"))
    d["house"] = d["group"].isin(["single_family", "two_family", "three_family"]).astype(int)
    d["E1_transit_x_house"] = d["c_transit"] * d["house"]
    block = []
    for term in PRE + ["E1_transit_x_house"]:
        res = fit(d, formula(extra=f" + {term}"))
        wb = WildClusterBootstrap(res.model.exog, res.model.endog, d["neighborhood"], n_boot=N_BOOT,
                                  seed=SEED)
        j = res.model.exog_names.index(term)
        block.append({"sample": name, "term": term, "coef": res.params[term], "se_tract": res.bse[term],
                      "p_tract": res.pvalues[term], "p_wild_bootstrap": wb.pvalue(j)})
    b = pd.DataFrame(block)
    pre = b[b["term"].isin(PRE)].sort_values("p_wild_bootstrap")
    running, adj = 0.0, []
    for i, p in enumerate(pre["p_wild_bootstrap"]):
        running = max(running, min(1.0, (len(pre) - i) * p))
        adj.append(running)
    b.loc[pre.index, "p_holm"] = adj
    rows.append(b)
m2 = pd.concat(rows, ignore_index=True)
m2.to_csv(RES / "check_restricted_model2.csv", index=False)
print("\n" + m2.round(4).to_string(index=False))

# ------------------------------------------------------------------ Moran's I
rows = []
for name, d in samples.items():
    res = fit(d, formula())
    r = res.resid.to_numpy()
    p = gpd.GeoSeries(gpd.points_from_xy(d.longitude, d.latitude), crs=4326).to_crs(26986)
    w = KNN.from_array(np.column_stack([p.x, p.y]), k=8, silence_warnings=True)
    w.transform = "r"
    np.random.seed(SEED)
    mi = Moran(r, w, permutations=999)
    loc_id = d.groupby([d.latitude.round(7), d.longitude.round(7)]).ngroup().to_numpy()
    lr = pd.Series(r).groupby(loc_id).mean()
    lxy = pd.DataFrame({"x": p.x.to_numpy(), "y": p.y.to_numpy()}).groupby(loc_id).first()
    wl = KNN.from_array(lxy.to_numpy(), k=8, silence_warnings=True)
    wl.transform = "r"
    np.random.seed(SEED)
    ml = Moran(lr.to_numpy(), wl, permutations=999)
    within = ((r - pd.Series(r).groupby(loc_id).transform("mean").to_numpy()) ** 2).sum()
    rows.append({"sample": name, "moran_I_sales_k8": mi.I, "p_sales": mi.p_sim,
                 "moran_I_locations_k8": ml.I, "p_locations": ml.p_sim,
                 "share_resid_var_between_locations": 1 - within / ((r - r.mean()) ** 2).sum(),
                 "resid_sd": r.std()})
mo = pd.DataFrame(rows)
mo.to_csv(RES / "check_restricted_moran.csv", index=False)
print("\n" + mo.round(4).to_string(index=False))
