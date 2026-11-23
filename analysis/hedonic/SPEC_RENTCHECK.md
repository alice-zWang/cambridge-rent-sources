# Pre-specification: small tract-level rent check (PLAN.md section 2)

*Written and committed on 2026-11-23, before the rent check was run. You chose "Sales + small rent
check" in Phase 0, and this is that check.*

**In plain words:** no free source gives the rent of individual apartments with their features. The
Census does give each census tract's **median gross rent** (ACS 2020–2024, table B25064). This check
asks whether tracts with more crime, higher income or closer stations have higher rents. It is a
**descriptive** comparison of about 31 numbers, not a model of individual homes.

- **Unit:** the Cambridge census tracts that contain at least one sale in `market_sample` and
  report a median gross rent.
- **Outcome:** log median gross rent. Its margin of error is reported, and tracts where the margin
  of error exceeds 20% of the estimate are flagged.
- **Tract factors:** the same as the sales models, summarized per tract over sales from 2020 to
  2024, the years the ACS estimate covers.
  - mean violent crime and mean property crime within 500 m;
  - mean distance to station;
  - log tract median household income (ACS).
- **Price comparison:** tract median sale price per sq ft, condos only (`market_sample`, 2020–2024).
  It is used as a check of whether rents and sale prices rank tracts the same way.
- **Analyses:**
  1. Spearman correlations of log rent with each factor and with price per sq ft.
  2. Regression of log rent on each factor alone, then on all four together, with HC3 standard
     errors (suited to small samples).
  3. A check: the same regressions without flagged tracts (margin of error above 20%).
- **Labels:** association only. With about 31 tracts, an all-factor regression has little power.
  Tract income and rent are linked by construction: renters' incomes are part of tract income.
- **Outputs:** `results/hedonic/rentcheck_*.csv`, figure `fig_h19_rent_check`. Script:
  `analysis/hedonic/70_rent_check.py`.

## Changes after seeing results

- One tract has no published margin of error. It is kept, and counted as not flagged.
