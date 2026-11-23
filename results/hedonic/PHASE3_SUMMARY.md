# Phase 3 summary: interactions, spatial check, and a data issue (2026-11-22)

*All results are **associations**. They describe how prices differ between similar homes, not
what would happen if something changed.*

## What was done

- **Rules first.** The four interactions, the spatial tests and the rule for choosing a spatial
  model were written in [`SPEC_PHASE3.md`](../../analysis/hedonic/SPEC_PHASE3.md) and committed
  before anything ran. Three things were added after seeing results; they are listed at the
  bottom of that file and labeled as such here.
- **Model 2** ([`35_interactions.py`](../../analysis/hedonic/35_interactions.py)) adds each
  interaction to Model 1 on its own.
- **Model 3** ([`40_spatial.py`](../../analysis/hedonic/40_spatial.py)) checks whether the leftover
  errors cluster on the map, then fits spatial models.
- **A data issue** turned up in the residuals: likely deed-restricted affordable homes. It is
  checked in [`45_restricted_check.py`](../../analysis/hedonic/45_restricted_check.py).

## Model 2: does one factor's price association depend on another?

**In plain words:** an interaction asks, for example, "is being near the T associated with a
*bigger* price difference in higher-income tracts than in lower-income ones?"

Four interactions are tested. That raises the chance that one looks important by luck alone, so
the p-values are also given after the **Holm correction**, which accounts for testing several
things at once.

| Interaction (planned in PLAN.md) | What the numbers say | Bootstrap p | After Holm correction |
|---|---|---|---|
| **I1 income × transit** | Living farther from the T (514 → 911 m) goes with −0.1% in the lowest-income tracts, −2.8% in middle ones and −4.3% in the highest-income ones | 0.07 | 0.20 |
| **I2 bedrooms × transit** | Same distance: −2.2% for 1-bedroom homes, −4.6% for 5-bedroom homes | 0.21 | 0.43 |
| **I3 violent crime × income** | No meaningful difference across income levels | 0.55 | 0.55 |
| **I4 living area × after COVID** | Space became more valuable. 10% more living area went with **+5.4% price in 2016** and **+6.8% in 2025** | **0.02** | 0.08 |

Figures: [`fig_h7_interactions.png`](../../figures/hedonic/fig_h7_interactions.png) and
[`fig_h8_area_by_year.png`](../../figures/hedonic/fig_h8_area_by_year.png).

**What this means:**
- **Space became more valuable (I4).** This is the clearest pattern. The value of extra living
  area rose fairly steadily over the decade, not as a sudden jump in 2020. It passes the bootstrap
  test on its own (p = 0.02) but narrowly misses after the multiple-testing correction (0.08).
  Call it **suggestive**: likely real, but not firmly established.
- **Income × transit and bedrooms × transit (I1, I2).** Nearness to the T may matter more for
  higher-income areas and larger homes. Both patterns point the same way, but neither is reliable
  after correction. **Not established.**
- **Crime × income (I3).** Nothing there.
- **The houses-vs-condos lead from Phase 2 (exploratory E1) did not hold up.** When only the
  transit association is allowed to differ by home type, houses (−3.9%) and condos (−2.9%) look
  the same. Without West Cambridge both turn slightly *positive* (+2–3%). So the Phase 2 transit
  association rests largely on that one neighborhood, as suspected.

## Model 3: do the model's errors cluster on the map?

**In plain words:** if homes close together all sell for more (or less) than the model predicts,
something local is missing, and the uncertainty ranges are too optimistic. **Moran's I** measures
this clustering: 0 means none, and 1 would mean neighbours' errors are identical.

- **Yes, strongly, but mostly *within the same building*.**
  - Moran's I is **0.21** when each sale is compared with its 8 nearest sales (0.24 and 0.19 with
    5 and 15 neighbours; all p = 0.001).
  - The 9,024 sales sit at only 3,605 locations, because condo units in one building share their
    parcel's coordinates. **63%** of the leftover variation is *between* locations. In other
    words, units in the same building sell above or below the model together: a shared lobby,
    view, management, renovation or building reputation that the assessor data do not capture.
- **Between buildings the clustering is small**: Moran's I = **0.06** (0.05–0.07 depending on
  the number of neighbours). It is still statistically clear, because there are so many sales.
