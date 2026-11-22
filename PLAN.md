# PLAN: What drives housing prices in Cambridge, and how do the factors interact?

*Status: draft for review (2026-11-22). Nothing has been downloaded, installed or run yet.
Decisions still open are marked **[DECIDE]**.*

---

## 1. Research question

**Main question.** Holding the home itself constant (size, type, bedrooms, age, condition), how are
Cambridge housing prices associated with **neighborhood safety, area income, transit access and
time**, and do these factors **interact**? For example, is a short walk to the T worth more for a
larger unit, or in a lower-income tract?

**Secondary question (schools).** Because Cambridge uses **Controlled Choice**, every Cambridge
address belongs to the same school district and a child's school is not set by address. So
"school district" cannot vary *inside* Cambridge and cannot be a variable in the Cambridge model.
Schools can only be studied **across towns** (Cambridge, Somerville, Arlington, Newton, Brookline),
each with its own district. This is a much weaker design. With only five districts, "school quality"
is tangled with everything else that differs between towns: tax rates, city services, housing stock
and distance to Boston. Section 5, model 5, explains how far that can go.

**What this study can and cannot say.** All main models measure **associations**. A
coefficient such as "+4% per 100 m closer to a station" means *homes near stations sell for more,
after comparing similar homes*. It does **not** mean *building a station raises prices by 4%*.
Every result in `report.md` will carry one of three labels: **association**,
**suggestive of a causal effect** (quasi-experiment, with stated assumptions) or **not
identifiable with this data**.

---

## 2. Rents, sale prices or both? **[DECIDE]**

I checked what actually exists before writing this plan:

| | Sale prices | Rents |
|---|---|---|
| Unit-level public data | **Yes.** Cambridge Property Database FY2016–FY2027 (`eey2-rv59`, 354,003 rows). Each yearly snapshot lists each parcel's latest sale price and date, plus bedrooms, living area, property class, condition and coordinates. | **No.** No free public source gives rent for individual units with their features. |
| Amount | About **830–1,350 distinct parcels sold per year at more than $1,000**, 2010–2025 (union of all snapshots). Latest snapshot, sales since 2016: about 4,640 condos, 650 luxury condos, 920 single-family, 300 two-family, 200 three-family. | Census ACS 5-year **tract medians** (about 30–35 tracts in Cambridge), plus the citywide medians already in this repo. |
| Can it support the requested models? | Yes: hedonic regression, interactions, spatial models, ML with SHAP. | Only a coarse tract-level comparison (about 30 data points in Cambridge). No bedroom or size controls at unit level. |

**Recommendation: sale prices as the main study.** Optionally add a **small tract-level rent
comparison** (ACS median gross rent against the same tract factors), clearly labeled as an
aggregate, descriptive check. A unit-level rent study is not possible with free public data.

---

## 3. Variables

