"""What new renters are asked vs. what all renters pay.

Compares the City of Cambridge median asking rent (advertised listings, September of
year t) with the Census ACS 1-year median gross rent paid by all renter households
(calendar year t), by bedroom count, 2015-2024 (no 2020 ACS 1-year release).
The difference is a rough "newcomer premium". Census gross rent includes utilities,
so if anything this understates the premium.

Outputs: data/processed/city_vs_acs.csv, results/asked_vs_paid.csv,
figures/fig7_asked_vs_paid.png
"""
import csv

import numpy as np
import scipy.stats as st

from common import BLUE, GRID, MUTED, ORANGE, PROCESSED, RAW, RESULTS, dollars, plt, save

acs = {int(r["year"]): r for r in csv.DictReader(open(RAW / "census_acs1_gross_rent_by_bedroom.csv"))}
city = {int(r["year"]): r for r in csv.DictReader(open(RAW / "cambridge_median_rents_2010_2025.csv"))}
years = sorted(y for y in acs if y in city)

rows = []
for y in years:
    row = {"year": y}
    for b in ("1", "2", "3"):
        row[f"city_{b}br"] = int(city[y][f"nominal_{b}br_median_rent"])
        row[f"acs_{b}br"] = int(acs[y][f"br{b}_median_gross_rent"])
        row[f"acs_{b}br_moe"] = acs[y][f"br{b}_moe"]
    rows.append(row)
with open(PROCESSED / "city_vs_acs.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

summary = []
print("Asked (city listings) minus paid (Census, all renters):")
for b in ("1", "2", "3"):
    c = np.array([r[f"city_{b}br"] for r in rows], float)
    a = np.array([r[f"acs_{b}br"] for r in rows], float)
    gap = c - a
    t = st.ttest_rel(c, a)
    trend = st.linregress(years, gap)
    s = {"bedrooms": f"{b}BR", "n_years": len(gap), "mean_gap": round(gap.mean(), 1), "sd_gap": round(gap.std(ddof=1), 1),
         "mean_gap_pct": round((gap / a * 100).mean(), 1), "t": round(float(t.statistic), 2), "df": len(gap) - 1,
         "p_value": round(float(t.pvalue), 4), "gap_first": int(gap[0]), "gap_last": int(gap[-1]),
         "gap_trend_per_year": round(trend.slope, 1), "gap_trend_p": round(trend.pvalue, 4),
         "city_growth_pct": round((c[-1] / c[0] - 1) * 100, 1), "acs_growth_pct": round((a[-1] / a[0] - 1) * 100, 1)}
    summary.append(s)
    print(f"  {b}BR: mean ${s['mean_gap']:,.0f} ({s['mean_gap_pct']}%), t = {s['t']}, p = {s['p_value']}; "
          f"{years[0]} ${s['gap_first']:,} -> {years[-1]} ${s['gap_last']:,}")
with open(RESULTS / "asked_vs_paid.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
    w.writeheader()
    w.writerows(summary)

fig, axs = plt.subplots(1, 2, figsize=(9, 4.2), sharey=True)
for ax, b in ((axs[0], "1"), (axs[1], "2")):
    yr = np.array(years)
    c = [r[f"city_{b}br"] for r in rows]
    a = [r[f"acs_{b}br"] for r in rows]
    moe = [float(r[f"acs_{b}br_moe"]) if r[f"acs_{b}br_moe"] else 0 for r in rows]
    for vals, color, label in ((c, BLUE, "Asked: city listings (Sept)"), (a, ORANGE, "Paid: all renters (Census)")):
        for i in range(1, len(yr)):
            ax.plot(yr[i - 1:i + 1], vals[i - 1:i + 1], color=color, lw=2, ls="--" if yr[i] - yr[i - 1] > 1 else "-")
        ax.scatter(yr, vals, s=36, color=color, edgecolor="white", linewidth=1.2, zorder=3, label=label)
    ax.errorbar(yr, a, yerr=moe, fmt="none", ecolor=ORANGE, elinewidth=1, capsize=3, alpha=0.7)
    ax.set_title(f"{b}-bedroom", loc="left", fontsize=12)
    ax.set_xticks([2015, 2018, 2021, 2024])
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
axs[0].set_ylabel("Monthly rent (USD)")
dollars(axs[0])
axs[0].set_ylim(1500, 3600)
axs[0].legend(frameon=False, loc="upper left", fontsize=9)
fig.suptitle("New renters are asked more than current renters pay, but the gap is closing", x=0.01, ha="left", fontsize=13)
axs[1].text(0.98, 0.03, "Error bars: Census 90% margin of error", transform=axs[1].transAxes, ha="right", fontsize=8, color=MUTED)
save(fig, "fig7_asked_vs_paid.png")
