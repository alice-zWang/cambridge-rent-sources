# Deductive coding framework: Cambridge housing price sources

## What was coded

- **Corpus:** the documentation attached to 10 housing datasets on the [Cambridge Open Data portal](https://data.cambridgema.gov): descriptions, source notes, stated limitations, update schedules and column definitions. The text is in [`data/raw/cambridge_open_data_metadata.csv`](../data/raw/cambridge_open_data_metadata.csv).
- **Unit of analysis:** one dataset record. Each text field is coded, and a passage can receive more than one code.
- **Why deductive:** codes come from the research question (which price sources are reliable and reasonable for newcomers) and from standard data-quality dimensions: accuracy, timeliness, completeness, granularity, provenance and comparability. New codes are added only when a passage fits none of these.

## Codebook

### PRICE: What price is measured

**Definition:** the kind of housing cost a source reports.
**Captures:** column names and definitions; phrases such as "median rent charged", "arms-length", "assessed value".

- **PRICE-ASK:** rents or prices that landlords charge or advertise. *Example:* Median Residential Rents
- **PRICE-SALE:** prices from completed sales. *Example:* Housing Median Sales Prices (arms-length sales only)
- **PRICE-ASSESS:** values the city sets for property tax, not market prices. *Example:* Property Database FY2016–FY2026

### SRC: Where the numbers come from

**Definition:** how clearly a source says where its numbers come from and how they were processed.
**Captures:** the attribution field, "Data Origins" notes, method descriptions.

- **SRC-NAMED:** a specific origin is named. *Example:* Middlesex South Registry of Deeds; U.S. Census Bureau
- **SRC-VAGUE:** the origin is unclear. *Example:* rents "collected from various sources"
- **SRC-METHOD:** filtering or estimation rules are explained. *Example:* the arms-length sales filter; block groups combined into neighborhoods; CPI adjustment

### TIME: How current it is

**Definition:** how up to date the data is, and when in the year it was collected.
**Captures:** update frequency, last-updated date, year and month columns.

- **TIME-FREQ:** how often it is updated, from daily to annually
- **TIME-LAG:** the gap between the latest data and today. *Example:* rents end at Sept 2025; sales end at 2024
- **TIME-POINT:** when in the year values are collected, and whether that is consistent. *Example:* rents from Jan 2010, Aug 2011, then September every year after

### GRAN: Detail and coverage

**Definition:** how finely the data is broken down, and which housing it includes.
**Captures:** geography columns, unit-type columns, phrases like "market rate" or "includes university housing".

- **GRAN-GEO:** citywide, neighborhood or parcel level
- **GRAN-UNIT:** which unit types are separated. *Example:* 1BR/2BR/3BR rents with no studios; single-, two-, three-family and condo sales
- **GRAN-SEGMENT:** which housing is in or out. *Example:* market-rate only; graduate student housing included; affordable units; short-term rentals

### LIM: Limitations and uncertainty

**Definition:** what a source admits it cannot do or might get wrong.
**Captures:** the "Specific Limitations" field and caution notes in descriptions.

- **LIM-GENERIC:** boilerplate disclaimers. *Example:* "subject to revision or retraction at any time"
- **LIM-SPECIFIC:** concrete, named problems. *Example:* ACS boundaries don't match neighborhoods 10, 12 and 13; the property data is "not the official information source"
- **LIM-ERROR:** statistical error stated outright. *Example:* ACS sampling error

### COMP: Comparability across sources

**Definition:** whether numbers can fairly be compared over time or with other sources.
**Captures:** adjustment notes, category definitions, ID and geography columns.

- **COMP-ADJUST:** adjustments that allow comparison over time. *Example:* CPI-adjusted rents
- **COMP-DEF:** whether categories match other sources. *Example:* bedroom counts vs. property types vs. Census categories
- **COMP-LINK:** shared IDs or geography for joining datasets. *Example:* Map/Lot, MBL, GISID, neighborhood number, latitude/longitude

### CTX: Market context for newcomers

**Definition:** information that isn't a price but explains price pressure or what newcomers face.
**Captures:** enrollment, unit counts, permits, violations.

- **CTX-DEMAND:** who needs housing. *Example:* Town Gown enrollment and students living off campus
- **CTX-SUPPLY:** how many units exist, are coming, or are leaving the long-term market. *Example:* housing stock, Development Log, short-term rentals
- **CTX-QUALITY:** housing conditions. *Example:* code violations such as pests

## First pass: codes applied

| Dataset | Main codes | Note |
|---|---|---|
| Median Residential Rents 2010–present | PRICE-ASK, SRC-VAGUE, SRC-METHOD, TIME-POINT, GRAN-GEO (citywide), GRAN-UNIT, COMP-ADJUST, LIM-GENERIC | The only rent dataset |
| Housing Median Sales Prices | PRICE-SALE, SRC-NAMED, SRC-METHOD, TIME-LAG, GRAN-UNIT, LIM-GENERIC | Clearest method on the portal |
| ACS 5-Year by Neighborhood: Housing | SRC-NAMED, SRC-METHOD, GRAN-GEO, LIM-SPECIFIC, LIM-ERROR, COMP-LINK | Vacancy and renter share; no rent values |
| Housing Stock by Neighborhood | CTX-SUPPLY, GRAN-GEO, GRAN-SEGMENT, TIME-FREQ | Counts university grad housing |
| Town Gown Report | CTX-DEMAND, SRC-NAMED, TIME-FREQ | Universities report their own numbers |
| Short Term Rentals | CTX-SUPPLY, GRAN-SEGMENT, TIME-FREQ, LIM-SPECIFIC | Complete applications only |
| Property Database FY2016–FY2026 | PRICE-ASSESS, PRICE-SALE, GRAN-GEO (parcel), COMP-LINK, LIM-SPECIFIC | Contains owner names, which must be dropped |
| Housing Code Violations | CTX-QUALITY, GRAN-GEO, TIME-FREQ | Updated weekly |
| Decennial Census Housing 1980–2020 | SRC-NAMED, SRC-METHOD, CTX-SUPPLY, TIME-LAG | Ends at 2020 |
| Development Log 2026 Q3 | CTX-SUPPLY, GRAN-GEO, TIME-FREQ | Lists new and affordable units |

## Observations

- **One rent source, weak on provenance.** The portal's only rent dataset gives one citywide median per bedroom size per year, mostly from September, attributed to "various sources". The city's housing data page later clarified that the medians come from advertised listings and exclude affordable and university graduate housing, which moves this record from SRC-VAGUE toward SRC-METHOD.
- **Sales data is clearer but less useful to renters.** It names its source and explains its filter but says nothing about rent.
- **Nominal vs. real.** The median 1-bedroom rose from $1,725 (Jan 2010) to $2,700 (Sept 2025), about 57%, but in Sept 2025 dollars it peaked at $3,525 in 2014 and is about 23% lower now.
- **Gaps.** No studios, no neighborhood-level rents, and no information on utilities.

## Next steps

- Apply the codebook to outside sources (Zillow, Census ACS, HUD, listing samples)
- Second-coder check on 2–3 datasets
- Add inductive codes for passages that fit nowhere, with a note on why
