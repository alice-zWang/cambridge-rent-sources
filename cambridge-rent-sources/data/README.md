# Data

All files in `raw/` were collected on **November 17–21, 2026**. Figures copied from websites are snapshots and will not update. `processed/` is rebuilt by `analysis/run_all.py`.

## raw/

### `cambridge_median_rents_2010_2025.csv`
City of Cambridge, Community Development Department, *Median Residential Rents 2010 – Present* (dataset `n9xk-8wft`), [data.cambridgema.gov/d/n9xk-8wft](https://data.cambridgema.gov/d/n9xk-8wft). Last updated Dec 12, 2025.
Median advertised rent for market-rate apartments, citywide, one value per year (September; January in 2010 and August in 2011). Excludes affordable housing and university graduate housing ([city housing data page](https://cambridgema.gov/CDD/factsandmaps/housingdata)).

| Column | Meaning |
|---|---|
| `year`, `month` | When the value was collected |
| `nominal_{1,2,3}br_median_rent` | Median monthly rent in dollars of that year |
| `cpi_adjusted_{1,2,3}br_median_rent` | Same, converted by the city to Sept 2025 dollars using the CPI |

### `cambridge_open_data_metadata.csv`
Documentation text for 10 housing-related datasets on the Cambridge Open Data portal (description, publisher, update frequency, stated limitations). This is the corpus for the [coding framework](../methods/coding-framework.md).

### `rent_snapshot_all_sizes.csv`
"Typical" Cambridge rent for all apartment sizes from seven public sources, with the measure (median or average), date, geography, who is counted and whether utilities are included. Each row has its source URL.

### `rent_snapshot_by_bedroom.csv`
Rent by bedroom count from the City of Cambridge (Sept 2025), HUD Fair Market Rents (FY2026), Zillow (2025) and Apartments.com (May 2026).

### `hud_fmr_boston_metro.csv`
HUD Fair Market Rents for the Boston-Cambridge-Quincy, MA-NH HUD Metro FMR Area, 1–3 bedrooms, for the fiscal years found in published schedules (FY2014, 2015, 2017–2021, 2024–2027). A fiscal year starts on October 1 of the previous calendar year. Each row lists the document it came from.
Notes: FMRs are 40th-percentile gross rents (including utilities) across about 112 towns. HUD later revised the FY2025 figures; the original values are used here. FY2027 values come from a secondary summary, not a HUD document.

## processed/

### `city_vs_hud.csv`
City September values (year *t*) paired with the HUD fiscal year that starts the following October (FY *t*+1).

## Terms

City of Cambridge and federal (HUD, Census) data are public. Figures from commercial sites (Zillow, Apartments.com, Zumper, Redfin, RentCafe, Point2) are single published summary numbers cited for comparison; see each site's terms for reuse of their data.
