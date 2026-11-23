"""Step 75: how much do crime, income and transit vary WITHIN neighborhoods? (report finding 2)

WHAT THIS DOES (plain words)
  Model 1 compares homes within the same neighborhood. A factor that barely changes inside a
  neighborhood leaves the model little to learn from, so a "no measurable difference" result
  says nothing about differences BETWEEN neighborhoods. For each headline factor, this splits the
  variation across sales into a between-neighborhood part and a within-neighborhood part, and
  reports the typical within-neighborhood spread next to the citywide spread.

OUTPUTS
  results/hedonic/within_neighborhood_variation.csv

RUN
  uv run python analysis/hedonic/75_within_variation.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from model_common import HEAD, LABEL, RES, load  # noqa: E402

_, d = load("market_sample")
rows = []
for v in HEAD:
    x = d[v].astype(float)
    nb_mean = x.groupby(d["neighborhood"]).transform("mean")
    within = x - nb_mean
    total_var, within_var = x.var(), within.var()
    iqr_by_nb = x.groupby(d["neighborhood"]).quantile(0.75) - x.groupby(d["neighborhood"]).quantile(0.25)
    nb_means = x.groupby(d["neighborhood"]).mean()
    rows.append({"variable": v, "label": LABEL[v],
                 "citywide_p25": x.quantile(0.25), "citywide_p75": x.quantile(0.75),
                 "citywide_iqr": x.quantile(0.75) - x.quantile(0.25),
                 "median_within_neighborhood_iqr": iqr_by_nb.median(),
                 "neighborhood_mean_min": nb_means.min(), "neighborhood_mean_max": nb_means.max(),
                 "sd_total": np.sqrt(total_var), "sd_within": np.sqrt(within_var),
                 "share_variance_within": within_var / total_var})
    if v == "log_income":                           # also on the dollar scale, for the report
        inc = np.exp(x)
        iqr_d = inc.groupby(d["neighborhood"]).quantile(0.75) - inc.groupby(d["neighborhood"]).quantile(0.25)
        m = inc.groupby(d["neighborhood"]).mean()
        rows.append({"variable": "income_dollars", "label": "Tract median income ($)",
                     "citywide_p25": inc.quantile(0.25), "citywide_p75": inc.quantile(0.75),
                     "citywide_iqr": inc.quantile(0.75) - inc.quantile(0.25),
                     "median_within_neighborhood_iqr": iqr_d.median(),
                     "neighborhood_mean_min": m.min(), "neighborhood_mean_max": m.max(),
                     "sd_total": inc.std(), "sd_within": (inc - inc.groupby(d["neighborhood"]).transform("mean")).std(),
                     "share_variance_within": (inc - inc.groupby(d["neighborhood"]).transform("mean")).var() / inc.var()})
out = pd.DataFrame(rows)
out.to_csv(RES / "within_neighborhood_variation.csv", index=False)
pd.set_option("display.width", 220)
print(out.round(3).to_string(index=False))
print("\nnote: crime is per 100 reports per km2 per year; transit in km")
