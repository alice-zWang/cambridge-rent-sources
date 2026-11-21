# Annotated bibliography

**Research question:** How much do Cambridge, MA rent estimates differ across sources, and what explains the gaps?

Citations follow APA 7th edition. Entries are grouped by theme. Each entry gives a summary, an assessment of the method, its relevance to this project, and how it connects to the other sources. All sources were checked on November 21, 2026.

---

## Theme 1: How each rent source is built

### U.S. Department of Housing and Urban Development, Office of Policy Development and Research. (2025). *Calculation of HUD Fair Market Rents* [Methodology document, FY2026]. https://www.huduser.gov/portal/datasets/fmr/fmr2026/FY26-Public-FMR-Methodology.pdf

**Summary.** Explains how HUD sets Fair Market Rents (FMRs) for the Housing Choice Voucher program. The base is the 40th-percentile two-bedroom gross rent for standard-quality units in each FMR area, drawn from five-year American Community Survey (ACS) data. HUD then updates it with more recent rent and inflation data and derives the other bedroom sizes using ratios.

**Method assessment.** Transparent and replicable: every step is published. But the design makes it a lagging, metro-wide benchmark, not a measure of current Cambridge rent. FY2026 rests on 2019–2023 survey data, and the area covers more than 100 towns. The method is revised most years, and FY2025 figures for the Boston area were challenged and revised, so values are not strictly comparable across years.

**Relevance.** Explains the project's city-vs-HUD finding. HUD sits below the city's asking rents because it uses the 40th percentile, covers a cheaper region and lags in time. The gap's narrowing is consistent with HUD's survey data catching up to the post-2020 rent rise.

**Connections.** Built on the same ACS data as the Census entries below. Boeing et al. (2023) compare FMRs directly with listing rents and find the same kind of gap.

### U.S. Census Bureau. (2025). *American Community Survey and Puerto Rico Community Survey: 2025 subject definitions*. https://www2.census.gov/programs-surveys/acs/tech_docs/subject_definitions/2025_ACSSubjectDefinitions.pdf

**Summary.** The official definitions for ACS variables. Gross rent is contract rent plus the estimated monthly cost of utilities and fuels paid by the renter, and is reported for all occupied rental units that pay rent, whatever the move-in date.

**Method assessment.** The ACS is a large, probability-based survey, the strongest design among the sources here for representing *all* renters. Its weaknesses for this project: rents are self-reported, one-year estimates for a city of about 120,000 carry margins of error of roughly ±$90–230, and it describes existing leases, not what a newcomer is asked today.

**Relevance.** Defines the "paid" side of the project's asked-vs-paid comparison. Because gross rent includes utilities and listing rents usually don't, the measured newcomer premium is probably an underestimate.

**Connections.** Supplies HUD's base data. Adams et al. (2024) explain why an all-tenant measure like this one moves more slowly than new-lease measures.

### U.S. Census Bureau. (2025, December 3). *Change to monthly contract rent estimates* [User note]. https://www.census.gov/programs-surveys/acs/technical-documentation/user-notes/2025-06.html

**Summary.** Announces that the maximum allowed contract rent in ACS processing was raised to $20,000 a month for 2024 data, from $10,000 for 2020–2023 and $4,000 before 2020. Gross rent maximums rise with it, and the note warns against comparing high-rent areas across years.

**Method assessment.** A short technical note, but essential. Processing caps mainly affect the top of the distribution, so medians are less exposed than averages. Still, any series spanning 2019–2020 or 2023–2024 in a high-rent city deserves caution.

**Relevance.** A direct caveat for the project's Census series, which crosses both cap changes. The 2024 three-bedroom median, which hit the table's $3,500+ top code, shows the problem in practice.

**Connections.** Qualifies every ACS-based number in this list, including HUD's FMRs.

### Zillow Research. (n.d.). *Methodology: Zillow Observed Rent Index (ZORI)*. Retrieved November 21, 2026, from https://www.zillow.com/research/methodology-zori-repeat-rent-27092/

**Summary.** Describes ZORI, a repeat-rent index of *asking* rents on Zillow listings. It compares the same units over time to control for quality changes and is weighted to represent the whole rental stock, not only units on the market.

