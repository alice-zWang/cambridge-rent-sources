"""Shared paths and chart styling for the analysis scripts."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
SITE_ASSETS = ROOT / "docs" / "assets"

for folder in (PROCESSED, RESULTS, FIGURES, SITE_ASSETS):
    folder.mkdir(parents=True, exist_ok=True)

# Colorblind-safe pair (blue / orange) plus two extra series colors.
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
TEXT, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e1"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#8a8984",
    "axes.labelcolor": TEXT,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
})


def save(fig, name):
    """Save a figure to figures/ and a copy to docs/assets/ for the website."""
    fig.tight_layout()
    for folder in (FIGURES, SITE_ASSETS):
        fig.savefig(folder / name, dpi=200)
    plt.close(fig)
    print(f"  wrote figures/{name}")


def dollars(ax, axis="y"):
    fmt = matplotlib.ticker.StrMethodFormatter("${x:,.0f}")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)
