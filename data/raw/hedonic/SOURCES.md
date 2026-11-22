# Raw data sources (hedonic study)

Every file in this folder is an **unedited** download, made by `analysis/hedonic/00_fetch_data.py`. The files themselves are git-ignored (size; the property file contains owner names). Re-create them by running the script. The SHA-256 checksum shows whether a new download is byte-identical to the one used here. Publishers update their data, so a later download will usually differ.

## `cambridge_property_db_fy2016_fy2027.csv`

- **Publisher:** City of Cambridge, Assessing Department (Cambridge Open Data)
- **Dataset:** Cambridge Property Database FY2016-FY2027 (eey2-rv59), https://data.cambridgema.gov/d/eey2-rv59
- **Download URL:** <https://data.cambridgema.gov/api/views/eey2-rv59/rows.csv?accessType=DOWNLOAD>
- **Downloaded:** 2026-11-22 20:29 UTC. **Size:** 147.1 MB. **Contents:** 354,003 rows
- **SHA-256:** `0ab31fc00ea5835955607aee165aca366106693d3f2451ab40cfae50945c7705`
- **What it is:** One row per parcel (or condo unit) per fiscal year, FY2016-FY2027: latest sale price and date, assessed values, building characteristics (living area, bedrooms, baths, year built, condition), property class, coordinates. Contains owner names and mailing addresses: these are dropped in step 10 and never committed.
- **Terms:** Public record. Cambridge Open Data portal terms of use apply (see portal).

## `cambridge_crime_reports.csv`

- **Publisher:** Cambridge Police Department (Cambridge Open Data)
- **Dataset:** Crime Reports (xuad-73uj), https://data.cambridgema.gov/d/xuad-73uj
- **Download URL:** <https://data.cambridgema.gov/api/views/xuad-73uj/rows.csv?accessType=DOWNLOAD>
- **Downloaded:** 2026-11-22 20:29 UTC. **Size:** 17.9 MB. **Contents:** 102,097 rows
- **SHA-256:** `33a52b618c0323d798bd1c03cb7117044e609a50969cad761524c3d965c956e8`
- **What it is:** One row per reported crime since 2009: type, date, police reporting area (117 areas), neighborhood, reporting-area centroid coordinates. Locations are reporting areas, not addresses.
- **Terms:** Cambridge Open Data portal terms of use apply (see portal).

## `cambridge_neighborhoods.geojson`

- **Publisher:** City of Cambridge, Community Development Department (Cambridge Open Data)
- **Dataset:** Cambridge Neighborhood Polygons (k3pi-9823), https://data.cambridgema.gov/d/k3pi-9823
- **Download URL:** <https://data.cambridgema.gov/api/geospatial/k3pi-9823?method=export&format=GeoJSON>
- **Downloaded:** 2026-11-22 20:29 UTC. **Size:** 0.2 MB. **Contents:** 13 features
- **SHA-256:** `af10123833e56fe029f656ec2c641dfa58962fba3136fe18fc951164054aa186`
- **What it is:** Boundaries of Cambridge's 13 official neighborhoods.
- **Terms:** Cambridge Open Data portal terms of use apply (see portal).

## `acs5_2024_b19013_median_household_income.dat`

- **Publisher:** U.S. Census Bureau, American Community Survey
- **Dataset:** ACS 5-year 2020-2024 table-based summary file, table B19013 (median household income)
- **Download URL:** <https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-b19013.dat>
- **Downloaded:** 2026-11-22 20:29 UTC. **Size:** 17.9 MB. **Contents:** 543,579 rows
- **SHA-256:** `b25a176b0e6c339b6f3a2a0d3d8446bf06f5f080b4395993ec9a8313efb1c229`
- **What it is:** National file, every geography. Step 20 keeps Massachusetts census tracts. Estimates with 90% margins of error, in 2024 dollars.
- **Terms:** U.S. federal government data (public domain).

## `acs5_2024_b25064_median_gross_rent.dat`

- **Publisher:** U.S. Census Bureau, American Community Survey
- **Dataset:** ACS 5-year 2020-2024 table-based summary file, table B25064 (median gross rent)
- **Download URL:** <https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-b25064.dat>
- **Downloaded:** 2026-11-22 20:29 UTC. **Size:** 17.3 MB. **Contents:** 543,579 rows
- **SHA-256:** `b36e6dc1fcef36b8b307d31b37517b64c80d8b9c70d48c9b1894242860f42eb0`
- **What it is:** National file, every geography. Used only for the small tract-level rent check.
- **Terms:** U.S. federal government data (public domain).