**Method assessment.** Methodologically strong for tracking change: the repeat-rent design follows Ambrose et al. (2015), and the documentation is public. Limits: the underlying listing data are proprietary and can't be checked, the index is smoothed, and there is no bedroom breakdown. Zillow has also replaced earlier methods (the older Zillow Rent Index), so older Zillow figures are not comparable.

**Relevance.** The best candidate to test whether the city's flat asking-rent series is accurate, since ZORI also measures asking rents. This is the project's main next step.

**Connections.** Adams et al. (2024) classify ZORI as a new-tenant index. Lansing et al. (2022) use it to forecast all-tenant rents.

### City of Cambridge, Community Development Department. (n.d.). *Housing data*. Retrieved November 21, 2026, from https://cambridgema.gov/CDD/factsandmaps/housingdata

**Summary.** The city's description of its median market-rate rent series. Medians are based on advertised apartment prices and exclude affordable housing and university-owned graduate student housing. Figures are given in both nominal and inflation-adjusted dollars, with a separate rental cost tracker by neighborhood.

**Method assessment.** The weakest documentation of the sources here. The page does not name the listing sources, the sample size, or how duplicate and stale listings are handled, and collection month varies in early years. That makes the series hard to audit, which matters because it behaves differently from every other source.

**Relevance.** The project's core series. Its flat growth compared with HUD and the Census is the project's main open question.

**Connections.** Conceptually closest to ZORI and the listing studies by Boeing and colleagues, all of which measure asking rents.

---

## Theme 2: Why asking rents and rents paid diverge

### Adams, B., Loewenstein, L., Montag, H., & Verbrugge, R. (2024). Disentangling rent index differences: Data, methods, and scope. *American Economic Review: Insights, 6*(2), 230–245. https://doi.org/10.1257/aeri.20220685

**Summary.** Uses the Bureau of Labor Statistics microdata behind the Consumer Price Index to build two repeat-rent indexes, one for new tenants and one for all tenants. The large gap between the official CPI rent index and private indexes is explained mainly by scope: new tenants' rents grow differently from all tenants'. New-tenant rents lead all-tenant rents by about a year.

**Method assessment.** The strongest source in this list: published in a top peer-reviewed journal, built on high-quality government microdata, and designed to isolate one cause at a time by holding data and method constant. Its national focus means it doesn't speak to Cambridge directly.

**Relevance.** Provides the theory for the project's asked-vs-paid finding. The newcomer premium and its narrowing fit the pattern of all-tenant rents catching up to new-lease rents with a lag.

**Connections.** Extends Ambrose et al. (2015). Explains why Lansing et al. (2022) can forecast CPI rent from asking rents. Gallin and Verbrugge (2019) explain the slow adjustment for sitting tenants.

### Gallin, J., & Verbrugge, R. J. (2019). A theory of sticky rents: Search and bargaining with incomplete information. *Journal of Economic Theory, 183*, 478–519. https://doi.org/10.1016/j.jet.2019.06.003

**Summary.** Offers the first theoretical explanation for why sitting tenants' rents change slowly even though leases are renegotiated regularly, and why small landlords' rents are stickier than large landlords'. Moving costs and private information make offering the same contract attractive to landlords.

**Method assessment.** A formal economic model, not an empirical study. It is persuasive as a mechanism but does not measure how big the effect is in any city. The math is advanced; the introduction and conclusion are the accessible parts.

**Relevance.** Explains *why* existing renters pay less than the asking rents newcomers see, which is the mechanism behind the project's newcomer premium. Cambridge's many small, older buildings make this especially relevant.

**Connections.** Gives a theoretical basis to the facts Genesove (2003) documents. Supports the lag found by Adams et al. (2024).

### Genesove, D. (2003). The nominal rigidity of apartment rents. *Review of Economics and Statistics, 85*(4), 844–853.

**Summary.** Using national housing survey data from 1974–1981, finds that 29% of apartments had no change in nominal rent from one year to the next. Rigidity was far higher for continuing tenants than for units with a new tenant, and higher in small buildings.

**Method assessment.** A careful, widely cited empirical study, but the data are more than 40 years old, from a high-inflation era and before online listings. Its numbers should not be applied to today's Cambridge, though the pattern it documents has been confirmed by later work.

**Relevance.** Early evidence that continuing tenants' rents lag new tenants', the basis of the asked-vs-paid gap.