| Factor | Variable(s) | Source | Level | Notes |
|---|---|---|---|---|
| **Price** (outcome) | log(sale price) | Property Database | sale | Log so effects read as % changes. Prices in nominal dollars; time handled by date effects. |
| Unit type | property class (condo, luxury condo, 1-, 2-, 3-family) | Property Database | parcel | Separate models or class fixed effects (decided after Tier-1 checks). |
| Unit size | living area (sq ft), bedrooms, full/half baths | Property Database | parcel | Characteristics taken from the snapshot closest **after** the sale, to match the home as sold. |
| Other home controls | year built, condition, grade, parking, floor/view (condos) | Property Database | parcel | Controls, not findings. |
| **Safety** | crimes per year near the home, split violent vs property | Cambridge Police *Crime Reports* (`xuad-73uj`, 102,097 rows, 2009–2026, 117 reporting areas) | reporting area | Counts are by **police reporting area**, not exact address. Busy commercial areas (Harvard Sq, Central Sq) have high counts because of visitors, not residents; a rate per resident would mislead. Plan: count per km², and a sensitivity check that leaves out commercial areas. |
| **Area income** | median household income (B19013) | Census ACS 5-year, tract | tract | Has margins of error, which will be carried through. Small queries need no API key. |
| **Transit** | walking distance to nearest MBTA rapid-transit station; optional bus-stop count within 400 m | MassGIS *MBTA Rapid Transit* (stations) and MBTA GTFS `stops.txt` (buses) | parcel | Straight-line distance first; walking-network distance is an optional refinement. |
| **Time** | sale year-quarter fixed effects | sale date | sale | Absorbs the citywide market trend (rates, booms). |
| **Location** | 13 neighborhoods (fixed effects) | Cambridge *Neighborhood Polygons* (`k3pi-9823`) | neighborhood | Compares homes **within** the same neighborhood. |
| **Schools** (cross-town only) | district MCAS growth (SGP) and achievement; per-pupil spending | MA DESE School and District Profiles | district | Growth (SGP) tracks income less closely than raw scores. Not usable inside Cambridge (Controlled Choice). |
| Town controls (cross-town only) | residential tax rate | MA DLS Municipal Databank | town | Needed because tax differences also show up in prices. |

**Other-town sales** (for models 4 and 5) would come from **MassGIS Property Tax Parcels**, which
has a standardized assessor table for every town. To confirm when downloading: field names and
the exact sale fields (expected: last sale date and price, building area, units, rooms, use code,
year built). Limits: probably **only the most recent sale per parcel**, and **no bedroom count**
(rooms instead). So cross-town models use a reduced set of home controls.

---

## 4. Data handling rules

1. **Raw data is never edited.** Every download goes into `data/raw/hedonic/` exactly as received,
   with an entry in `data/raw/hedonic/SOURCES.md` (URL, dataset ID, date downloaded, license or
   terms, row count, checksum).
2. **Privacy.** The Property Database includes **owner names and mailing addresses**. They are
   public record, but this study does not need them. **[DECIDE]** Proposal: keep the raw files
   only on your computer (git-ignored, re-creatable with a fetch script), and drop owner columns at
   the first cleaning step, so no owner names ever reach GitHub. This also keeps large files
   (the property file is likely 100+ MB) out of the repo.
3. **Cleaning is scripted and logged.** Each step in `analysis/hedonic/10_clean_sales.py` writes a
   line to `results/hedonic/cleaning_log.csv`: *step, rule, rows before, rows after, rows removed*.
   Planned rules (each documented, with counts reported):
   - Drop **non-market sales**: price ≤ $1,000 (the $0/$1 transfers: about 10,700 parcels in the
     latest snapshot alone).
   - Flag likely non-arm's-length sales: price below 10% of the assessed value, or many units sold
     for one total price (same book/page and date). Report results with and without these.
   - Keep residential classes only (condo, luxury condo, 1–3 family; 4–8-unit apartments only if
     enough sales).
   - De-duplicate sales that appear in several yearly snapshots (same parcel, date and price).
   - Trim extreme price per sq ft (top and bottom 0.5%) **only as a sensitivity check**, never
     silently.
   - Every threshold is fixed **before** looking at regression results.
4. **Cleaned data** goes in `data/processed/hedonic/` (no owner fields), with a data dictionary.

---

## 5. Models (in this order)

Each model gets a plain-language explanation in `report.md`. The order goes from simplest and most
transparent to most flexible.

### Model 1: Hedonic regression on log(price)
**In plain words:** a home's price is treated as the sum of the values of its parts (space,
bedrooms, location, safety and so on). The regression estimates what each part is "worth" on
average, comparing homes that are alike in everything else. With log price, each estimate reads as
"about X% higher price".

- log(price) = home features + crime + tract income + transit distance + **neighborhood fixed
  effects** + **year-quarter fixed effects** + error.
- **Neighborhood fixed effects** mean each home is compared only with homes in its own neighborhood,
  so "Cambridgeport is pricier than Alewife" does not get mixed into the estimates.
