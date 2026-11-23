# Phase 4 summary: gradient boosting with SHAP, and a five-town comparison (2026-11-23)

*All results are **associations**. They describe how prices differ between similar homes, not
what would happen if something changed.*

## What was done

- **Rules first.** Models, settings and tests were written in
  [`SPEC_PHASE4.md`](../../analysis/hedonic/SPEC_PHASE4.md) and committed before anything ran.
  Changes made later are listed at the bottom of that file.
- **New main sample.** As you decided, the likely deed-restricted sales are left out from now on:
  8,823 Cambridge sales.
- **Model 4** ([`50_boosting_shap.py`](../../analysis/hedonic/50_boosting_shap.py)): gradient
  boosting, tested on neighborhoods it never saw, and explained with SHAP.
- **Five towns** ([`55_crosstown_build.py`](../../analysis/hedonic/55_crosstown_build.py),
  [`56_crosstown_models.py`](../../analysis/hedonic/56_crosstown_models.py)): Cambridge,
  Somerville, Arlington, Newton and Brookline, from the state's standardized assessor files.
- **Checks:** [`verify_shap.py`](../../analysis/hedonic/verify_shap.py) passes all 5 checks: the
  explanations add up exactly to the predictions, and no neighborhood is in both training and test.

## Model 4: gradient boosting with SHAP (Cambridge, 8,823 sales)

**In plain words:** gradient boosting builds hundreds of small decision trees, each one fixing the
errors of the ones before. It can find curves and interactions without being told where to look.
**SHAP** then splits each prediction into a contribution from each factor, so we can see what the
model relies on. Three versions: **G1** gets no location information except crime, income and
transit; **G2** also knows the neighborhood, like Model 1; **G3** also knows the map position.

### How accurate is it on areas it has never seen?

([`model4_cv.csv`](model4_cv.csv), [`fig_h11_cv_accuracy.png`](../../figures/hedonic/fig_h11_cv_accuracy.png))

| Version and test | Boosting | Linear regression | Typical error (boosting) |
|---|---|---|---|
| G1, whole neighborhood held out | 79% of price variation | 78% | 13% of price |
| G2, census tracts held out | 83% | 75% (Model 1) | 11% |
| G3, whole neighborhood held out | 83% | 76% | 11% |
| Any version, random folds | 87–88% | 83–85% | 8% |

- Boosting predicts only a little better than the linear models. The gain is largest in the G2 test,
  but there it is mostly an artifact of the test: in one fold the only tract of Baldwin was held
  out, so the linear model had never seen Baldwin and its accuracy fell to 30% in that fold. In the
  other folds the two are within a few points: boosting is 1 point behind to 6 points ahead.
- Random folds look better because test homes then sit next to training homes, often in the same
  building (Phase 3). The spatial numbers are the honest ones.

### What does the model rely on?

([`model4_importance.csv`](model4_importance.csv), [`fig_h12_shap_importance.png`](../../figures/hedonic/fig_h12_shap_importance.png))

- **Living area dominates.** It moves a typical prediction by about 28% of price. Next come sale
  date (9%), full baths (6%), condition (5%) and grade (5%). These five were in the top five in
  almost every one of the 30 refits.
- **The four headline factors are near the bottom** (1–4% each). They were never in the top five in
  any refit.

### "Typical change" numbers, compared with Model 1 on the same sales

([`model4_pd_contrasts.csv`](model4_pd_contrasts.csv); ranges from 30 refits on neighborhood-bootstrap samples)

| Factor (25th → 75th percentile) | Boosting G2 | 95% range | Model 1 (same 8,823 sales) |
|---|---|---|---|
| Violent crime | −0.2% | −3.0 to +3.3 | +0.2% |
| Property crime | −0.3% | −4.8 to +1.2 | +0.7% |
| Tract income | +1.1% | −1.2 to +2.9 | +0.3% |
| Distance to station (514 → 911 m) | −0.5% | −2.2 to +8.9 | −4.0% |
| 10% more living area | +5.6% | +5.2 to +5.8 | +6.1%* |

\*Model 1's area elasticity on the same sample is 0.62.

**What this means:**
- **Crime and income: nothing, again.** A completely different kind of model agrees with Models 1–3.
- **Transit: the shape matters.** Model 1 fits a straight line. The boosting model finds prices
  roughly **flat from 200 m to about 1 km** from a station, then **lower beyond about 1.2 km**
  (about −5% in the farthest group; range −9% to −1%; [`fig_h13`](../../figures/hedonic/fig_h13_shap_dependence.png)).
  So a typical 514 → 911 m change shows almost nothing. The penalty, if real, is for homes far from
  any station, and 60% of those sales are in **West Cambridge**. That is the same neighborhood that
  drove the Phase 2 transit estimate. **Exploratory:** distance to the T cannot be separated from
  what else is different about West Cambridge.
- **Violent crime curve:** prices are slightly higher where recorded violent crime is higher. These
  are busy, central places (squares, main streets) that people pay to be near. This is not a sign
  that crime raises prices.
- **Living area and time:** the model's curves agree closely with Model 1.

### Interactions: does the model find the Model 2 pairs?

([`model4_interactions.csv`](model4_interactions.csv), [`fig_h14_shap_interactions.png`](../../figures/hedonic/fig_h14_shap_interactions.png))