- Figures: [`fig_h9_residual_map.png`](../../figures/hedonic/fig_h9_residual_map.png) and
  [`fig_h10_moran_scatter.png`](../../figures/hedonic/fig_h10_moran_scatter.png).

**Which spatial model?** By the pre-set rule, the tests strongly favour a **spatial error model**:
shared unmeasured local factors, such as the building effect above. The alternative, prices
"spilling over" to neighbours (a lag model), scores far lower (test statistic 1,374 vs 55). Both
passed the threshold, so all three models were fitted, as planned. Only the error model removes
the clustering from the residuals (Moran's I falls from 0.21 to 0.00). The lag model leaves 0.16.

**Do the main results change?** No. The comparison is in
[`model3_comparison.csv`](model3_comparison.csv).

| | Violent crime | Property crime | Income (log) | Transit (per km) |
|---|---|---|---|---|
| Model 1 | +0.047 | +0.019 | +0.040 | −0.082 |
| Spatial error model | +0.056 | +0.010 | +0.037 | −0.063 |

- The spatial software reports much smaller standard errors, but they do not allow for the
  neighborhood-wide correlation that Phase 2 showed matters. Re-estimated with the same cautious
  methods as Model 1 (added after seeing results), **all four ranges still include zero**
  ([`model3_filtered_clustered.csv`](model3_filtered_clustered.csv)).

## A data issue: likely deed-restricted affordable homes

The largest errors came from a distinct group: **201 sales in 76 buildings**, almost all condos,
selling at about **$250 per sq ft against a citywide median of about $840**. The assessor values
them just as low, often at one flat value for every unit in a building. This is the pattern of
**deed-restricted affordable homes**: Cambridge's affordable homeownership units, whose resale
price is capped by the deed. Those are **not market sales**, which your cleaning rule says to
remove. The $0/$1 and low-ratio filters missed them, because both the price *and* the assessment
are low. The database has no field that marks them, so the identification is an inference, not a
certainty.

- **Rule (defined after seeing the data, so labeled as a check):** flag a sale when *both* its
  price and its assessed value per sq ft are below half the median for the same home type and
  year. A real bargain with a normal assessment is not flagged.
- **Where they are:** mostly The Port (42), North Cambridge (37), East Cambridge (35),
  Cambridgeport (21) and Wellington-Harrington (20).

**Re-running Models 1–3 without them** ([`check_restricted_model1.csv`](check_restricted_model1.csv)):

- The model fits much better: it explains **85%** of price differences instead of 78%.
- Crime and income move to almost exactly zero: +0.2%, +0.7% and +0.3% for a typical low → high
  change. The small positive crime association in Phase 2 partly came from these homes.
- Distance to the T: **−4.0%** for 514 → 911 m. The tract-clustered range now excludes zero
  (−6.9% to −1.0%). The more honest bootstrap range still does not (−9.3% to +4.4%).
- Interactions: the living-area trend (I4) stays (bootstrap p = 0.03, Holm 0.11). The others
  remain unclear.
- Spatial: same picture (Moran's I 0.18 for sales, 0.06 between buildings).

**The overall conclusions do not change.** But these sales should not count as market sales.
Recommendation: **remove them from the main sample from Phase 4 on**, and report Phases 2–3 both
ways. This changes the sample definition, so it needs your OK.

## Overall picture after Phases 2–3

1. **Prices are explained mainly by the home itself** (size, bathrooms, type, condition), by
   **which neighborhood** it is in and by **when** it sold. Within a neighborhood, crime, tract
   income and distance to the T add little that can be measured reliably.
2. **Space has become more valuable over time** (suggestive).
3. **Transit:** a modest price penalty for being farther from the T is plausible (about −3 to
   −4% for an extra 400 m). It cannot be pinned down with 12 neighborhoods, and it depends
   heavily on West Cambridge.
4. **Building-level factors matter a lot.** Units in the same building share price differences
   that public data cannot explain.

## Files

- Results:
  - `model2_interactions.csv`, `model2_marginal_effects.csv`, `model2_area_by_year.csv`,
    `model2_all_four_together.csv`.
  - `model3_moran.csv`, `model3_lm_tests.csv`, `model3_comparison.csv`,
    `model3_filtered_clustered.csv`, `model3_decision.csv`.
  - `check_restricted_model1.csv`, `check_restricted_model2.csv`, `check_restricted_moran.csv`.
- Figures: `fig_h7` to `fig_h10`.
