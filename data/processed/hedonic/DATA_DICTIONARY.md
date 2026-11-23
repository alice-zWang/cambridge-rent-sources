# Data dictionary: `sales_clean.csv`

Built by `analysis/hedonic/10_clean_sales.py` from the Cambridge Property Database (see `data/raw/hedonic/SOURCES.md`). One row per market sale. Owner names and addresses were removed. Cleaning steps and row counts: `results/hedonic/cleaning_log.csv`.

| Column | Meaning | Non-missing |
|---|---|---|
| `pid` | Cambridge parcel ID (condo units have their own ID) | 9,236 |
| `address` | Street address | 9,236 |
| `unit` | Unit number (condos) | 7,054 |
| `latitude` | Latitude (WGS84) | 9,236 |
| `longitude` | Longitude (WGS84) | 9,236 |
| `propertyclass` | Assessor property class, as published | 9,236 |
| `group` | Analysis group: condo, condo_lux, single_family (incl. with auxiliary apartment), two_family, three_family | 9,236 |
| `saledate` | Sale date (YYYY-MM-DD) | 9,236 |
| `sale_year` | Calendar year of sale | 9,236 |
| `sale_quarter` | Calendar quarter of sale (e.g. 2021Q3), used for time fixed effects | 9,236 |
| `saleprice` | Recorded sale price, US$ (nominal) | 9,236 |
| `log_price` | Natural log of saleprice | 9,236 |
| `price_per_sqft` | saleprice / interior_livingarea | 9,236 |
| `book_page` | Registry of Deeds book/page of the sale | 9,236 |
| `yearofassessment` | Fiscal-year snapshot the home's features were taken from (first snapshot that shows this sale) | 9,236 |
| `assessedvalue` | Assessed value in that snapshot, US$ | 9,236 |
| `interior_livingarea` | Living area, sq ft | 9,236 |
| `interior_bedrooms` | Bedrooms | 9,236 |
| `interior_fullbaths` | Full bathrooms | 9,236 |
| `interior_halfbaths` | Half bathrooms | 9,236 |
| `interior_totalrooms` | Total rooms | 9,236 |
| `interior_numunits` | Number of units in the building/parcel | 2,183 |
| `condition_yearbuilt` | Year built | 9,236 |
| `condition_overallcondition` | Assessor overall condition rating | 9,236 |
| `condition_overallgrade` | Assessor construction grade | 9,236 |
| `condition_interiorcondition` | Assessor interior condition rating | 2,183 |
| `exterior_numstories` | Number of stories | 9,236 |
| `exterior_floorlocation` | Floor (condos) | 6,926 |
| `exterior_view` | Assessor view rating (condos) | 7,053 |
| `systems_centralair` | Central air (yes/no) | 2,183 |
| `interior_laundryinunit` | In-unit laundry (yes/no) | 7,053 |
| `parking_open` | Open parking spaces | 9,236 |
| `parking_covered` | Covered parking spaces | 9,236 |
| `parking_garage` | Garage spaces | 7,053 |
| `landarea` | Land area, sq ft (parcel) | 9,236 |
| `zoning` | Zoning district | 2,451 |
| `flag_low_ratio` | TRUE if price < 10% of assessed value (likely not arm's-length) | 9,236 |
| `flag_multi_parcel` | TRUE if several parcels share this deed (book/page) and date | 9,236 |
| `flag_ppsf_extreme` | TRUE if price per sq ft is in the bottom/top 0.5% of its group | 9,236 |
| `flag_bedrooms_missing` | TRUE if bedroom count is missing | 9,236 |
| `main_sample` | TRUE unless flag_low_ratio or flag_multi_parcel (main analysis sample) | 9,236 |

# Added columns: `sales_features.csv`

Built by `analysis/hedonic/20_build_features.py`. Same rows as `sales_clean.csv` plus the columns below. Rules: `analysis/hedonic/SPEC_MODEL1.md`.

| Column | Meaning |
|---|---|
| `neighborhood` | Cambridge neighborhood (point in polygon) |
| `tract` | 2020 census tract GEOID |
| `income`, `income_moe`, `log_income` | ACS 2020–2024 tract median household income, its 90% margin of error, and its log |
| `crime_violent_{300,500,800}` | Violent crime reports with reporting-area centre within the radius, 3 calendar years before the sale year, per km² per year, divided by 100 |
| `crime_property_{300,500,800}` | Same, for property crime against residents |
| `crime_*_500_nosq` | 500 m measures without reporting areas within 300 m of a Red Line station in Cambridge |
| `transit_km`, `nearest_station` | Distance (km) to and name of the nearest rapid-transit station north of the Charles that was open on the sale date |
| `transit_km_allstations` | Same, among all MBTA rapid-transit stations |
| `transit_band` | `transit_km` in bands: <400 m, 400–800 m, 800–1,200 m, >1,200 m |
| `age_group`, `condition`, `grade` | Grouped year built, overall condition and construction grade (see spec) |
| `log_area`, `bedrooms`, `fullbaths`, `halfbaths`, `parking`, `floor`, `log_land` | Tidy home features (capped as in the spec) |
| `rel_assessed_ppsf`, `rel_price_ppsf` | Assessed value per sq ft, and price per sq ft, relative to the median for the same home type and year |
| `flag_restricted_likely` | TRUE if both relative values are below 0.5 (likely deed-restricted; robustness check in Phase 3, excluded from `market_sample`) |
| `model_sample` | TRUE if in the Model 1 sample (main sample with all features; used for Phases 2–3) |
| `market_sample` | `model_sample` without `flag_restricted_likely`: the main sample from Phase 4 on (decided 2026-11-22, after seeing Phase 3 results) |
| `robust_sample` | TRUE if all features are present (including flagged sales) |
