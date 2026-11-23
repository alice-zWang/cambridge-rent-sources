"""Shared helpers for Model 4 (gradient boosting + SHAP), see SPEC_PHASE4.md.

WHAT THIS DOES (plain words)
  - turns the sales table into the numeric feature table a tree model needs;
  - builds the gradient-boosting model with the settings fixed in the spec;
  - computes the "typical change" number (partial-dependence contrast) and binned SHAP curves;
  - adds SHAP values of dummy columns back up to one value per original feature.

Categorical features are coded as numbers, not with the library's native categorical splits,
because SHAP gives wrong values for native categorical splits (see verify_shap.py, check 2).
Ordered categories (condition, grade) get their natural order; unordered ones (home type,
neighborhood) get one 0/1 column per level.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

ORD = {
    "condition": ["Below average", "Average", "Good", "Very Good", "Excellent+"],
    "grade": ["Below average", "Average", "Good", "Very Good", "Excellent+"],
}
HEAD = ["crime_violent_500", "crime_property_500", "log_income", "transit_km"]
BASE = ["log_area", "bedrooms", "fullbaths", "halfbaths", "parking", "year_built", "condition",
        "grade"] + HEAD + ["sale_time"]
NICE = {"log_area": "Living area (log)", "bedrooms": "Bedrooms", "fullbaths": "Full baths",
        "halfbaths": "Half baths", "parking": "Parking spaces", "year_built": "Year built",
        "condition": "Condition", "grade": "Grade", "crime_violent_500": "Violent crime nearby",
        "crime_property_500": "Property crime nearby", "log_income": "Tract income (log)",
        "transit_km": "Distance to station (km)", "sale_time": "Sale date", "group": "Home type",
        "neighborhood": "Neighborhood", "x": "Map x (east-west)", "y": "Map y (north-south)"}

SETTINGS = dict(loss="squared_error", learning_rate=0.05, max_leaf_nodes=31, min_samples_leaf=20,
                l2_regularization=1.0, max_iter=3000, early_stopping=True, validation_fraction=0.1,
                n_iter_no_change=50)


def make_model(seed=0):
    return HistGradientBoostingRegressor(random_state=seed, **SETTINGS)


def sale_time(dates):
    dates = pd.to_datetime(dates)
    return dates.dt.year + (dates.dt.dayofyear - 1) / 365.25


def build_X(df, version="G1", xy=None):
    """Feature table for version G1 (no location IDs), G2 (+ neighborhood) or G3 (+ x, y).

    Returns (X, groups), where groups maps each original feature to its column(s) in X.
    One-hot columns are built from all levels in df, so a level absent from a training fold
    is still a column (all zeros there).
    """
    X = pd.DataFrame(index=df.index)
    for c in ["log_area", "bedrooms", "fullbaths", "halfbaths", "parking"] + HEAD:
        X[c] = df[c].astype(float)
    yb = df["condition_yearbuilt"].astype(float)
    X["year_built"] = yb.where(yb.between(1700, 2027))          # invalid -> missing
    for c, levels in ORD.items():
        X[c] = df[c].map({lv: i for i, lv in enumerate(levels)}).astype(float)
    X["sale_time"] = sale_time(df["saledate"])
    groups = {c: [c] for c in BASE}
    cats = ["group"] + (["neighborhood"] if version == "G2" else [])
    for c in cats:
        d = pd.get_dummies(df[c], prefix=c, dtype=float)
        X = pd.concat([X, d], axis=1)
        groups[c] = list(d.columns)
    if version == "G3":
        X["x"], X["y"] = xy[:, 0], xy[:, 1]
        groups["x"], groups["y"] = ["x"], ["y"]
    return X, groups


def feature_shap(sv, X, groups):
    """Sum SHAP columns per original feature -> DataFrame (rows x features)."""
    cols = list(X.columns)
    return pd.DataFrame({f: sv[:, [cols.index(c) for c in cs]].sum(1) for f, cs in groups.items()},
                        index=X.index)


def feature_interactions(iv, X, groups):
    """Sum a (n x p x p) SHAP interaction array into feature blocks -> (n x F x F), names."""
    cols = list(X.columns)
    names = list(groups)
    idx = [[cols.index(c) for c in groups[f]] for f in names]
    out = np.zeros((iv.shape[0], len(names), len(names)))
    for a, ia in enumerate(idx):
        for b, ib in enumerate(idx):
            out[:, a, b] = iv[:, ia][:, :, ib].sum((1, 2))
    return out, names


def pd_contrast(model, X, col, lo, hi):
    """Partial-dependence contrast: mean prediction with X[col]=hi minus with X[col]=lo (log)."""
    a, b = X.copy(), X.copy()
    a[col], b[col] = hi, lo
    return float(np.mean(model.predict(a)) - np.mean(model.predict(b)))


def binned_curve(values, shap_col, edges):
    """Mean SHAP value per bin of the feature (bins given by edges); NaN for empty bins."""
    b = np.digitize(values, edges[1:-1])
    return np.array([shap_col[b == k].mean() if np.any(b == k) else np.nan
                     for k in range(len(edges) - 1)])


def pct(d):
    return 100 * (np.exp(d) - 1)