- **Clustered standard errors.** Homes in the same area share unmeasured traits, so their errors are
  not independent. Plan: cluster by **census tract** (about 30 clusters). As a robustness check,
  cluster by the 13 neighborhoods using a *wild cluster bootstrap*, because 13 clusters are too few
  for ordinary cluster formulas.
- **Multicollinearity check before interpreting anything.** Income, crime and transit are
  correlated. Steps: correlation matrix, variance inflation factors (VIF), and a "drop one, see what
  changes" table. If two factors cannot be separated, the report says so instead of over-reading
  either coefficient.

### Model 2: Interaction terms
**In plain words:** an interaction asks whether one factor's value *depends on* another. Example:
"Is being near the T worth more in a lower-income tract than a higher-income one?"

- Planned interactions (fixed in advance, to avoid fishing): **income × transit**,
  **bedrooms × transit**, **crime × income**, **living area × year** (did space become more
  valuable after 2020?).
- **bedrooms × school quality** only works across towns (model 4), since school quality does not
  vary within Cambridge.
- Shown as plots (predicted price across one factor, at low, middle and high levels of the other),
  with confidence bands.

### Model 3: Spatial autocorrelation check and spatial model if needed
**In plain words:** nearby homes tend to have similar prices for reasons the model may miss (a park,
a noisy road). If the model's errors cluster on a map, ordinary uncertainty estimates are too
optimistic. **Moran's I** measures that clustering: 0 means no pattern, positive means similar
errors sit next to each other.

- Compute Moran's I on model 1 residuals (k-nearest-neighbor weights; k = 8, checked with k = 5 and 15).
- If it is clearly positive: Lagrange-multiplier tests choose between a **spatial error model**
  (shared unmeasured local factors) and a **spatial lag model** (prices influence neighbors'
  prices), estimated with PySAL. Compare coefficients with model 1.

### Model 4: Gradient boosting with SHAP values
**In plain words:** a flexible machine-learning model that finds non-linear patterns and
interactions on its own, without being told which to look for. **SHAP values** then break each
prediction into contributions from each factor, and *SHAP interaction values* show which pairs of
factors work together.

- Gradient boosting (scikit-learn or LightGBM). **Spatial cross-validation** by neighborhood, so the
  model is tested on areas it has not seen and does not just memorize location.
- Used to **explore and cross-check** the interactions from model 2, not as the source of headline
  numbers. SHAP explains what the model learned, which is **association, not cause**.
- A cross-town version (5 towns, MassGIS data) can add district school measures. With five
  districts, any "school" pattern cannot be told apart from "town" (taxes, services, location).
  The report will state that explicitly.

### Model 5 (if the data allows): Boundary comparison at a town line
**In plain words:** compare similar homes just on either side of a town line, for example a few
hundred meters apart across the **Cambridge–Somerville** border. The neighborhood is nearly the
same, but the town (and its schools, taxes and services) changes at the line.

- Sales within 250–500 m of the line, with boundary-segment fixed effects and distance-to-line
  controls.
