# Phase 2 summary: Model 1, the first price model (2026-11-22)

*Every result here is an **association**: homes with feature X sold for more or less than similar
homes without it. None of it shows that changing X would change prices.*

## What was done

1. **Rules written down first.** Before any regression ran, the crime categories, the transit
   station dates, the exact model and all robustness checks were written in
   [`SPEC_MODEL1.md`](../../analysis/hedonic/SPEC_MODEL1.md) and committed to git. The commit date
   shows they were not adjusted to fit the results. One diagnostic added later is listed at the
   bottom of that file.
2. **Features for each sale** ([`20_build_features.py`](../../analysis/hedonic/20_build_features.py)):
   - **Neighborhood** and **census tract**.
   - **Tract median household income** (Census 2020–2024, with its margin of error).
   - **Violent crime** and **property crime against residents** reported within 500 m in the
     three years before the sale, per km² per year. Shoplifting, fraud, warrant arrests, traffic
     and similar categories are left out.
   - **Distance to the nearest T station open on the sale date.** The old Lechmere closed in May
     2020, the new Lechmere and Union Square opened in March 2022, and the Medford branch opened in
     December 2022.
   - Only 3 of 9,027 sales were lost (outside all neighborhood boundaries), leaving **9,024 sales**.
3. **Model 1** ([`30_hedonic_ols.py`](../../analysis/hedonic/30_hedonic_ols.py)) compares each
   sale with similar homes in the **same neighborhood**, sold in the **same quarter**. "Similar"
   means type, living area, bedrooms, bathrooms, age, condition, construction grade and parking.

## How Model 1 works, in plain words

The model splits a sale price into parts: so much for the space, so much per bathroom, so much
for the neighborhood and the quarter it sold in. Then it asks what is left over for crime,
income and transit. It explains **78% of the differences in (log) prices** between sales. Almost
all of that comes from the home itself, its neighborhood and the sale date.

## Main result: the four neighborhood factors

For each factor, the table compares a typical **low** value with a typical **high** value
(25th and 75th percentiles of the sales).

| Factor | Typical low → high | Price difference | 95% range, clustered by tract | 95% range, bootstrap by neighborhood |
|---|---|---|---|---|
| Violent crime nearby | 10 → 36 reports/km²/yr | +1.3% | −0.2% to +2.8% | −1.0% to +5.2% |
| Property crime nearby | 68 → 179 reports/km²/yr | +2.1% | −3.2% to +7.7% | −1.8% to +9.6% |
| Tract median income | $110k → $162k | +1.6% | −1.5% to +4.7% | −3.2% to +8.0% |
| Distance to nearest station | 514 m → 911 m | −3.2% | −7.0% to +0.8% | −9.7% to +7.2% |

Figure: [`fig_h5_model1_effects.png`](../../figures/hedonic/fig_h5_model1_effects.png).

**What this means:**
- **No factor shows a clear association with price** once similar homes in the same neighborhood
  are compared. Every 95% range includes zero.
- **The ranges are wide.** The data is consistent with a small price penalty for distance from
  the T, and also with none.
- **Why two ranges?** The data contains only 12 neighborhoods. Standard formulas for grouped data
  are unreliable with so few groups, so the wider **bootstrap** range is the more honest one.
- **Crime comes out slightly positive.** This does *not* mean crime raises prices. Reported crime
  is highest on busy, central blocks near the squares, which also have shops, restaurants and
  transit. The crime measure mostly picks up "how central and busy" a location is.

## Checks on the result

- **Do the factors overlap too much to separate?** Partly.
  - Violent and property crime move together (correlation 0.72 within neighborhoods). Read them as
    one "busy, central location" signal, not two separate effects.
  - Crime and distance to the T are also linked (−0.4 to −0.5): central blocks are near stations
    and have more reports.
  - The variance inflation factors stay below 2.4 for the four factors, under the usual warning
    level of 5. So the overlap makes estimates less precise but does not break the model.
  - Dropping one crime measure roughly doubles the other's estimate
    ([`model1_drop_one.csv`](model1_drop_one.csv)).
  - Figure: [`fig_h6_model1_correlations.png`](../../figures/hedonic/fig_h6_model1_correlations.png).
