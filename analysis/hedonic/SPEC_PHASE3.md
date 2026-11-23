# Pre-specification for Phase 3 (Model 2: interactions; Model 3: spatial)

*Written and committed on 2026-11-22, **before** any Phase 3 model was run. Phase 2 results were
known when this was written; the pre-registered interactions below are the four listed in
PLAN.md (written before any data was seen). Anything added beyond PLAN.md is marked
**exploratory**. Changes after seeing results go at the bottom.*

Sample, features and base model: exactly Model 1 (`SPEC_MODEL1.md`), 9,024 sales.

## Model 2: interactions

**In plain words:** does one factor's association with price depend on another factor?

Continuous variables are **centred** at their sample mean before multiplying, so the main
effects keep their Model 1 meaning (the association at an average value of the other factor).

| ID | Interaction (from PLAN.md) | Variables |
|---|---|---|
| I1 | income × transit | log(tract income) × distance to station (km) |
| I2 | bedrooms × transit | bedrooms × distance to station (km) |
| I3 | crime × income | violent crime (500 m) × log(tract income) |
| I4 | living area × time | log(living area) × after-COVID (sale on or after 2020-04-01) |

- Violent crime is used in I3 because violent and property crime cannot be separated well
  (correlation 0.72 within neighborhoods, Phase 2). Check: I3 with property crime.
- Each interaction is added **on its own** to Model 1 (one change at a time). Check: all four
  together.
- I4 is also shown year by year (log living area × sale year, 2016 = reference), as a figure.
- Inference: standard errors clustered by census tract (31), and the wild cluster bootstrap by
  neighborhood (12 clusters, Webb weights, 9,999 draws, `wildboot.py`) for each interaction term.
  Because four interactions are tested, bootstrap p-values are also given with the **Holm**
  correction for multiple testing.
- Figures: for I1–I3, the price difference for a typical low → high change (25th → 75th
  percentile) in the first factor, at low, middle and high values (10th, 50th, 90th percentile) of
  the second factor, with 95% ranges. For I4, the living-area coefficient by year.

**Exploratory (not in PLAN.md; suggested by Phase 2):**
- E1: transit × house (single-, two- or three-family vs condo).
- E2: E1 without West Cambridge (the neighborhood that drove the Phase 2 transit estimate).

## Model 3: spatial autocorrelation

**In plain words:** if the model's leftover errors are similar for homes that are close
together, something local is missing from the model and its uncertainty is understated.

**Weights.** Each sale's neighbours are its **8 nearest other sales** (row-standardised), checked
with 5 and 15. Many condo sales share a location: 9,024 sales sit on 3,606 distinct points, because
units in one building share the parcel's coordinates. So the nearest neighbours of a condo sale are
often other units in the same building, and Moran's I partly measures a **"same building"** effect.
Two checks separate the two:
- the share of residual variance that lies between locations, not within them;
- Moran's I on residuals **averaged per location** (3,606 points, 8 nearest other locations).
  This measures clustering **between buildings**.

Coincident points are kept as they are. If the software refuses them, the points are jittered by
at most 0.5 m, with a fixed random seed, and that is reported.

**Moran's I** on Model 1 residuals, with a permutation test (999 permutations).

**Rule for the spatial model** (Anselin's standard decision rule):
- If Moran's I is positive with permutation p < 0.01, run the Lagrange-multiplier (LM) tests
  for a spatial error and a spatial lag model, both classic and robust.
- If only robust LM-error is significant (p < 0.01): spatial error model. If only robust
  LM-lag: spatial lag model. If both: fit both and the combined model (SARAR), and report all.
- Estimators: GMM, robust to heteroskedasticity (Kelejian–Prucha; PySAL `spreg`
  `GM_Error_Het`, `GM_Lag` with White errors, `GM_Combo_Het`), with the same regressors and fixed
  effects as Model 1.
- For a lag model, report **total impacts** (direct + spill-over), not raw coefficients.
- Comparison table: the four headline estimates in Model 1 against the spatial model(s), and
  Moran's I of the spatial model's residuals.
- Limitation stated up front: `spreg` standard errors are not clustered.

**Figures:** map of Model 1 residuals averaged per location; Moran scatterplot.

## Changes after seeing results

- **Spatially filtered OLS with clustered inference** (`40_spatial.py`). `spreg`'s standard errors
  are not clustered, so the spatial error model was re-estimated as OLS on spatially filtered
  data (y − λWy on X − λWX, with λ from the GMM model), using Model 1's tract clustering and the
  neighborhood wild bootstrap. The coefficients match the GMM error model.
- **Likely deed-restricted sales** (`20_build_features.py`, `45_restricted_check.py`). Model 1
  residuals revealed 201 sales (76 addresses, mostly condos) whose price and assessed value are
  both below half the median per sq ft for their home type and year. This is the pattern of
  deed-restricted affordable homes, which are not market sales. They are flagged, not removed:
  `model_sample` is unchanged and all pre-specified results use it. Models 1–3 were re-run
  without them as a robustness check. The 0.5 threshold was chosen after looking at the
  distribution: a clear low group below about 0.35, then a gap up to about 0.6.
- Shared model definitions moved to `model_common.py`. Model 1 outputs are byte-identical after
  the move.
