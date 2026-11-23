"""Wild cluster restricted (WCR) bootstrap for one OLS coefficient, with few clusters.

WHAT THIS IS (plain words)
  Ordinary "clustered" uncertainty formulas assume many clusters. With only 12 neighborhoods they
  are too optimistic. The wild cluster bootstrap re-creates thousands of alternative datasets in
  which, under the hypothesis being tested, each neighborhood's leftover errors are randomly
  flipped and rescaled together, and checks how unusual the real result looks among them.
  (Cameron, Gelbach and Miller 2008; Webb 2023 for the six-point weights used with few clusters.)

  The algebra below avoids refitting the regression for every draw: the coefficient and its
  clustered standard error are linear/quadratic in the random weights, so all draws are computed
  with a few matrix products. verify_wild_bootstrap.py checks this against brute-force refits.
"""
import numpy as np

WEBB = np.array([-np.sqrt(1.5), -1, -np.sqrt(0.5), np.sqrt(0.5), 1, np.sqrt(1.5)])


class WildClusterBootstrap:
    def __init__(self, X, y, groups, n_boot=9999, seed=0):
        self.X, self.y = np.asarray(X, float), np.asarray(y, float)
        n, k = self.X.shape
        self.A = np.linalg.pinv(self.X.T @ self.X) @ self.X.T      # beta = A y
        g_id = np.unique(np.asarray(groups), return_inverse=True)[1]
        self.G = g_id.max() + 1
        self.onehot = np.zeros((n, self.G))
        self.onehot[np.arange(n), g_id] = 1
        self.cr1 = self.G / (self.G - 1) * (n - 1) / (n - k)
        self.W = np.random.default_rng(seed).choice(WEBB, size=(n_boot, self.G))
        self.beta = self.A @ self.y
        self.resid = self.y - self.X @ self.beta

    def t_stat(self, j, b0=0.0):
        """Cluster-robust (CR1) t statistic for H0: beta_j = b0."""
        s = self.onehot.T @ (self.A[j] * self.resid)
        return (self.beta[j] - b0) / np.sqrt(self.cr1 * (s ** 2).sum())

    def restricted(self, j, b0):
        xj = self.X[:, j]
        Xr = np.delete(self.X, j, axis=1)
        yr = self.y - b0 * xj
        br, *_ = np.linalg.lstsq(Xr, yr, rcond=None)
        ur = yr - Xr @ br
        return Xr @ br + b0 * xj, ur                     # restricted fit (incl. b0*xj), residuals

    def t_star(self, j, b0=0.0, W=None):
        """Bootstrap t statistics (one per row of W) under H0: beta_j = b0."""
        W = self.W if W is None else W
        _, ur = self.restricted(j, b0)
        Aj = self.A[j]
        Bj = (Aj * ur) @ self.onehot                     # beta*_j - b0 = Bj @ w
        U = ur[:, None] * self.onehot                    # cluster pieces of ur
        MU = U - self.X @ (self.A @ U)                   # residual-maker applied to each piece
        S = self.onehot.T @ (Aj[:, None] * MU)           # score of cluster h from piece g
        return (W @ Bj) / np.sqrt(self.cr1 * ((W @ S.T) ** 2).sum(axis=1))

    def pvalue(self, j, b0=0.0):
        return float(np.mean(np.abs(self.t_star(j, b0)) >= abs(self.t_stat(j, b0))))

    def ci(self, j, se_guess, level=0.05):
        """Confidence interval by inverting the bootstrap test (bisection on each side)."""
        center = self.beta[j]
        out = []
        for sign in (-1, 1):
            inside, outside = center, center + sign * 3 * se_guess
            while self.pvalue(j, outside) > level:
                outside = center + 2 * (outside - center)
            for _ in range(25):
                mid = (inside + outside) / 2
                if self.pvalue(j, mid) > level:
                    inside = mid
                else:
                    outside = mid
            out.append((inside + outside) / 2)
        return out