- **Little to work with inside neighborhoods.** After comparing within neighborhoods, only 38% of
  the variation in property crime and 44% of the variation in transit distance remains. Much of
  what makes these factors differ is *which neighborhood* a home is in, and that difference is
  already absorbed by the neighborhood comparison.
- **One neighborhood drives the transit estimate.** Leaving out West Cambridge reverses its sign
  (from about −8% to about +6.5% per km farther). In West Cambridge, homes far from the T are also far from Harvard
  Square, so "distance to the T" there also measures "distance to the Square". This explains the
  much wider bootstrap range ([`model1_leave_one_neighborhood_out.csv`](model1_leave_one_neighborhood_out.csv)).
- **Income uncertainty.** The Census margin of error was carried through by re-running the model
  200 times with income drawn within its margin. The income result then ranges from about −0.4%
  to +2.8% (typical low → high tract, against +1.6% in the main model) and averages a bit lower.
  The other estimates barely change
  ([`model1_income_moe.csv`](model1_income_moe.csv)).
- **Robustness table** ([`model1_robustness.csv`](model1_robustness.csv)): including flagged
  sales, dropping extreme prices, other crime radii (300 m and 800 m), crime without the
  commercial squares, transit in distance bands, and stations on both sides of the river.
  - No version makes any factor clearly and consistently different from zero.
  - Two patterns are worth following up, as **exploratory** findings, not conclusions:
    - **Single- to three-family homes:** a clearer transit association (about **−7.5% per 400 m
      farther**, 95% range about −11% to −4%, tract clustering). For condos it is close to zero.
    - **Transit bands:** homes 400–800 m from a station sold for slightly *more* than homes
      within 400 m (+6.5%, range −1.7% to +15.4%). Right next to a station may come with noise
      and traffic.

## What the home features are worth (controls, for orientation)

Compared with similar homes in the same neighborhood and quarter:
- **Living area:** 10% more living area goes with about **6% higher** price.
- **Bathrooms:** an extra full bathroom **+14.6%**, an extra half bathroom **+7.8%**.
- **Parking:** an extra parking space **+2.6%**.
- **Bedrooms:** an extra bedroom *at the same living area* adds about **+1.5%** (range −0.4% to
  +3.4%). Splitting the same space into more rooms adds little.
- **Home type:** at the same size, a single-family house sells for about **14% more** than a
  condo. Two- and three-family houses sell for about 12% and 20% less.

## What this means for the next phases

- The neighborhood factors are hard to separate from "which neighborhood" and "how central".
  Model 2's planned interactions (income × transit, bedrooms × transit, crime × income,
  living area × year) will be **less precise still**, so they will be read with care.
- The difference between houses and condos on transit is the most promising lead. It will be
  tested in Phase 3 and labeled exploratory, because it was not in the original plan.
- Model 3 (Moran's I) will check whether the leftover errors cluster on the map. If they do, the
  ranges above are too narrow, which would strengthen the "no clear effect" conclusion.

## Files

- Data: `data/processed/hedonic/sales_features.csv`.
- Logs: `feature_log.csv` (rows lost).
- Results:
  - `model1_coefficients.csv`: every coefficient.
  - `model1_headline.csv`: the four neighborhood factors.
  - `model1_wild_bootstrap.csv`.
  - `model1_vif.csv`, `model1_correlations*.csv`, `model1_drop_one.csv`.
  - `model1_income_moe.csv`, `model1_robustness.csv`, `model1_leave_one_neighborhood_out.csv`.
- Check of the bootstrap code: `uv run python analysis/hedonic/verify_wild_bootstrap.py` →
  PASS. It matches brute-force refits exactly and rejects 4.3% of the time when the true effect
  is zero (target 5%).
