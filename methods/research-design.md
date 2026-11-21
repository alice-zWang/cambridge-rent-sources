# Research design

## Starting topic

Make it easier for people moving to Cambridge, MA for school or work to understand rent, by comparing several sources and identifying the most reliable and reasonable prices.

## Evaluation of the starting topic

| Criterion | Rating | Why |
|---|---|---|
| Specificity | Low | "Most reliable and reasonable" was undefined, and so were housing type, time period and audience. |
| Feasibility | Medium | Rent data exists, but each source measures something different, and scraping listing sites can break their terms of service. |
| Originality | Low as stated | Rental sites already aggregate prices. Explaining *why* sources disagree is the less-covered question. |
| Theoretical contribution | Weak as stated | Building a tool tests nothing on its own. The contribution comes from explaining gaps between sources. |

## Refined questions

1. **Source comparison (chosen).** How much do Cambridge rent estimates differ across the City of Cambridge, HUD, the Census and listing sites, and what explains the gaps?
   *Method:* match sources by year and bedroom count; measure the gaps; test the city–HUD gap with a paired t-test; code each source's documentation for how it measures rent.
2. **Rent prediction.** Can listing features (size, bedrooms, distance to transit or campus, building age) predict asking rent?
   *Method:* hedonic regression plus a gradient-boosting model, with cross-validation.
3. **Newcomer affordability.** How has rent burden changed since 2015 for graduate students and entry-level workers?
   *Method:* descriptive time series of rent divided by stipend or entry-level wage, against the 30% rent-burden line.

## What this repository covers

- A t-test for the slope of a regression line on the city's rent data, 2010–2025 ([analysis/01_rent_trend_tests.py](../analysis/01_rent_trend_tests.py))
- A seven-source comparison and a city-vs-HUD paired comparison ([analysis/02_compare_sources.py](../analysis/02_compare_sources.py))
- Asking rent (city listings) vs. rent paid by all renters (Census), by bedroom count ([analysis/03_asked_vs_paid.py](../analysis/03_asked_vs_paid.py))
- A deductive coding framework for the documentation of 10 city housing datasets ([coding-framework.md](coding-framework.md))
- An ethics checklist ([ethics-checklist.md](ethics-checklist.md)) and a positionality statement ([positionality.md](positionality.md))

## Planned next steps

- Add Zillow's Observed Rent Index history (Census rent by bedroom count was added in Nov 2026)
- Test why the city's asking-rent series grew far less than HUD and Census rents
- Add neighborhood-level rents from the city's Rental Housing Cost Tracker
- Have a second coder apply the codebook to 2–3 datasets and compare results
- Ask the Cambridge Community Development Department which listing sources feed its rent figures
