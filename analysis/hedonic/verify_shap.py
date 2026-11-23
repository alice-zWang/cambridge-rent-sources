"""Verification for Model 4 (SPEC_PHASE4.md). Run: uv run python analysis/hedonic/verify_shap.py

Checks
  1. SHAP additivity on the real feature table: baseline + sum of contributions = prediction.
  2. Native categorical splits break SHAP additivity (why categories are coded as numbers).
  3. Feature-level sums of SHAP (one-hot blocks) keep additivity; interaction blocks add up to
     the feature-level SHAP values.
  4. Partial-dependence contrast: exact on a known function; close on a boosted model fitted to
     synthetic data with a known effect.
  5. Spatial folds: no neighborhood (or tract) is in both training and test.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut

sys.path.insert(0, str(Path(__file__).parent))
from boost_common import build_X, feature_interactions, feature_shap, make_model, pd_contrast  # noqa: E402
from model_common import load  # noqa: E402

ok = True


def check(name, cond, detail):
    global ok
    ok &= bool(cond)
    print(f"[{'PASS' if cond else 'FAIL'}] {name}: {detail}")


_, df = load("market_sample")
X, groups = build_X(df, "G2")
y = df["log_price"].to_numpy()
m = make_model().fit(X, y)
sub = X.sample(500, random_state=1)
e = shap.TreeExplainer(m)
sv = e.shap_values(sub)
err = np.abs(sv.sum(1) + e.expected_value - m.predict(sub)).max()
check("1 additivity (G2, real data)", err < 1e-6, f"max error {err:.2e}, {m.n_iter_} trees")

rng = np.random.default_rng(0)
n = 2000
Xc = pd.DataFrame({"a": rng.normal(size=n), "c": pd.Categorical(rng.choice(list("pqrstu"), n))})
yc = Xc.a + Xc.c.map(dict(p=0, q=2, r=0, s=2, t=1, u=-1)).astype(float)
mc = HistGradientBoostingRegressor(categorical_features="from_dtype", max_iter=200).fit(Xc, yc)
Xn = Xc.assign(c=Xc.c.cat.codes)
try:
    ec = shap.TreeExplainer(mc)
    errc = np.abs(ec.shap_values(Xn).sum(1) + ec.expected_value - mc.predict(Xc)).max()
except Exception as ex:  # noqa: BLE001
    errc = np.inf
    print("   (native categorical: SHAP raised", type(ex).__name__, ")")
check("2 native categorical splits break SHAP (expected)", errc > 1e-3, f"max error {errc:.2f}")

fs = feature_shap(sv, sub, groups)
err3 = np.abs(fs.sum(1).to_numpy() + e.expected_value - m.predict(sub)).max()
iv = e.shap_interaction_values(sub.iloc[:100])
fi, names = feature_interactions(iv, sub.iloc[:100], groups)
err3b = np.abs(fi.sum(2) - fs.iloc[:100][names].to_numpy()).max()
check("3 feature-level SHAP and interaction blocks", max(err3, err3b) < 1e-5,
      f"additivity {err3:.2e}; interaction rows vs SHAP {err3b:.2e}")


class Known:
    def predict(self, Z):
        return 0.3 * Z["a"] + 0.5 * Z["a"] * Z["b"]


Z = pd.DataFrame({"a": rng.normal(size=1000), "b": rng.normal(1, 1, size=1000)})
exact = 0.3 * 2 + 0.5 * 2 * Z["b"].mean()
got = pd_contrast(Known(), Z, "a", -1, 1)
Zs = pd.DataFrame({"a": rng.normal(size=8000), "b": rng.normal(size=8000)})
ys = 0.3 * Zs.a + 0.2 * Zs.b + rng.normal(0, 0.1, 8000)
got2 = pd_contrast(make_model().fit(Zs, ys), Zs, "a", -0.67, 0.67)
check("4 partial-dependence contrast", abs(got - exact) < 1e-12 and abs(got2 - 0.3 * 1.34) < 0.03,
      f"known function {got:.6f} vs {exact:.6f}; boosted {got2:.3f} vs true {0.3 * 1.34:.3f}")

bad = 0
for tr, te in LeaveOneGroupOut().split(X, y, df["neighborhood"]):
    bad += len(set(df["neighborhood"].iloc[tr]) & set(df["neighborhood"].iloc[te]))
for tr, te in GroupKFold(n_splits=10).split(X, y, df["tract"]):
    bad += len(set(df["tract"].iloc[tr]) & set(df["tract"].iloc[te]))
check("5 spatial folds disjoint", bad == 0, f"{bad} shared groups")

print("ALL PASS" if ok else "SOME CHECKS FAILED")
sys.exit(0 if ok else 1)