**Connections.** Gallin and Verbrugge (2019) build a theory to explain these facts.

### Lansing, K. J., Oliveira, L. E., & Shapiro, A. H. (2022, February 14). Will rising rents push up future inflation? *FRBSF Economic Letter*, 2022-03. Federal Reserve Bank of San Francisco. https://www.frbsf.org/research-and-insights/publications/economic-letter/2022/02/will-rising-rents-push-up-future-inflation/

**Summary.** Using 15 metro areas, shows that growth in asking rents (from ZORI) and house prices predicts later growth in the rents counted in official inflation. As new leases are signed at higher asking rents, the average rent of all units rises.

**Method assessment.** A short, non-peer-reviewed policy brief from a reputable research department. Clear and data-based, but brief, and its forecasts were for 2022–2023 specifically.

**Relevance.** Supports reading the project's data as a lag: Cambridge's Census rents rising toward the city's asking rents after 2021 is what this mechanism predicts.

**Connections.** Uses ZORI (Zillow Research, n.d.). Its mechanism is formalized by Adams et al. (2024).

### Ambrose, B. W., Coulson, N. E., & Yoshida, J. (2015). The repeat rent index. *Review of Economics and Statistics, 97*(5), 939–950. https://doi.org/10.1162/REST_a_00500

**Summary.** Builds quarterly repeat-rent indexes for U.S. cities, 2000–2010, from lease data. Finds wide variation across cities, nominal rent declines after 2007 that official data missed, and differences from BLS indexes caused by sampling and construction methods.

**Method assessment.** Peer-reviewed and influential: it introduced the repeat-rent method that ZORI and later research use. The data end in 2010, so its findings about specific cities are dated, but the method is current.

**Relevance.** Shows that how an index is built can change what it says, the same lesson as the project's seven-source comparison.

**Connections.** Methodological ancestor of ZORI and of Adams et al. (2024).

---

## Theme 3: Rental listings as research data

### Boeing, G., & Waddell, P. (2017). New insights into rental housing markets across the United States: Web scraping and analyzing Craigslist rental listings. *Journal of Planning Education and Research, 37*(4), 457–476. https://doi.org/10.1177/0739456X16664789

**Summary.** Collects and analyzes about 11 million Craigslist rental listings across U.S. metro areas. Shows that listings reveal fine-grained, current rent patterns that census data lack, and that in some metros only a small share of listings fall below HUD's Fair Market Rent.

**Method assessment.** Innovative and peer-reviewed, with clear documentation of cleaning steps. Limits the authors discuss: listings are asking prices, not signed leases; duplicates and errors need filtering; and coverage depends on one platform. The data predate today's mix of listing sites.

**Relevance.** A model for how the project could collect its own neighborhood-level listings for Cambridge, and a warning about the cleaning that requires.

**Connections.** Followed by Boeing et al. (2023). The city's own series is also listing-based, but undocumented by comparison.

### Boeing, G., Wegmann, J., & Jiao, J. (2023). Rental housing spot markets: How online information exchanges can supplement transacted-rents data. *Journal of Planning Education and Research, 43*(3), 525–537. https://doi.org/10.1177/0739456X20904435

**Summary.** Distinguishes the "transacted market" (what existing renters pay, as in the ACS) from the "spot market" (asking rents a home-seeker faces). Comparing millions of listings with government data, finds that asking rents diverge substantially from official estimates, especially in tight, expensive markets.

**Method assessment.** Peer-reviewed, with a large dataset and an explicit comparison design. The main limit is that listings are not leases. It also shares the platform-coverage issues of the 2017 study.

**Relevance.** The closest published parallel to this project. Its spot vs. transacted framing matches the asked-vs-paid comparison, and its finding matches the Cambridge result for most years. The narrowing seen in Cambridge after 2021 is a twist worth discussing against it.

**Connections.** Compares listings to both the ACS and HUD FMRs, the same two benchmarks used here. Explains the gap empirically where Adams et al. (2024) explain it with government microdata.

---

## Gaps in this literature

- No source here studies Cambridge specifically, or a college town with a large graduate student population.
- None audits a city government's own listing-based rent series. This project's finding that the city series grows much less than HUD and Census figures has no direct precedent in these sources.
- The Census cap changes (2020, 2024) are rarely accounted for in published comparisons.
