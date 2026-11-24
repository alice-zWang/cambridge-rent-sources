"""Is the city's asking-rent series too flat? A check against recent movers.

People who moved in recently pay close to what the market was asking when they
signed, so their rents should grow roughly like asking rents. This compares growth
in the Census ACS 1-year median gross rent for recent movers (table B25113) with
the city's median asking rents, Cambridge, 2015-2024 (no 2020 ACS 1-year release).

Growth is the slope of log(rent) on year, so it is a percent change per year.
The test for a difference regresses log(city / recent movers) on year: a negative
slope means the city series grows more slowly.

Outputs: results/recent_movers_growth.csv, figures/fig8_recent_movers.png
"""
import csv

import numpy as np
import scipy.stats as st

from common import AQUA, BLUE, GRID, MUTED, ORANGE, RAW, RESULTS, YELLOW, plt, save

moved = {int(r["year"]): r for r in csv.DictReader(open(RAW / "census_acs1_rent_by_year_moved.csv"))}
city = {int(r["year"]): r for r in csv.DictReader(open(RAW / "cambridge_median_rents_2010_2025.csv"))}
years = sorted(y for y in moved if y in city)
yr = np.array(years)

series = {
    "Census: recent movers (all sizes)": [int(moved[y]["recent_movers_median_gross_rent"]) for y in years],
    "Census: all renters (all sizes)": [int(moved[y]["all_renters_median_gross_rent"]) for y in years],
    "City asking rent: 1-bedroom": [int(city[y]["nominal_1br_median_rent"]) for y in years],
    "City asking rent: 2-bedroom": [int(city[y]["nominal_2br_median_rent"]) for y in years],
}


def growth(values):
    res = st.linregress(yr, np.log(np.array(values, float)))
    tcrit = st.t.ppf(0.975, len(values) - 2)
    pct = lambda b: (np.exp(b) - 1) * 100
    return pct(res.slope), pct(res.slope - tcrit * res.stderr), pct(res.slope + tcrit * res.stderr)


rows = []
recent = np.array(series["Census: recent movers (all sizes)"], float)
print("Annual growth, 2015-2024 (log-linear fit):")
for name, vals in series.items():
    g, lo, hi = growth(vals)
    row = {"series": name, "first": vals[0], "last": vals[-1], "total_change_pct": round((vals[-1] / vals[0] - 1) * 100, 1),
           "annual_growth_pct": round(g, 2), "ci_low": round(lo, 2), "ci_high": round(hi, 2),
           "gap_vs_recent_movers_pct_per_year": "", "gap_p_value": ""}
    if name.startswith("City"):
        d = st.linregress(yr, np.log(np.array(vals, float)) - np.log(recent))
        row["gap_vs_recent_movers_pct_per_year"] = round(d.slope * 100, 2)
        row["gap_p_value"] = round(d.pvalue, 4)
    rows.append(row)
    extra = f"; vs recent movers {row['gap_vs_recent_movers_pct_per_year']} pts/yr (p = {row['gap_p_value']})" if row["gap_p_value"] != "" else ""
    print(f"  {name:<36} {row['total_change_pct']:5.1f}% total, {g:4.2f}%/yr (95% CI {lo:.2f} to {hi:.2f}){extra}")
with open(RESULTS / "recent_movers_growth.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

# Figure: every series indexed to 2015 = 100
fig, ax = plt.subplots(figsize=(8, 4.6))
colors = [ORANGE, YELLOW, BLUE, AQUA]
for (name, vals), color in zip(series.items(), colors):
    idx = np.array(vals, float) / vals[0] * 100
    for i in range(1, len(yr)):
        ax.plot(yr[i - 1:i + 1], idx[i - 1:i + 1], color=color, lw=2.2 if "recent" in name else 1.8,
                ls="--" if yr[i] - yr[i - 1] > 1 else "-")
    ax.scatter(yr, idx, s=30, color=color, edgecolor="white", linewidth=1, zorder=3, label=name)
    ax.text(yr[-1] + 0.25, idx[-1], f"{idx[-1]:.0f}", va="center", fontsize=9, color=MUTED)
ax.axhline(100, color="#8a8984", lw=1)
ax.set(xlim=(2014.6, 2025.0), ylim=(90, 165), xlabel="Survey year", ylabel="Index (2015 = 100)")
ax.grid(axis="y", color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.legend(frameon=False, loc="upper left", fontsize=9)
ax.set_title("City asking rents tracked recent movers until 2022, then fell away", loc="left", fontsize=13)
save(fig, "fig8_recent_movers.png")