## `cb_2023_25_tract_500k.zip`

- **Publisher:** U.S. Census Bureau, Cartographic Boundary Files
- **Dataset:** 2023 census tracts, Massachusetts, 1:500,000 (2020 tract definitions)
- **Download URL:** <https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_25_tract_500k.zip>
- **Downloaded:** 2026-11-22 20:29 UTC. **Size:** 0.6 MB. **Contents:** 7 files in zip
- **SHA-256:** `5c35a1200fd2c8cdc96f577b37d23e78ffb5615a0100b28ec770ab68deea3e59`
- **What it is:** Tract boundaries, to attach each sale to its census tract.
- **Terms:** U.S. federal government data (public domain).

## `MBTA_GTFS.zip`

- **Publisher:** Massachusetts Bay Transportation Authority (MBTA)
- **Dataset:** MBTA GTFS static feed (current schedule), https://www.mbta.com/developers
- **Download URL:** <https://cdn.mbta.com/MBTA_GTFS.zip>
- **Downloaded:** 2026-11-22 20:29 UTC. **Size:** 19.8 MB. **Contents:** 32 files in zip
- **SHA-256:** `04cd2571fed0494c0c0dd2e30fa770140fd87ad7b6eb3c40265426c3c43d0772`
- **What it is:** Current stops and stations (stops.txt) and routes. A current snapshot: stations that opened recently (Green Line Extension, 2022) are present; opening dates are handled in step 20.
- **Terms:** MBTA developer license agreement (see https://www.mbta.com/developers).

## `L3_SHP_M049_CAMBRIDGE.zip`

- **Publisher:** MassGIS (Bureau of Geographic Information), from municipal assessors
- **Dataset:** MassGIS Property Tax Parcels, standardized parcels + assessor table, Cambridge
- **Download URL:** <https://s3.us-east-1.amazonaws.com/download.massgis.digital.mass.gov/shapefiles/l3parcels/L3_SHP_M049_CAMBRIDGE.zip>
- **Downloaded:** 2026-11-22 20:29 UTC. **Size:** 4.5 MB. **Contents:** 35 files in zip
- **SHA-256:** `fca6ceb1816f16bbde25ea6610fdc30dcb4e0f79c77561b062b04a9abf817b60`
- **What it is:** Parcel polygons and a standardized assessor table (last sale only, no bedroom count). Used for cross-town comparisons (models 4 and 5).
- **Terms:** MassGIS data, free public download (see mass.gov MassGIS terms).

## `L3_SHP_M274_SOMERVILLE.zip`

- **Publisher:** MassGIS (Bureau of Geographic Information), from municipal assessors
- **Dataset:** MassGIS Property Tax Parcels, standardized parcels + assessor table, Somerville
- **Download URL:** <https://s3.us-east-1.amazonaws.com/download.massgis.digital.mass.gov/shapefiles/l3parcels/L3_SHP_M274_SOMERVILLE.zip>
- **Downloaded:** 2026-11-22 20:29 UTC. **Size:** 4.1 MB. **Contents:** 35 files in zip
- **SHA-256:** `e9992a59482163dce46efbb5f8fb28ac0c0ae2bba03331c76c875a1123d97be8`
- **What it is:** Parcel polygons and a standardized assessor table (last sale only, no bedroom count). Used for cross-town comparisons (models 4 and 5).
- **Terms:** MassGIS data, free public download (see mass.gov MassGIS terms).

## `L3_SHP_M010_ARLINGTON.zip`

- **Publisher:** MassGIS (Bureau of Geographic Information), from municipal assessors
- **Dataset:** MassGIS Property Tax Parcels, standardized parcels + assessor table, Arlington
- **Download URL:** <https://s3.us-east-1.amazonaws.com/download.massgis.digital.mass.gov/shapefiles/l3parcels/L3_SHP_M010_ARLINGTON.zip>
- **Downloaded:** 2026-11-22 20:29 UTC. **Size:** 3.7 MB. **Contents:** 35 files in zip
- **SHA-256:** `d87d7231fcb037eaa703a137505187e2ec31fe2ca95a145d0e38598161d1211f`
- **What it is:** Parcel polygons and a standardized assessor table (last sale only, no bedroom count). Used for cross-town comparisons (models 4 and 5).
- **Terms:** MassGIS data, free public download (see mass.gov MassGIS terms).

## `L3_SHP_M207_NEWTON.zip`

- **Publisher:** MassGIS (Bureau of Geographic Information), from municipal assessors
- **Dataset:** MassGIS Property Tax Parcels, standardized parcels + assessor table, Newton
- **Download URL:** <https://s3.us-east-1.amazonaws.com/download.massgis.digital.mass.gov/shapefiles/l3parcels/L3_SHP_M207_NEWTON.zip>
- **Downloaded:** 2026-11-22 20:29 UTC. **Size:** 10.0 MB. **Contents:** 35 files in zip
- **SHA-256:** `5338ee105a315d23e0081869248ac612749d7344879af8f76bb6bfcf5fb26f87`
- **What it is:** Parcel polygons and a standardized assessor table (last sale only, no bedroom count). Used for cross-town comparisons (models 4 and 5).
- **Terms:** MassGIS data, free public download (see mass.gov MassGIS terms).

## `L3_SHP_M046_BROOKLINE.zip`

- **Publisher:** MassGIS (Bureau of Geographic Information), from municipal assessors
- **Dataset:** MassGIS Property Tax Parcels, standardized parcels + assessor table, Brookline
- **Download URL:** <https://s3.us-east-1.amazonaws.com/download.massgis.digital.mass.gov/shapefiles/l3parcels/L3_SHP_M046_BROOKLINE.zip>
- **Downloaded:** 2026-11-22 20:29 UTC. **Size:** 3.3 MB. **Contents:** 35 files in zip
- **SHA-256:** `f8eea9c9f9888587d8a652a69659e47a6b04dc8404b63edb1d6212d8c101ab87`
- **What it is:** Parcel polygons and a standardized assessor table (last sale only, no bedroom count). Used for cross-town comparisons (models 4 and 5).
- **Terms:** MassGIS data, free public download (see mass.gov MassGIS terms).

## `dese_mcas_district_5towns.csv`

- **Publisher:** Massachusetts DESE, via the Education-to-Career Research and Data Hub
- **Dataset:** MCAS Achievement Results (i9w6-niyt), https://educationtocareer.data.mass.gov/d/i9w6-niyt
- **Download URL:** <https://educationtocareer.data.mass.gov/resource/i9w6-niyt.csv?%24where=dist_name+in%28%27Cambridge%27%2C%27Somerville%27%2C%27Arlington%27%2C%27Newton%27%2C%27Brookline%27%29+AND+org_type%3D%27Public+School+District%27&%24limit=500000>
- **Downloaded:** 2026-11-22 20:29 UTC. **Size:** 3.5 MB. **Contents:** 16,274 rows
- **SHA-256:** `589189560db604ad8fc0f39dcf9751799bb5fd34d3c341f28396cd57436cabbd`
- **What it is:** District-level MCAS rows for Cambridge, Somerville, Arlington, Newton and Brookline: all years, grades, subjects and student groups, with % meeting/exceeding, average scaled score and average student growth percentile (SGP). Filtered on the server; the exact query is the URL.
- **Terms:** Commonwealth of Massachusetts open data portal terms apply (see portal).

## `dese_per_pupil_spending_5towns.csv`

- **Publisher:** Massachusetts DESE, via the Education-to-Career Research and Data Hub
- **Dataset:** Elementary and Secondary District Expenditures Per Pupil (8szy-v4ed)
- **Download URL:** <https://educationtocareer.data.mass.gov/resource/8szy-v4ed.csv?%24where=dist_name+in%28%27Cambridge%27%2C%27Somerville%27%2C%27Arlington%27%2C%27Newton%27%2C%27Brookline%27%29&%24limit=50000>
- **Downloaded:** 2026-11-22 20:29 UTC. **Size:** 0.0 MB. **Contents:** 85 rows
- **SHA-256:** `8eda0f9173c3d2bbd78491a92b7201bb84228246ef9b4eec0e5fb9dc828d854d`
- **What it is:** Per-pupil spending by school year for the five districts. Filtered on the server.
- **Terms:** Commonwealth of Massachusetts open data portal terms apply (see portal).
