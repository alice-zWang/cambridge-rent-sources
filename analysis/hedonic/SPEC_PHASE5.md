# Pre-specification for Phase 5 (Model 5: Cambridge–Somerville boundary comparison)

*Written and committed on 2026-11-23, after the feasibility counts (`60_boundary_feasibility.py`)
and **before** any boundary model was run. The counts include each side's raw average log price
(balance table), but no model estimate.*

## Feasibility (counts only)

- **The line.** The Cambridge outline (union of the city's neighborhood polygons), kept where
  Somerville parcels lie within 60 m. It is one piece, 7.7 km long, running from Alewife/Davis in
  the northwest to East Cambridge/Inner Belt in the east
  ([`fig_h17`](../../figures/hedonic/fig_h17_boundary_map.png)). No sale was placed on the wrong
  side of it.
- **Data.** MassGIS last-sale data for both cities (`crosstown_sales.csv`), so both sides have the
  same fields. Somerville's file ends on 2024-07-31 and Cambridge's on 2025-07-31.
- **Counts** (`boundary_counts.csv`):

  | Distance from line | Cambridge | Somerville |
  |---|---|---|
  | within 100 m | 342 | 504 |
  | within 250 m | 1,047 | 1,058 |
  | within 500 m | 2,125 | 1,793 |

  About 77% of these are condos on both sides.
- **Segments.** Of the eight 1 km segments, 7 have at least 20 sales on each side within 250 m
  (`boundary_segments.csv`). The easternmost stretch borders mostly rail and industrial land on the
  Somerville side.
- **Balance within 250 m** (`boundary_balance.csv`). Cambridge homes near the line are somewhat
  smaller (standardized difference −0.32 in log area). They are closer to a station (0.62 vs
  0.79 km; −0.49) and sold later on average, because Somerville's file ends a year earlier.
  Tract income is similar (+0.06). So the model must control for size, transit and sale date.

**Verdict: feasible.** About 1,000 sales per side within 250 m, spread along most of the line.

## Schools on each side (checked 2026-11-23)

- **Both cities use Controlled Choice, not address zones.**
  - *Somerville:* families rank up to five K-8 schools, and only Somerville residents may apply.
    Priority for the first-choice school goes to siblings, then to families living near that school
    (by the district's street directory). Source:
    <https://www.somerville.k12.ma.us/schools/enrollment/school-assignment/>.
  - *Cambridge:* Controlled Choice since 1980. Family choices are balanced against equity,
    socio-economic and enrollment goals. Source: <https://www.cpsd.us/fs/pages/5196>.
- **So crossing the line changes which district's schools a family may choose from, not a fixed
  assigned school.** It also changes the tax rate (FY2025 residential: Cambridge \$6.35, Somerville
  \$10.91 per \$1,000; DLS), city services and parking rules. **A price jump at the line is the
  value of the whole "Cambridge bundle", not of schools alone.**

## Model 5 (pre-specified)

**Sample.** Sales within **250 m** of the line, sold 2016-01-01 to **2024-07-31**. That is the window
both cities cover, so the comparison covers the same period on both sides.

**B1 (main):**

log(price) = β · Cambridge + home features + distance to the line (separate slope on each side)
+ 1 km segment fixed effects + sale-quarter fixed effects + distance to station + error

- Home features are as in cross-town model C1: home type, log living area, rooms, year-built
  group, and log lot size for houses.
- **β** is the price jump at the line, reported as a % (exp(β) − 1).
- Tract income is **not** controlled in the main model. Income can be a result of being in
  Cambridge, so controlling for it would remove part of the jump.
- **Inference:**
  - Standard errors clustered by census tract.
  - Wild cluster restricted bootstrap by tract (Webb weights, 9,999 draws; `wildboot.py`).
  - The more cautious interval is the headline.

**Checks (each changes one thing from B1):**
1. Within 100 m; within 500 m.
2. Adding log tract income.
3. Without distance to station.
4. Condos only.
5. **Placebo lines.** The same model on a fake line drawn 400 m *inside* Cambridge (Cambridge sales
   only), and on one 400 m inside Somerville (Somerville sales only). Here a jump should be about
   zero; a clear jump would mean the main estimate picks up a smooth price gradient, not the city
   line.
6. Without the easternmost segment.

**Tax-only benchmark (to bound expectations).** How large a jump could the tax difference alone
explain? Each year's tax saving is (10.91 − 6.35)/1000 = 0.456% of assessed value. Valued as a
permanent saving at 4% or 6% a year, that is 0.456/4 = 11.4% or 0.456/6 = 7.6% of value.
- Assumptions: FY2025 rates; assessed value ≈ price; residential exemptions ignored, because
  they were not checked.
- This only puts the estimate in context; it is not tested. If the jump is close to this range,
  the tax difference alone could account for it.

**Interpretation labels.**
- The jump is labeled **suggestive of causal** for "being in Cambridge rather than Somerville", for
  homes near this line.
- It is labeled **not identifiable** for schools specifically.

## Files
- `60_boundary_feasibility.py` (counts; done)
- `65_boundary_model.py` (B1, checks, placebos)
- Outputs: `results/hedonic/boundary_model.csv`; figure `fig_h18` (average price by distance to the
  line on each side, adjusted for home features)

## Changes after seeing results
*(none yet)*