| Planned pair | Rank among all pairs (G2) | Same direction as Model 2? |
|---|---|---|
| I4 living area × time | **3 of 105** | **Yes**: space became more valuable over time |
| I1 income × transit | 52 of 105 | Yes, but weak |
| I2 bedrooms × transit | 55 of 105 | No (weak) |
| I3 violent crime × income | 64 of 105 | No (weak) |

- **Space becoming more valuable (I4) is confirmed** by a model that was never told to look for it.
  It ranks third of all pairs, behind only living area × full baths and living area × grade. In
  G1 it also ranks third.
- The other three planned interactions are weak in boosting too, consistent with Model 2's
  "not established".


## Five towns: what does "being in a town" add to price?

**In plain words:** Cambridge assigns schools by Controlled Choice, so school quality does not change
with address inside the city. Comparing five towns adds district differences. With only five
districts, though, **a school pattern cannot be told apart from everything else that differs by
town**: taxes, services, distance to jobs in Boston and Cambridge, the housing stock, reputation.

**Data.** The state's standardized assessor files give each property's **most recent sale only**:
27,480 sales since 2016 after cleaning (log in
[`crosstown_cleaning_log.csv`](crosstown_cleaning_log.csv)). As a check, 99% of the Cambridge sales
in the state file match a sale in the city's own data with the same date and price. These files
have **no bedrooms, bathrooms, condition or grade**, so "comparable homes" here is coarser than in
Models 1–4.

**C1: town premium.** This compares homes of the same type, size, number of rooms, age and lot size,
at the same distance to the T, in tracts with the same income, sold in the same quarter
([`crosstown_c1_town_premium.csv`](crosstown_c1_town_premium.csv)):

| Town | Price vs a comparable Cambridge home | 95% range |
|---|---|---|
| Brookline | **−12%** | −17% to −7% |
| Somerville | **−24%** | −28% to −20% |
| Newton | **−31%** | −35% to −27% |
| Arlington | **−37%** | −40% to −33% |

- Leaving tract income out barely changes these numbers. The gradient-boosting check gives nearly
  the same ordering and size (−12%, −25%, −28%, −32%).
- The ranges are clustered by census tract (102 tracts). Homes in the same town also share
  town-wide conditions, so the real uncertainty is somewhat larger than shown.

**C2: is space worth more in some towns?** Yes, clearly (joint test p < 0.001). In Cambridge,
1% more living area goes with about 0.87% higher price; in Brookline 0.81%, Newton 0.75%,
Arlington 0.66% and Somerville 0.65%
([`crosstown_c2_area_by_town.csv`](crosstown_c2_area_by_town.csv)). The rooms check points the
same way. In the boosting model, town × living area is the strongest of all 45 feature pairs.
- Why: probably because space costs most where land is scarcest and closest to job centres. The
  planned "bedrooms × school quality" question cannot be answered: there are no bedroom counts, and
  schools cannot be separated from town.

**Schools and taxes next to the town premium** ([`crosstown_school_context.csv`](crosstown_school_context.csv)):

| Town | MCAS % meeting/exceeding (2017–2026) | Student growth (SGP) | Spending per pupil (2016–2025) | Residential tax rate FY2025 | Town premium |
|---|---|---|---|---|---|
| Cambridge | 57% | 50 | \$32,000 | \$6.35 | reference |
| Brookline | 75% | 56 | \$22,700 | \$9.87 | −12% |
| Somerville | 42% | 48 | \$22,400 | \$10.91 | −24% |
| Newton | 73% | 56 | \$21,700 | \$9.80 | −31% |
| Arlington | 74% | 54 | \$16,300 | \$10.77 | −37% |

- **Test scores do not line up with the town premium.** Cambridge has the highest premium but
  middling scores. Arlington and Newton score about as high as Brookline but have the lowest
  premiums. So the premium is **not** a simple reflection of test scores.
- Cambridge spends the most per pupil and has by far the lowest residential tax rate. Both go with
  its premium, but so does its location next to Boston and its job centres. With five towns these
  cannot be separated: [`fig_h16`](../../figures/hedonic/fig_h16_crosstown_context.png) shows the
  points and deliberately fits no line.
- **Label: not identifiable.** These data cannot say whether schools raise prices. The boundary
  comparison in Phase 5 (homes just either side of the Cambridge–Somerville line) gets closer, but
  even there the line changes schools, taxes and services all at once.
- Tax-rate source: Massachusetts Division of Local Services, Municipal Databank. The values were
  copied by hand on 2026-11-23 (see `SOURCES.md`). Residential exemptions, which some of these
  cities offer, are not included.

Figures: [`fig_h15_crosstown_premium.png`](../../figures/hedonic/fig_h15_crosstown_premium.png),
[`fig_h16_crosstown_context.png`](../../figures/hedonic/fig_h16_crosstown_context.png).

## Overall picture after Phases 2–4

1. **Prices are explained mainly by the home itself** (size, bathrooms, condition, grade), by
   **when** it sold, and by **which town and neighborhood** it is in. Within Cambridge, crime and
   tract income add nothing measurable, in a linear model, a spatial model and a flexible
   machine-learning model alike.
2. **Space has become more valuable over time.** Suggestive in Model 2, confirmed in shape by
   Model 4. Space is also worth more in Cambridge and Brookline than in the other three towns.
3. **Transit:** a price penalty appears only for homes more than about 1 km from a station, and it
   rests largely on West Cambridge. Not established.
4. **Being in Cambridge** goes with prices 12–37% above comparable homes in the four neighbouring
   towns. That is a bundle (location, services, taxes, schools) that these data cannot take apart.
   Test scores do not line up with it.
