"""Shared definitions for the hedonic models (Model 1 as fixed in SPEC_MODEL1.md).

Paths, the headline variables and their labels, the Model 1 formula, the fitting function
(standard errors clustered by census tract), the data loader, and the "% price difference" helper.
Used by 30_hedonic_ols.py, 35_interactions.py and 40_spatial.py so all models share one definition.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed" / "hedonic"
RES = ROOT / "results" / "hedonic"
FIG = ROOT / "figures" / "hedonic"

HEAD = ["crime_violent_500", "crime_property_500", "log_income", "transit_km"]
LABEL = {"crime_violent_500": "Violent crime nearby", "crime_property_500": "Property crime nearby",
         "log_income": "Tract median income", "transit_km": "Distance to nearest station"}
CONTROLS = ("C(group, Treatment('condo')) + log_area + bedrooms + fullbaths + halfbaths"
            " + C(age_group, Treatment('1900-1939')) + C(condition, Treatment('Average'))"
            " + C(grade, Treatment('Average')) + parking")
FE = "C(neighborhood) + C(sale_quarter)"


def formula(head=HEAD, extra=""):
    return f"log_price ~ {' + '.join(head)} + {CONTROLS}{extra} + {FE}"


def fit(df, f, cluster="tract"):
    groups = pd.factorize(df[cluster])[0]
    return smf.ols(f, data=df).fit(cov_type="cluster", cov_kwds={"groups": groups})


def load():
    """All sales with features, and the Model 1 sample (reset index)."""
    df_all = pd.read_csv(PROC / "sales_features.csv", parse_dates=["saledate"])
    return df_all, df_all[df_all["model_sample"]].reset_index(drop=True)


def pct(b, d):
    """% price difference implied by log-price coefficient b for a change d."""
    return 100 * (np.exp(b * d) - 1)
