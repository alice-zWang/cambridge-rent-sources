# Phase 5 summary: the price jump at the Cambridge–Somerville line (2026-11-23)

## What was done

- **Counts first.** The 7.7 km city line has about 1,050 recent sales within 250 m on each side,
  spread along most of the line ([`fig_h17_boundary_map.png`](../../figures/hedonic/fig_h17_boundary_map.png)).
  The counts were reported, and the model rules were written in
  [`SPEC_PHASE5.md`](../../analysis/hedonic/SPEC_PHASE5.md) and committed, before the model ran.
- **Model 5** ([`65_boundary_model.py`](../../analysis/hedonic/65_boundary_model.py)) compares
  similar homes within 250 m of the line, on the same 1 km stretch of it and sold in the same
  quarter, from 2016 to July 2024, the period both cities' files cover.
  - Similar means the same type, size, rooms, age, lot size and distance to a station.
  - Prices may drift gradually with distance on each side. The model allows for that and asks
    whether there is an extra **jump exactly at the line**.

**In plain words:** two condos 100 m apart on either side of the line share the same streets, shops
and T stops. If the Cambridge one sells for more, the difference reflects what changes at the line:
the city.

## Result

**Comparable homes on the Cambridge side sell for about 17% more** than those just across the line
in Somerville. The cautious 95% range is **+6% to +28%** (bootstrap p = 0.009)
([`boundary_model.csv`](boundary_model.csv), [`fig_h18_boundary_jump.png`](../../figures/hedonic/fig_h18_boundary_jump.png)).

| Version (each changes one thing) | Jump | Cautious 95% range |
|---|---|---|
| **Main: within 250 m** | **+17%** | **+6 to +28** |
| Within 100 m (fewer sales) | +16% | −3 to +37 |
| Within 500 m | +16% | +6 to +26 |
| Adding tract income | +17% | +6 to +28 |
| Without distance to station | +17% | +6 to +29 |
| Condos only | +17% | +1 to +32 |
| Without the eastern stretch | +17% | +5 to +28 |
| **Placebo: fake line 400 m inside Cambridge** | −4% | −11 to +4 |
| **Placebo: fake line 400 m inside Somerville** | +1% | −7 to +8 |

- **The jump is stable.** It is 16–17% in every version. The 100 m version has too few sales to
  rule out zero, but its estimate is the same size.
- **The placebo test passes.** At the fake lines, where nothing changes, there is no jump. So the
  main estimate is not just a smooth price gradient running across the area.
- **The map shape matches.** Prices are flat on each side and step up at the line (`fig_h18`).

## What the jump is, and what it is not

- **It is the value of the whole "Cambridge bundle"** for homes near this line. The line changes
  several things at once:
  - which district's schools a family may choose from (both cities use Controlled Choice; no
    fixed assigned school);
  - the tax rate: FY2025 residential, \$6.35 vs \$10.91 per \$1,000;
  - city services, parking rules and anything else tied to the city.
- **Taxes alone could explain a large part of it.** The lower Cambridge tax rate, treated as a
  permanent saving, is worth roughly **8–11%** of a home's value (at 4–6% a year; residential
  exemptions not included). The 17% estimate is above that, but its range (6–28%) includes it.
  So the data **cannot show that anything beyond taxes is priced in**: schools, services or
  reputation might add to it, or might not.
- **Schools: not identifiable**, even at the line.
- **Compared with the five-town result:** across both whole cities, comparable Cambridge homes sold
  about 32% above Somerville ones. At the line it is 17%. So about half of the citywide gap
  remains when location is held nearly fixed. The rest is about *where* in each city homes are.

**Label: suggestive of causal**, for "being in Cambridge rather than Somerville" near this line.

## Caveats

- The state files have **no bathrooms, condition or grade**. If Cambridge-side homes are better
  kept or finished, part of the jump is home quality, not the city.
- **Last sale only** per home, and Somerville's file ends a year earlier (handled by using the
  common period).
- **21 census tracts** in the main sample. The bootstrap is designed for this, but the range is
  still wide.
- The easternmost kilometre has no Somerville sales nearby (rail and industrial land). Dropping it
  changes nothing.

## Files

- Results: `boundary_counts.csv`, `boundary_segments.csv`, `boundary_balance.csv`, `boundary_model.csv`.
- Figures: `fig_h17_boundary_map`, `fig_h18_boundary_jump`.