- **Main caveat:** the line changes a **whole bundle** of things at once: school district, the tax
  rate (Cambridge's residential rate is low), trash and snow services, parking rules. So a price
  jump at the line is the value of *being in Cambridge*, not of schools alone. Somerville's school
  assignment rules also need checking before any school interpretation.
- Feasibility depends on how many comparable sales lie near the line and on matching the two towns'
  data fields. I will report the counts before running it.

### Optional extras (only if you want them)
- **Green Line Extension (GLX), opened 2022:** compare price changes before and after the opening for
  homes near the new stations versus similar homes farther away (difference-in-differences). This
  is the closest thing to a natural experiment for transit in the area. **[DECIDE]**
- **Repeat sales:** homes sold more than once let each home serve as its own control, which removes
  unmeasured quality differences.
- **Tract-level rent comparison** (Section 2).

---

## 6. Uncertainty and honesty rules

- Every estimate is reported with a **95% confidence interval**, never a bare point estimate.
- Robustness table for each headline result: different clustering, with/without flagged sales,
  with/without commercial-area crime, spatial versus non-spatial model.
- Interactions and models are chosen **before** seeing results (this plan). Anything added later is
  labeled *exploratory*.
- Each conclusion in `report.md` is labeled **association**, **suggestive of causal**, or **not
  identifiable**.

---

## 7. Outputs and folder layout

The existing project is kept as is. The new study gets its own subfolders:

```
cambridge-rent-sources/
├── PLAN.md                         this file
├── report.md                       short report for a non-technical audience (city councilors)
├── analysis/hedonic/               numbered scripts, each explained in a comment block
│   ├── 00_fetch_data.py            downloads raw data, records sources and checksums
│   ├── 10_clean_sales.py           cleaning rules, writes cleaning_log.csv
│   ├── 20_build_features.py        crime, income, transit distance, neighborhoods per sale
│   ├── 30_hedonic_ols.py           models 1–2 (+ VIF)
│   ├── 40_spatial.py               model 3 (Moran's I, spatial models)
│   ├── 50_boosting_shap.py         model 4
│   └── 60_boundary.py              model 5 (if feasible)
├── data/raw/hedonic/               unedited downloads (git-ignored) + SOURCES.md
├── data/processed/hedonic/         cleaned data, no owner fields, + data dictionary
├── results/hedonic/                tables (CSV), cleaning log
└── figures/hedonic/                charts (PNG + PDF)
```

**Software [DECIDE]:** Python packages needed: pandas, geopandas, statsmodels, PySAL (libpysal,
esda, spreg), scikit-learn, shap, matplotlib, plus LightGBM optionally. They would go in a
project-local environment (`.venv/` inside the repo, managed by `uv`). uv also keeps a download
cache in your home folder, which is *outside* the project, so I need your OK before installing.
No paid services. Nothing is pushed to GitHub.

---

## 8. Timeline

Each phase ends with a checkpoint where you review results before the next starts. The durations
are working sessions, not calendar weeks; the real limit is your review time.

| Phase | Work | Checkpoint (what you get) |
|---|---|---|
| **0. Setup** | Pick the repo copy, `git init` locally, create environment | Folder layout and empty scripts |
| **1. Data** | Download all sources, record SOURCES.md, cleaning with log | Cleaning log, data dictionary, basic maps and summary tables |
| **2. Model 1** | Hedonic regression, VIF and correlation checks | Coefficient table with CIs, plain-language summary |
| **3. Models 2–3** | Interactions, Moran's I, spatial model if needed | Interaction plots, residual map, comparison table |
| **4. Model 4** | Gradient boosting, spatial CV, SHAP | SHAP summary and interaction plots |
| **5. Model 5 / extras** | Boundary feasibility counts, then model if feasible; GLX if chosen | Feasibility note, then results |
| **6. Report** | `report.md`: findings, uncertainty, limits, correlation vs causation | Draft report and figures for presentation |

---

## 9. Known limitations (stated up front)

- **Assessor characteristics** describe the home at assessment time, not necessarily at sale.
  Renovations between the two are a source of error.
- **Selection:** homes that sell are not a random sample of all homes.
- **Crime** is recorded by reporting area and reflects reporting behavior, not just risk.
- **ACS income** is a 5-year average with margins of error, and is strongly linked to price itself
  (high prices attract high incomes), so it cannot be read as a cause.
- **Schools** cannot be studied within Cambridge (Controlled Choice). Across five towns, they are
  bundled with taxes and services.
- **Data sources checked on 2026-11-22.** Cambridge Open Data catalog and dataset metadata (row
  counts above); MassGIS Property Tax Parcels and MBTA Rapid Transit pages; DESE Profiles. Exact
  MassGIS field names and Somerville school assignment rules are **still to confirm**.
