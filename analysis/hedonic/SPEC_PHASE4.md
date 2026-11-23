# Pre-specification for Phase 4 (Model 4: gradient boosting with SHAP; cross-town comparison)

*Written and committed on 2026-11-22, **before** any Phase 4 model was run. Phase 2–3 results
were known when this was written. Model 4 as described in PLAN.md section 5. Anything beyond
PLAN.md is marked **check** or **exploratory**. Changes after seeing results go at the bottom.*

**Role of this model (from PLAN.md):** gradient boosting is used to **explore and cross-check**
Models 1–2, not as the source of headline numbers. SHAP explains what the model learned. That is
**association, not cause**.

---

## Part A: Cambridge (Model 4)

### Sample and features
- **Sample:** `market_sample`: 8,823 sales. This is the Model 1 sample without the likely
  deed-restricted sales, as decided on 2026-11-22.
- **Target:** log(price).
- **Features:** the same information as Model 1 and no new variables.
  - Home: home type, log living area, bedrooms, full baths, half baths, parking, year built (as a
    number; unknown = missing), condition, grade.
  - The four headline factors: violent and property crime within 500 m, log tract income, distance
    to the nearest station.
  - Time: sale date as a decimal year (for example 2019.5).
- **Three versions:**
  - **G1 (main, as in PLAN.md):** the features above, with **no location identifiers**. The model has
    to explain location through crime, income and transit. Its SHAP values therefore mix
    differences *between* neighborhoods with differences *within* them, unlike Model 1.
  - **G2 (check, comparable to Model 1):** G1 plus neighborhood as a categorical feature. Like
    Model 1, it compares homes within a neighborhood.
  - **G3 (check):** G1 plus map coordinates (x, y in metres). It shows how much price variation is
    tied to location beyond the measured factors.

### Algorithm (settings fixed now, not tuned on results)
scikit-learn `HistGradientBoostingRegressor` with these settings:
- squared-error loss
- learning rate 0.05
- `max_leaf_nodes` 31
- `min_samples_leaf` 20
- `l2_regularization` 1.0
- `max_iter` 3000, with early stopping: 10% internal validation split, stop after 50 rounds without
  improvement
- `random_state` 0
- native handling of categorical features

### Validation (spatial cross-validation)
- **G1 and G3:** **leave one neighborhood out** (12 folds). The model is always tested on a
  neighborhood it never saw.
- **G2:** a held-out neighborhood would be a category it never saw, so G2 instead holds out
  **census tracts** (10 folds grouped by tract).
- **Random 10-fold** for every version, to show how much ordinary cross-validation overstates
  accuracy.
- **Benchmarks on the same folds:**
  - OLS with the same features (log-linear, categorical features as dummies).
  - For G2, Model 1 itself (OLS with neighborhood and sale-quarter fixed effects).
- **Metrics** (out of fold): RMSE of log price, R², median absolute % price error. Each is reported
  with its spread across folds.

### SHAP (models fitted on all 8,823 sales; G1 and G2)
- **Method:** `shap.TreeExplainer`, exact for trees. A verification script checks additivity: the
  contributions plus the baseline must add up to each prediction.
- **Importance:** mean |SHAP| for each feature. **Dependence plots** for the four headline factors,
  log area and sale date.
- **Comparable "typical change" number:** the **partial-dependence contrast**. It is the average
  predicted price with a factor set to its 75th percentile minus the average with it set to its
  25th percentile, expressed as a % (the same 25th → 75th percentile change as Model 1).
- **Uncertainty:** 30 refits on **neighborhood-cluster bootstrap** samples (draw the 12
  neighborhoods with replacement), each with the fixed settings. For each refit:
  - the partial-dependence contrast;
  - each dependence curve, binned on a common grid.
  
  Report the 2.5th–97.5th percentile range across refits, and how often each feature ranks in the
  top 5. With only 12 neighborhoods these ranges are rough.
- **Interactions:** SHAP interaction values on a random subsample of 2,000 sales (seed 20261122).
  - Rank all feature pairs by mean |interaction|, and report where the four planned Model 2 pairs
    fall: income × transit, bedrooms × transit, violent crime × income, and living area × sale
    date (I4 used before/after COVID; here time is continuous).
  - One figure per planned pair: interaction value against the first factor, coloured by the
    second.
  - Compare the direction with Model 2.

---

## Part B: cross-town comparison (5 towns)

**In plain words:** Cambridge assigns schools by Controlled Choice, so school quality does not vary
with address inside the city. Comparing Cambridge, Somerville, Arlington, Newton and Brookline adds
district-level differences. **With five districts, a "school" pattern cannot be told apart from
"town"** (taxes, services, location, housing stock). The report states this explicitly. Schools
are shown **next to** the town price differences, not regressed on them.

### Data (all downloaded in Phase 1; nothing new)
- **MassGIS L3 parcels** for the 5 towns: the assessor table gives each property's **last sale
  only**; the tax-parcel polygons (joined on `LOC_ID`, centroid) give its location. Owner fields
  are never read.
- ACS tract income (same file as Model 1).
- Distance to the nearest MBTA rapid-transit station: all stations in the feed, including Green
  Line stops in Brookline and Newton, with GLX stations gated by opening date. This is the same
  rule as `transit_km_allstations`.
