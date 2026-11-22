# Phase 1 summary: data collected and cleaned (2026-11-22)

*Description of the data only. No models have been run, so nothing here is a finding about what
drives prices.*

## What was collected

All 14 sources are free and public. They were downloaded unedited into `data/raw/hedonic/`
(kept on this computer, not in git), and each one is documented in
[`data/raw/hedonic/SOURCES.md`](../../data/raw/hedonic/SOURCES.md) with its URL, download time,
size and checksum. Re-create them with `uv run python analysis/hedonic/00_fetch_data.py`.

| Source | What we got |
|---|---|
| Cambridge Property Database FY2016–FY2027 | 354,003 rows (one per property per year), 147 MB |
| Cambridge Police Crime Reports | 102,097 reports, 2009–2026, 117 reporting areas |
| Cambridge neighborhood boundaries | 13 neighborhoods |
| Census ACS 2020–2024, tracts | median household income (B19013) and median gross rent (B25064), 357 Middlesex County tracts |
| Census tract boundaries 2023 | Massachusetts |
| MBTA GTFS (current) | 10,292 stops, 276 stations |
| MassGIS parcels | Cambridge, Somerville, Arlington, Newton, Brookline (last sale only, no bedrooms) |
| DESE | MCAS district results 2017–2026 (with growth scores, SGP) and per-pupil spending 2009–2025, five districts |

## How the sales were cleaned

Every step and its row count is in [`cleaning_log.csv`](cleaning_log.csv):

1. Removed owner names and mailing addresses (not needed, never committed).
2. Collected every sale from all 12 yearly snapshots and removed duplicates. Each home's features
   come from the first snapshot after its sale.
3. Five sales appeared with two different prices, and 48 duplicate rows of that kind existed before
   the later filters. The more recent price was kept, as a likely correction.
4. **Years 2016–2025 only.** The first snapshot records sales only up to 14 July 2015. Before that,
   each home shows only its last sale, so earlier years would be incomplete and biased.
5. **Removed 8,054 non-market transfers** (price $1,000 or less, of which 1,686 were $0 and 3,982
   were $1).
6. Kept homes only: condos, luxury condos, single-family, two- and three-family. Removed 810 sales of
   apartment buildings, offices and shops.
7. Removed 68 sales with no living area or no location.
8. **Flagged, not deleted:** 197 sales recorded on one deed together with other parcels (the price is
   often a total for all of them) and 12 sales below 10% of the assessed value. Both are left out of
   the main sample but kept for robustness checks. Also flagged: 94 sales with extreme price per
   sq ft (kept in the main sample, trimmed in a sensitivity check).

**Result:** 9,236 market sales, of which **9,027 are in the main sample**: 5,949 condos, 945 luxury
condos, 1,274 single-family, 540 two-family and 319 three-family. That is about 750–1,120 a year.
Codebook: [`DATA_DICTIONARY.md`](../../data/processed/hedonic/DATA_DICTIONARY.md).

## First look (descriptive)

- Median price per sq ft by neighborhood ranges from about **$650 (Cambridge Highlands) to about $900
  (Mid-Cambridge)** ([`summary_by_neighborhood.csv`](summary_by_neighborhood.csv)). These raw
  medians mix very different homes. The models in Phase 2 compare like with like.
- Raw median price per sq ft rose roughly 35–80% from 2016 to 2025, depending on home type (figure 4).
- Figures in `figures/hedonic/`: sales per year (h1), price distribution (h2), map of price per sq ft
  (h3), trend (h4).

## Things found that matter for Phase 2

- **Crime data mixes very different events.** The most common types are hit-and-run, shoplifting,
  larceny from cars, bicycle theft, forgery and warrant arrests. Plan: build separate "violent" and
  "property crime against residents" measures, and leave out categories such as forgery,
  warrant arrests and traffic. The type lists will be written down before any model is run.
- **Transit stations change over time.** The Green Line Extension stations opened in 2022 and are in
  today's MBTA feed, so for earlier sales distance must be measured to the stations that existed then.
- **Cross-town data is thinner.** MassGIS has only each home's last sale and no bedroom count. Its
  Cambridge file has 6,068 recent sales, against 9,236 in the city's own database. Cross-town
  models will be smaller and use rooms and living area instead of bedrooms.
- **Still to collect:** town residential tax rates (MA Division of Local Services) for the cross-town
  comparison. That source has no simple download, so it will be entered from its published tables
  in Phase 4 and documented.
- No sales in the Area 2/MIT neighborhood (mostly institutional), so neighborhood fixed effects use
  12 neighborhoods.
