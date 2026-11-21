"""How much do Cambridge rent sources disagree?

1. Range of "typical rent" (all sizes) across seven public sources.
2. City of Cambridge median 2-bedroom rent vs. HUD Fair Market Rent (Boston metro):
   paired t-test on the yearly gap, and a regression of the gap on year.
   Each HUD fiscal year (starting Oct 1) is paired with the city's value from the
   September just before it, i.e. city year t <-> HUD FY t+1.
3. Rent by apartment size across four sources.

Outputs: data/processed/city_vs_hud.csv, results/source_range.csv, results/gap_tests.json,
figures/fig4_sources_all_sizes.png, fig5_city_vs_hud_2br.png, fig6_by_bedroom.png
"""
import csv
import json

import numpy as np
import scipy.stats as st

from common import AQUA, BLUE, GRID, MUTED, ORANGE, PROCESSED, RAW, RESULTS, TEXT, YELLOW, dollars, plt, save

# --- 1. Range across sources --------------------------------------------------
snap = list(csv.DictReader(open(RAW / "rent_snapshot_all_sizes.csv")))
for r in snap:
    r["v"] = float(r["value_usd_month"])
snap.sort(key=lambda r: r["v"])
lo, hi = snap[0], snap[-1]
listing = [r["v"] for r in snap if "Census" not in r["source"]]
with open(RESULTS / "source_range.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["n_sources", "low", "low_source", "high", "high_source", "spread", "spread_pct", "listing_sites_median"])
    w.writerow([len(snap), lo["v"], lo["source"], hi["v"], hi["source"], hi["v"] - lo["v"],
                round((hi["v"] / lo["v"] - 1) * 100, 1), float(np.median(listing))])
print(f"All-sizes range: ${lo['v']:,.0f} ({lo['source']}) to ${hi['v']:,.0f} ({hi['source']}), spread ${hi['v'] - lo['v']:,.0f}")

fig, ax = plt.subplots(figsize=(8, 4.2))
for i, r in enumerate(snap):
    color = ORANGE if "Census" in r["source"] else BLUE
    ax.plot([2500, r["v"]], [i, i], color=GRID, lw=2, zorder=1)
    ax.scatter(r["v"], i, s=80, color=color, edgecolor="white", linewidth=1.5, zorder=3)
    ax.text(r["v"] + 25, i, f"${r['v']:,.0f}", va="center", fontsize=10, color=MUTED)
ax.set_yticks(range(len(snap)))
ax.set_yticklabels([r["source"] for r in snap])
ax.set_xlim(2500, 3950)
dollars(ax, "x")
ax.set_xlabel("Typical monthly rent, all apartment sizes (USD)")
ax.scatter([], [], color=BLUE, label="Listings (what new renters are asked)")
ax.scatter([], [], color=ORANGE, label="All renters (Census survey, 2019–2023)")
ax.legend(frameon=False, loc="lower right", fontsize=9)
ax.grid(axis="x", color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.set_title("Seven sources, one city: typical Cambridge rent", loc="left", fontsize=13)
save(fig, "fig4_sources_all_sizes.png")

# --- 2. City vs HUD -------------------------------------------------------------
city = {int(r["year"]): r for r in csv.DictReader(open(RAW / "cambridge_median_rents_2010_2025.csv"))}
pairs = []
for h in csv.DictReader(open(RAW / "hud_fmr_boston_metro.csv")):
    y = int(h["fiscal_year"]) - 1
    if y in city:
        pairs.append({"city_year": y, "hud_fiscal_year": int(h["fiscal_year"]),
                      "city_2br": int(city[y]["nominal_2br_median_rent"]), "hud_2br": int(h["br2"]),
                      "city_1br": int(city[y]["nominal_1br_median_rent"]), "hud_1br": int(h["br1"]),
                      "city_3br": int(city[y]["nominal_3br_median_rent"]), "hud_3br": int(h["br3"])})
with open(PROCESSED / "city_vs_hud.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(pairs[0].keys()))
    w.writeheader()
    w.writerows(pairs)

yr = np.array([p["city_year"] for p in pairs])
c = np.array([p["city_2br"] for p in pairs], float)
h = np.array([p["hud_2br"] for p in pairs], float)
gap = c - h
t = st.ttest_rel(c, h)
trend = st.linregress(yr, gap)
tests = {
    "paired_t_test": {"n_pairs": len(gap), "mean_gap": round(gap.mean(), 1), "sd_gap": round(gap.std(ddof=1), 1),
                      "t": round(float(t.statistic), 2), "df": len(gap) - 1, "p_value": round(float(t.pvalue), 4)},
    "gap_trend": {"slope_per_year": round(trend.slope, 1), "r": round(trend.rvalue, 3), "p_value": round(trend.pvalue, 4)},
    "gap_first": {"year": int(yr[0]), "gap": int(gap[0])},
    "gap_last": {"year": int(yr[-1]), "gap": int(gap[-1])},
    "growth": {"city_2br_pct": round((c[-1] / c[0] - 1) * 100, 1), "hud_2br_pct": round((h[-1] / h[0] - 1) * 100, 1)},
    "caveat": "Years are treated as independent pairs; a time series is not, so p-values are approximate.",
}
json.dump(tests, open(RESULTS / "gap_tests.json", "w"), indent=2)
print(f"City vs HUD (2BR): mean gap ${gap.mean():,.0f}, paired t = {t.statistic:.2f}, p = {t.pvalue:.4f}; "
      f"gap {int(yr[0])}: ${gap[0]:,.0f} -> {int(yr[-1])}: ${gap[-1]:,.0f}")

fig, ax = plt.subplots(figsize=(8, 4.6))
for p in pairs:
    ax.plot([p["city_year"]] * 2, [p["hud_2br"], p["city_2br"]], color="#c9c8c2", lw=1, zorder=1)
for key, color, label in (("city_2br", BLUE, "City of Cambridge median asking rent (Sept)"),
                          ("hud_2br", ORANGE, "HUD Fair Market Rent, Boston metro (starts Oct 1)")):
    vals = [p[key] for p in pairs]
    for i in range(1, len(pairs)):
        dashed = pairs[i]["city_year"] - pairs[i - 1]["city_year"] > 1
        ax.plot([pairs[i - 1]["city_year"], pairs[i]["city_year"]], [vals[i - 1], vals[i]],
                color=color, lw=2, ls="--" if dashed else "-")
    ax.scatter(yr, vals, s=40, color=color, edgecolor="white", linewidth=1.2, zorder=3, label=label)
    ax.text(yr[-1] + 0.3, vals[-1], f"${vals[-1]:,.0f}", va="center", fontsize=10, color=TEXT)
ax.set(ylim=(1000, 3600), xlim=(yr[0] - 0.5, yr[-1] + 1.6), xlabel="City data year (HUD fiscal year = year + 1)",
       ylabel="2-bedroom rent (USD/month)")
dollars(ax)
ax.grid(axis="y", color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.legend(frameon=False, loc="lower right", fontsize=9)
ax.set_title("The gap between city listings and HUD's benchmark is closing", loc="left", fontsize=13)
save(fig, "fig5_city_vs_hud_2br.png")

# --- 3. By apartment size -----------------------------------------------------
beds = list(csv.DictReader(open(RAW / "rent_snapshot_by_bedroom.csv")))
order = [("City of Cambridge CDD", BLUE, "City (Sept 2025, median)"),
         ("HUD Fair Market Rent FY2026", ORANGE, "HUD FMR (FY2026)"),
         ("Zillow Rentals", AQUA, "Zillow (2025, average)"),
         ("Apartments.com", YELLOW, "Apartments.com (May 2026, average)")]
sizes = [0, 1, 2, 3]
fig, ax = plt.subplots(figsize=(8, 3.8))
for src, color, label in order:
    pts = [(float(r["value_usd_month"]), int(r["bedrooms"])) for r in beds if r["source"] == src]
    ax.scatter([v for v, _ in pts], [len(sizes) - 1 - b for _, b in pts], s=80, color=color,
               edgecolor="white", linewidth=1.5, zorder=3, label=label)
ax.set_yticks(range(len(sizes)))
ax.set_yticklabels(["3-bedroom", "2-bedroom", "1-bedroom", "Studio"])
ax.set_xlim(2000, 5600)
dollars(ax, "x")
ax.set_xlabel("Monthly rent (USD)")
ax.grid(axis="x", color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, fontsize=9)
ax.set_title("Rent by apartment size and source", loc="left", fontsize=13)
save(fig, "fig6_by_bedroom.png")
