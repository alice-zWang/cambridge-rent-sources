"""Step 76: how much did prices of comparable homes change from 2016 to 2025? (report finding 1)

WHAT THIS DOES (plain words)
  Model 1 includes a separate price level for each sale quarter. Averaging those per year gives the
  price change for a COMPARABLE home (same features, same neighborhood), not just the change in
  the average sale price. The change from 2016 to 2025 is then also given after inflation, using
  the Boston-area consumer price index (BLS CPI-U, annual averages, entered by hand; SOURCES.md).

OUTPUTS
  results/hedonic/price_change_2016_2025.csv

RUN
  uv run python analysis/hedonic/76_price_change.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from model_common import RES, ROOT, fit, formula, load  # noqa: E402

_, d = load("market_sample")
r = fit(d, formula())
fe = {k.split("[T.")[1].rstrip("]"): v for k, v in r.params.items() if k.startswith("C(sale_quarter)")}
fe[sorted(d["sale_quarter"].unique())[0]] = 0.0                  # reference quarter (2016Q1)
year_level = pd.Series(fe).groupby(lambda q: int(q[:4])).mean()   # mean log level per year
cpi = pd.read_csv(ROOT / "data" / "raw" / "hedonic" / "manual" / "bls_cpi_u_boston_annual.csv"
                  ).set_index("year")["annual_average"]
rows = []
for y in year_level.index:
    nominal = 100 * (np.exp(year_level[y] - year_level[2016]) - 1)
    infl = 100 * (cpi[y] / cpi[2016] - 1)
    real = 100 * (np.exp(year_level[y] - year_level[2016]) * cpi[2016] / cpi[y] - 1)
    rows.append({"year": y, "nominal_change_vs_2016_pct": nominal, "cpi_change_vs_2016_pct": infl,
                 "real_change_vs_2016_pct": real})
out = pd.DataFrame(rows)
out.to_csv(RES / "price_change_2016_2025.csv", index=False)
print(out.round(1).to_string(index=False))
