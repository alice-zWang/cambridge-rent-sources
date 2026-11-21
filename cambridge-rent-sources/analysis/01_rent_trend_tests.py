"""Are Cambridge rents rising? t-tests for the slope of a regression line.

Fits median rent (City of Cambridge, 2010-2025) on year for 1-, 2- and 3-bedroom
apartments, in nominal and inflation-adjusted dollars, then checks whether the
2-bedroom results hold when unusual years are removed.

Outputs: results/slope_tests.csv, results/sensitivity_2br.csv,
figures/fig1_rent_trend_2br.png, fig2_residuals_2br.png, fig3_slopes_ci.png
"""
import csv

import numpy as np
import scipy.stats as st

from common import BLUE, ORANGE, GRID, MUTED, TEXT, RAW, RESULTS, dollars, plt, save

rows = list(csv.DictReader(open(RAW / "cambridge_median_rents_2010_2025.csv")))
year = np.array([int(r["year"]) for r in rows])


def series(col, keep=None):
    keep = keep if keep is not None else np.ones(len(rows), bool)
    return year[keep], np.array([float(r[col]) for r in rows])[keep]


def slope_test(x, y):
    res = st.linregress(x, y)
    df = len(y) - 2
    resid = y - (res.intercept + res.slope * x)
    tcrit = st.t.ppf(0.975, df)
    return {
        "n": len(y), "slope": res.slope, "intercept": res.intercept, "se_slope": res.stderr,
        "t": res.slope / res.stderr, "df": df, "p_value": res.pvalue,
        "ci_low": res.slope - tcrit * res.stderr, "ci_high": res.slope + tcrit * res.stderr,
        "r": res.rvalue, "r_squared": res.rvalue ** 2,
        "s_resid": float(np.sqrt(np.sum(resid ** 2) / df)),
        "shapiro_p_resid": st.shapiro(resid).pvalue,
    }


# --- Main tests: every bedroom size, nominal and adjusted --------------------
out = []
for beds in ("1br", "2br", "3br"):
    for kind, label in (("nominal", "nominal"), ("cpi_adjusted", "inflation-adjusted")):
        x, y = series(f"{kind}_{beds}_median_rent")
        out.append({"bedrooms": beds.upper(), "dollars": label, **slope_test(x, y)})

with open(RESULTS / "slope_tests.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader()
    for row in out:
        w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()})
print("Slope tests (two-sided, H0: slope = 0):")
for r in out:
    print(f"  {r['bedrooms']} {r['dollars']:<19} b = {r['slope']:7.2f}/yr  t = {r['t']:5.2f}  p = {r['p_value']:.4f}")

# --- Sensitivity: drop January 2010 and/or the 2020 COVID year (2BR) ---------
sens = []
for dropped in ([], [2010], [2020], [2010, 2020]):
    keep = ~np.isin(year, dropped)
    for kind in ("nominal", "cpi_adjusted"):
        x, y = series(f"{kind}_2br_median_rent", keep)
        r = slope_test(x, y)
        sens.append({"years_dropped": " & ".join(map(str, dropped)) or "none", "dollars": kind,
                     "n": r["n"], "slope": round(r["slope"], 2), "t": round(r["t"], 2), "p_value": round(r["p_value"], 4)})
with open(RESULTS / "sensitivity_2br.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(sens[0].keys()))
    w.writeheader()
    w.writerows(sens)

# --- Figure 1: scatterplot with least-squares lines (2BR) --------------------
fig, ax = plt.subplots(figsize=(8, 5.4))
for kind, color, label in (("nominal", BLUE, "Nominal (dollars of each year)"),
                           ("cpi_adjusted", ORANGE, "Inflation-adjusted (Sept 2025 dollars)")):
    x, y = series(f"{kind}_2br_median_rent")
    r = st.linregress(x, y)
    xs = np.array([2009.6, 2025.4])
    ax.plot(xs, r.intercept + r.slope * xs, color=color, lw=2)
    ax.scatter(x, y, s=55, color=color, edgecolor="white", linewidth=1.5, zorder=3, label=label)
    sign = "+" if r.slope > 0 else "−"
    ax.text(2025.6, r.intercept + r.slope * 2025.4, f"{sign}${abs(r.slope):.0f}/yr", color=TEXT, va="center")
ax.annotate("Jan 2010\n(other years: Aug/Sept)", (2010, 2180), xytext=(10, -6),
            textcoords="offset points", fontsize=10, color=MUTED, va="top")
ax.set(xlim=(2009.3, 2027.3), ylim=(1800, 4400), xlabel="Year", ylabel="Median 2-bedroom rent (USD/month)")
dollars(ax)
ax.grid(axis="y", color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.45, -0.16), ncol=2, fontsize=10)
ax.set_title("Median 2-bedroom rent in Cambridge, 2010–2025", loc="left", fontsize=13)
save(fig, "fig1_rent_trend_2br.png")

# --- Figure 2: residual plots ------------------------------------------------
fig, axs = plt.subplots(1, 2, figsize=(8, 3.4), sharey=True)
for ax, kind, color, title in ((axs[0], "nominal", BLUE, "Nominal"), (axs[1], "cpi_adjusted", ORANGE, "Inflation-adjusted")):
    x, y = series(f"{kind}_2br_median_rent")
    r = st.linregress(x, y)
    e = y - (r.intercept + r.slope * x)
    ax.axhline(0, color="#8a8984", lw=1)
    ax.scatter(x, e, s=45, color=color, edgecolor="white", linewidth=1.2, zorder=3)
    for yr, lab in ((2010, "2010 (Jan)"), (2020, "2020")):
        i = list(x).index(yr)
        ax.annotate(lab, (yr, e[i]), xytext=(6, -4), textcoords="offset points", fontsize=9, color=MUTED)
    ax.set_title(f"Residuals: {title}", loc="left", fontsize=12)
    ax.set_xlabel("Year")
axs[0].set_ylabel("Residual (USD)")
save(fig, "fig2_residuals_2br.png")

# --- Figure 3: slopes with 95% confidence intervals --------------------------
fig, ax = plt.subplots(figsize=(8, 3.6))
for i, r in enumerate(out):
    yv = len(out) - i
    color = BLUE if r["dollars"] == "nominal" else ORANGE
    ax.plot([r["ci_low"], r["ci_high"]], [yv, yv], color=color, lw=2.5, solid_capstyle="round")
    ax.scatter([r["slope"]], [yv], s=60, color=color, edgecolor="white", linewidth=1.5, zorder=3)
ax.axvline(0, color=MUTED, lw=1.2, ls="--")
ax.text(1, len(out) + 0.6, "no trend", fontsize=10, color=MUTED)
ax.set_yticks(range(len(out), 0, -1))
ax.set_yticklabels([f"{r['bedrooms'][0]}-bedroom, {'nominal' if r['dollars'] == 'nominal' else 'adjusted'}" for r in out])
ax.set_xlabel("Slope (USD per year), with 95% confidence interval")
ax.set_ylim(0.4, len(out) + 0.9)
ax.grid(axis="x", color=GRID, lw=0.8)
ax.set_axisbelow(True)
save(fig, "fig3_slopes_ci.png")