- DESE MCAS and per-pupil spending (Phase 1 files).
- **Residential tax rates** (FY2025, per $1,000), entered by hand from the Massachusetts Division of
  Local Services (DLS) Municipal Databank, with the URL and date recorded. These are context only.

### Cleaning (each step logged with rows before and after, as in `cleaning_log.csv`)
1. Last sale on or after 2016-01-01, price above $1,000.
2. Residential use codes: 101 single-family, 102 condo, 104 two-family, 105 three-family (first
   three digits of `USE_CODE`).
3. Drop multi-parcel sales: the same town, deed book, page and date on more than one record.
4. Drop sales below 10% of the current total assessed value.
5. Living area (`RES_AREA`) between 300 and 10,000 sq ft.
6. Drop likely deed-restricted sales with the Phase 3 rule: price per sq ft and assessed value per
   sq ft both below half the median for the same town and home type (price: also the same sale
   year).
7. A location was found (parcel polygon), and the tract has an ACS income estimate.

- **Source check:** Cambridge appears both here and in the Cambridge assessor data used in
  Phases 2–3. Cambridge MassGIS last sales are matched to the city's sales on parcel and date, and
  the agreement of prices is reported.
- **Selection caveat** (stated in the report): last sale only, so a home that sold in 2017 and
  again in 2023 appears only once, for 2023. The sample leans towards recent sales.

### Features
Home type; log living area; rooms (`NUM_ROOMS`, 0 treated as missing, capped at 15); year-built
group (same bins as Model 1); log lot size for houses (0 for condos, plus a condo indicator);
distance to station; log tract income; sale quarter; town. MassGIS has **no bedrooms, bathrooms,
condition or grade**, so this model is coarser than Model 1.

### Models
- **C1 (main): hedonic OLS.** log(price) ~ home features + transit + log income + **town** (Cambridge
  = reference) + sale-quarter fixed effects. Standard errors are clustered by census tract.
  - The **town premium** is the % price difference against Cambridge for a comparable home, with a
    95% CI. It is a **bundle**: schools, taxes, services, location and amenities not in the data.
  - Check: without tract income. Income partly reflects the same amenities, schools included.
- **C2 (planned "bedrooms × school", adapted):** there are no bedroom counts, so the space premium is
  allowed to differ by town: log living area × town, with a joint Wald test. Check: rooms × town,
  where rooms are recorded. The question is whether space is worth more in some towns. Any link to
  schools is again not identifiable.
- **C3 (check): gradient boosting** with the same features and town as a category, the Part A
  settings, and cross-validation grouped by tract. Outputs: SHAP for town, and the SHAP interaction
  of town × living area.
- **School context table** (5 rows), shown alongside the C1 town premiums:
  - MCAS % meeting or exceeding expectations and average student growth (SGP). These cover all
    students, ELA and Math, grades "ALL (03-08)" and 10, averaged over school years 2017–2026 (no
    2020 test).
  - In-district spending per pupil, averaged over 2016–2025.
  - FY2025 residential tax rate.
  - A 5-point figure: town premium against each measure. **No regression line**, and labeled
    "five towns: not evidence of a school effect".

---

## Files
- `50_boosting_shap.py` (Part A)
- `55_crosstown_build.py` (Part B, data)
- `56_crosstown_models.py` (Part B, models)
- `verify_shap.py`: SHAP additivity; partial-dependence contrast against a known synthetic model; no
  overlap between training and test folds.
- Outputs: `results/hedonic/model4_*.csv` and `crosstown_*.csv`; figures `fig_h11` onward;
  `data/processed/hedonic/crosstown_sales.csv` with an added section in the data dictionary.

## Changes after seeing results

- **Categorical features coded as numbers, not with native categorical splits.** Found in a
  tooling test *before* any model ran on the real data. SHAP's `TreeExplainer` gives wrong values
  for scikit-learn's native categorical splits: in a synthetic test, the contributions did not add
  up to the predictions (error of 7.6 on the log scale). So condition and grade are coded in their
  natural order, and home type and neighborhood as 0/1 columns. SHAP values of the 0/1 columns are
  summed back up to one value per feature. Check 2 of `verify_shap.py` documents this.
- **Cross-town cleaning step 8** (implementation detail): 41 sales with no recorded rooms, or with
  no lot size for a house, are dropped. The spec treated rooms = 0 as missing but did not say what
  to do with missing values.
- **Tax rates:** the DLS report could not be fetched by script (HTTP 403), so it was read in a web
  browser on 2026-11-23 and the values were copied by hand into
  `data/raw/hedonic/manual/dls_tax_rates_by_class.csv`, with a note in `SOURCES.md`.
- **Diagnostic for the G2 cross-validation** (after seeing results). The linear benchmark scored
  0.30 in one tract fold. In that fold Baldwin's only tract was held out, so the neighborhood was
  absent from training. A second fold had the same issue for Strawberry Hill. This is reported in
  the summary. No numbers were changed.
- `fig_h11` was redrawn after seeing it, with shorter axis labels; only the labels changed. It was
  redrawn from `model4_cv.csv` using the same figure code; rerunning `50_boosting_shap.py` produces
  the same figure.
- **Transit far-distance pattern** (exploratory): the share of sales more than 1.2 km from a station
  that are in West Cambridge was counted after seeing the SHAP curve.
