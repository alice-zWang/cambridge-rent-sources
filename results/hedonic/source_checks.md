# Source checks (step 15)

Automatic description of every raw file, to confirm it can be used in later phases.

## Cleaned sales

- Main sample: 9,027 sales, 2016-2025; 3 fall outside all neighborhood polygons.
- By group: Condo 5,949, Luxury condo 945, Single-family 1,274, Two-family 540, Three-family 319

## Crime reports

- 102,097 reports; columns: File Number, Date of Report, Crime Date Time, Crime, Reporting Area, Neighborhood, Location, Reporting Area Lat, Reporting Area Lon, Reporting Area Location
- Report years 2009-2026; reports per year (median) 5,549; 117 reporting areas.
- Rows without a reporting area: 3.
- Most common types: Hit and Run (10,873); Shoplifting (8,328); Larceny from MV (8,103); Larceny of Bicycle (7,479); Mal. Dest. Property (6,951); Forgery (6,923); Warrant Arrest (5,068); Larceny from Residence (5,066)

## ACS 2020-2024 table B19013

- Columns: GEO_ID, B19013_E001, B19013_M001 ...; Massachusetts tracts: 1,620; Middlesex County tracts: 357.

## ACS 2020-2024 table B25064

- Columns: GEO_ID, B25064_E001, B25064_M001 ...; Massachusetts tracts: 1,620; Middlesex County tracts: 357.

## MBTA GTFS

- 10,292 stops; 276 parent stations (location_type = 1); route types: {'3': 371, '2': 14, '4': 9, '0': 5, '1': 3} (0 = light rail, 1 = subway, 2 = commuter rail, 3 = bus, 4 = ferry).
- Feed columns: stop_id, stop_code, stop_name, stop_desc, platform_code, platform_name, stop_lat, stop_lon, zone_id, stop_address, stop_url, level_id ...

## MassGIS parcels (5 towns)

- **L3_SHP_M010_ARLINGTON.zip**: assessor table `L3_SHP_M010_Arlington/M010Assess_CY26_FY26.dbf`, 15,663 rows, fiscal year 2026; sale fields present: FY, LS_DATE, LS_PRICE, USE_CODE, LS_BOOK, LS_PAGE, YEAR_BUILT, BLD_AREA, UNITS, RES_AREA, STYLE, NUM_ROOMS; last sales since 2016 with price > $1,000: 4,568.
- **L3_SHP_M046_BROOKLINE.zip**: assessor table `L3_SHP_M046_Brookline/M046Assess_CY26_FY27.dbf`, 18,114 rows, fiscal year 2027; sale fields present: FY, LS_DATE, LS_PRICE, USE_CODE, LS_BOOK, LS_PAGE, YEAR_BUILT, BLD_AREA, UNITS, RES_AREA, STYLE, NUM_ROOMS; last sales since 2016 with price > $1,000: 5,446.
- **L3_SHP_M049_CAMBRIDGE.zip**: assessor table `L3_SHP_M049_Cambridge/M049Assess_CY25_FY26.dbf`, 28,812 rows, fiscal year 2026; sale fields present: FY, LS_DATE, LS_PRICE, USE_CODE, LS_BOOK, LS_PAGE, YEAR_BUILT, BLD_AREA, UNITS, RES_AREA, STYLE, NUM_ROOMS; last sales since 2016 with price > $1,000: 6,068.
- **L3_SHP_M207_NEWTON.zip**: assessor table `L3_SHP_M207_Newton/M207Assess_CY25_FY26.dbf`, 30,165 rows, fiscal year 2026; sale fields present: FY, LS_DATE, LS_PRICE, USE_CODE, LS_BOOK, LS_PAGE, YEAR_BUILT, BLD_AREA, UNITS, RES_AREA, STYLE, NUM_ROOMS; last sales since 2016 with price > $1,000: 8,338.
- **L3_SHP_M274_SOMERVILLE.zip**: assessor table `L3_SHP_M274_Somerville/M274Assess_CY25_FY25.dbf`, 19,013 rows, fiscal year 2025; sale fields present: FY, LS_DATE, LS_PRICE, USE_CODE, LS_BOOK, LS_PAGE, YEAR_BUILT, BLD_AREA, UNITS, RES_AREA, STYLE, NUM_ROOMS; last sales since 2016 with price > $1,000: 5,852.

## DESE

- MCAS district rows: 16,274; districts ['Arlington', 'Brookline', 'Cambridge', 'Newton', 'Somerville']; school years 2017-2026; rows with average SGP: 10,252.
- Per-pupil spending rows: 85; years 2009-2025.
