# Pre-specification for Phase 2 (features and Model 1)

*Written and committed on 2026-11-22, **before** any regression was run. Anything changed after
results are seen will be listed at the bottom under "Changes after seeing results" and labeled
exploratory.*

## 1. Sample

- `sales_clean.csv`, rows with `main_sample = TRUE` (9,027 sales, 2016–2025).
- Dropped for Model 1 only if a feature cannot be built: outside every neighborhood polygon, no
  census tract, or no tract income. Counts are logged in `results/hedonic/feature_log.csv`.

## 2. Safety (crime)

Source: Cambridge Police Crime Reports. Each report has a police **reporting area** and that area's
centre point (no exact address). Report date = `Date of Report`, format `MM/DD/YYYY hh:mm:ss AM/PM`.

**Violent crime** (crimes that use or threaten force against a person):
Homicide, Kidnapping, Aggravated Assault, Simple Assault, Street Robbery, Commercial Robbery.

**Property crime against residents** (victims are mostly households, not businesses):
Housebreak, Larceny from Residence, Larceny from MV, Auto Theft, Larceny of Plate,
Larceny of Bicycle, Mal. Dest. Property, Arson.

**Left out** (not a measure of neighbourhood risk to residents, or mostly business/visitor
victims): Shoplifting, Larceny from Building, Larceny from Person, Commercial Break, Larceny
(Misc), Larceny of Services, Hit and Run, OUI, Forgery, Counterfeiting, Flim Flam, Embezzlement,
Extortion/Blackmail, Warrant Arrest, Rec. Stol. Property, Sex Offender Violation, Violation of
H.O., Violation of R.O., Drugs, Liquor Possession/Sale, Drinking in Public, Gambling,
Prostitution, Weapon Violations, Threats, Harassment, Stalking, Phone Calls, Annoying & Accosting,
Peeping & Spying, Indecent Exposure, Disorderly, Trespassing.

**Measure.** For each sale: reports of the category whose reporting-area centre lies within
**500 m** of the home, during the **three calendar years before the sale year**, expressed as
**reports per year per km²** (count / 3 / (π·0.5²)). Using years before the sale avoids counting
crimes the buyer could not have known about.

**Sensitivity checks** (Phase 2 robustness table): radius 300 m and 800 m; leaving out reports
whose reporting-area centre is within 300 m of a Red Line station in Cambridge (Harvard, Central,
Kendall/MIT, Porter, Alewife: the commercial squares, where counts reflect visitors).

## 3. Area income

ACS 2020–2024 5-year median household income (B19013) for the 2020 census tract containing the
home (point in polygon, 2023 cartographic tract file). One value per tract (no change over time).
Used as **log(income)**. The margin of error (90%) is carried through by re-estimating the model
200 times with income drawn from a normal distribution with standard error MOE/1.645.

## 4. Transit

Straight-line distance (metres, Massachusetts State Plane projection EPSG:26986) from the home to
the nearest rapid-transit station **open on the sale date**, among stations north of the Charles
River (so that the river does not create false "nearby" stations):

| Station(s) | Line | Open |
|---|---|---|
| Alewife, Davis, Porter, Harvard, Central, Kendall/MIT | Red | whole period |
| Science Park/West End (reached over the Charles River Dam) | Green | whole period |
| Assembly, Sullivan Square, Community College | Orange | whole period |
| Lechmere (old station) | Green | until 2020-05-23 |
| Lechmere (new station), Union Square | Green | from 2022-03-21 |
| East Somerville, Gilman Square, Magoun Square, Ball Square, Medford/Tufts | Green | from 2022-12-12 |

Dates: City of Cambridge GLX project page and press coverage (checked 2026-11-22). The old
Lechmere closed in May 2020; the exact last day is taken as 23 May 2020. Its coordinates are not in
the current GTFS feed; the new station stands just across O'Brien Highway, so its coordinates are
used for both (small error, East Cambridge only).

Coordinates: current MBTA GTFS `stops.txt` parent stations.

Main form: **distance in km** (linear). Sensitivity: distance bands (< 400 m, 400–800 m,
800–1,200 m, > 1,200 m); and nearest station among *all* MBTA rapid-transit stations (including
south of the river).

## 5. Model 1 specification

    log(price) = home features + violent crime + property crime + log(tract income)
                 + transit distance + neighborhood FE + sale year-quarter FE + error

Home features (controls, not findings):
- home type: condo, luxury condo, single-family, two-family, three-family (fixed effects)
- log(living area); bedrooms (capped at 6); full baths (capped at 4); half baths (capped at 2)
- age group from year built: before 1900, 1900–1939, 1940–1979, 1980–1999, 2000+, unknown
  (year built outside 1700–2027 is set to unknown: 51 rows with 0 and 1 row with 20233)
- overall condition: Excellent or better (Superior, Excellent) / Very Good / Good / Average /
  Below average (Fair, Poor, Very Poor)
- construction grade: Excellent or better (Estate Quality, Excellent, Very Good Ex) / Very Good
  (Very Good, Good Very Good) / Good / Average (Average Plus, Average, Average Minus) / Below
  average (Fair, Poor)
- parking spaces (open + covered + garage, capped at 4)

Standard errors: clustered by census tract (main). Check: wild cluster bootstrap (Webb weights,
9,999 draws, null imposed) clustered by the 12 neighborhoods, for the four headline variables.

Headline variables: violent crime, property crime, log(income), transit distance.

## 6. Collinearity checks (before interpreting)

- Correlation matrix of the headline variables and main home features.
- Variance inflation factors (VIF) of the headline variables after removing neighborhood and
  quarter fixed effects (the variation the model actually uses). VIF > 5 is flagged, > 10 means
  "cannot be separated".
- "Drop one" table: re-estimate leaving out each headline variable in turn.

## 7. Robustness table (Model 1)

1. Main model. 2. Include flagged sales (multi-parcel, low ratio). 3. Leave out extreme price per
sq ft. 4. Transit bands. 5. All stations, both sides of the river. 6. Crime radius 300 m.
7. Crime radius 800 m. 8. Crime without commercial squares. 9. Separate models for condos
(adding floor, view, in-unit laundry) and for 1–3 family homes (adding log land area).

## Changes after seeing results

- **Leave-one-neighborhood-out table** (diagnostic, added after the bootstrap gave a much wider
  interval for transit than the tract-clustered one). It re-fits the model 12 times, each time
  without one neighborhood. Exploratory; it changes no estimate.
- The wild bootstrap code was moved into `wildboot.py` and checked by `verify_wild_bootstrap.py`
  (exact match with brute-force refits; 4.3% rejection under a true null at the 5% level). Method
  unchanged.
- Figure styling only (labels, legend position).
