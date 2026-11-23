"""Verification of wildboot.py (the fast wild cluster bootstrap).

CHECKS
  1. The fast t statistic equals statsmodels' cluster-robust t (same CR1 correction).
  2. For 50 random weight draws, the fast bootstrap t* equals the t from actually building the
     bootstrap dataset and refitting the regression with statsmodels.
  3. Size: on simulated data where the true coefficient is 0, with 12 unequal clusters, the test
     rejects at 5% about 5% of the time (not far more, not far less).

RUN
  uv run python analysis/hedonic/verify_wild_bootstrap.py
"""
import sys
from pathlib import Path

import numpy as np
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).parent))
from wildboot import WildClusterBootstrap  # noqa: E402

rng = np.random.default_rng(1)
ok = True

# a design like Model 1: 12 unequal clusters, cluster-level shock, a regressor varying within
sizes = rng.integers(50, 1500, size=12)
g = np.repeat(np.arange(12), sizes)
n = len(g)
x = rng.normal(size=n) + 0.5 * rng.normal(size=12)[g]
z = rng.normal(size=(n, 3))
D = np.eye(12)[g][:, 1:]
X = np.column_stack([np.ones(n), x, z, D])
y = X @ rng.normal(size=X.shape[1]) * 0.1 + rng.normal(size=12)[g] * 0.3 + rng.normal(size=n)

wb = WildClusterBootstrap(X, y, g, n_boot=999, seed=2)
sm_fit = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": g})
d1 = abs(wb.t_stat(1) - sm_fit.tvalues[1])
print(f"1. t statistic: fast {wb.t_stat(1):.6f}, statsmodels {sm_fit.tvalues[1]:.6f}, diff {d1:.2e}")
ok &= d1 < 1e-8

b0 = 0.05
yfit_r, ur = wb.restricted(1, b0)
Wtest = wb.W[:50]
fast = wb.t_star(1, b0, Wtest)
brute = []
for w in Wtest:
    ys = yfit_r + ur * w[g]
    f = sm.OLS(ys, X).fit(cov_type="cluster", cov_kwds={"groups": g})
    brute.append((f.params[1] - b0) / f.bse[1])
d2 = np.max(np.abs(fast - np.array(brute)))
print(f"2. bootstrap t* vs brute-force refits (50 draws): max abs diff {d2:.2e}")
ok &= d2 < 1e-6

rej = []
for rep in range(300):
    y0 = (X[:, [0, 2, 3, 4]] @ rng.normal(size=4) + rng.normal(size=12)[g] * 0.5
          + rng.normal(size=n) * (1 + 0.5 * (g % 3)))
    w0 = WildClusterBootstrap(X, y0, g, n_boot=399, seed=rep)
    rej.append(w0.pvalue(1) < 0.05)
size = np.mean(rej)
print(f"3. rejection rate under a true null (300 simulations, nominal 5%): {size:.3f}")
ok &= 0.01 <= size <= 0.10

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
