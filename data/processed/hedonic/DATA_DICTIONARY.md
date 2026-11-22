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
