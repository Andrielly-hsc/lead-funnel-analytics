"""Shared figure style: one visual identity for every chart in the project.

Rules (from a validated, colour-blind-safe reference palette):

* **Colour follows the entity, never its rank.** Each channel and each lead source has
  a fixed colour (``CHANNEL_COLORS``, ``SOURCE_COLORS``), the same in every chart and
  regardless of which categories a filter leaves on screen.
* Categorical hues are assigned in a fixed slot order, never cycled. Three of them sit
  below 3:1 contrast on the light surface, so categorical marks always carry **direct
  labels** (validator WARN: "relief required").
* **Sequential** data (magnitudes, heatmaps) uses one hue, light → dark (``SEQUENTIAL``).
* **Status** colours (good/critical) are reserved for pass/fail and always ship with an
  icon + label, never colour alone.
* **One axis**: no dual-axis charts; two measures → two panels.
* Titles state the finding; axes carry units; uncertainty is shown (CI whiskers);
  group sizes are shown wherever rates are compared.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: figures are written to files, never shown

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

logger = logging.getLogger(__name__)

# ---- tokens ---------------------------------------------------------------------
SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e4e3df"
NEUTRAL = "#8a8984"  # reference lines, "other"
SERIES = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948")
SEQUENTIAL = (
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5",
    "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b",
)  # fmt: skip
STATUS_GOOD = "#0ca30c"
STATUS_CRITICAL = "#d03b3b"

# ---- fixed entity colours (colour follows the entity) ---------------------------
CHANNEL_COLORS = {
    "web_form": SERIES[0],
    "email": SERIES[1],
    "phone": SERIES[2],
    "partner_referral": SERIES[3],
}
SOURCE_COLORS = {
    "organic_search": SERIES[0],
    "paid_search": SERIES[1],
    "social": SERIES[2],
    "event": SERIES[3],
    "partner": SERIES[4],
    "direct": SERIES[5],
}
LABELS = {
    "web_form": "Web form",
    "email": "E-mail",
    "phone": "Phone",
    "partner_referral": "Partner referral",
    "organic_search": "Organic search",
    "paid_search": "Paid search",
    "social": "Social",
    "event": "Event",
    "partner": "Partner",
    "direct": "Direct",
}


def label(value: str) -> str:
    """Display label for a category code."""
    return LABELS.get(value, str(value).replace("_", " ").capitalize())


def apply_style() -> None:
    """Recessive axes and grid, readable text, consistent surface."""
    plt.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.labelcolor": TEXT_SECONDARY,
            "axes.edgecolor": GRID,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "xtick.color": TEXT_SECONDARY,
            "ytick.color": TEXT_PRIMARY,
            "text.color": TEXT_PRIMARY,
            "legend.frameon": False,
            "lines.linewidth": 2,
            "svg.hashsalt": "lead-funnel",  # deterministic SVG ids
        }
    )


def percent_axis(ax: plt.Axes, axis: str = "y", decimals: int = 0) -> None:
    """Format an axis holding shares (0-1) as percentages."""
    fmt = FuncFormatter(lambda v, _: f"{100 * v:.{decimals}f} %")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)


def bars_with_ci(
    ax: plt.Axes,
    labels: Sequence[str],
    values: Sequence[float],
    lower: Sequence[float],
    upper: Sequence[float],
    counts: Sequence[int],
    colors: Sequence[str],
    *,
    value_format: str = "{:.1%}",
) -> None:
    """Horizontal bars with confidence-interval whiskers and direct labels "value (n=…)".

    Direct labels are mandatory here: several categorical hues are below 3:1 contrast,
    so the value is never conveyed by colour or bar length alone.
    """
    y = range(len(labels))
    xerr = [
        [v - lo for v, lo in zip(values, lower, strict=True)],
        [hi - v for v, hi in zip(values, upper, strict=True)],
    ]
    ax.barh(y, values, height=0.6, color=colors, zorder=2)
    ax.errorbar(values, y, xerr=xerr, fmt="none", ecolor=TEXT_PRIMARY, elinewidth=1.2,
                capsize=3, zorder=3)  # fmt: skip
    right = max(upper)
    for yi, v, n in zip(y, values, counts, strict=True):
        ax.text(right * 1.03, yi, f"{value_format.format(v)}  (n={n:,})", va="center",
                fontsize=9, color=TEXT_PRIMARY)  # fmt: skip
    ax.set_yticks(list(y), labels)
    ax.set_xlim(0, right * 1.45)
    ax.grid(axis="y", visible=False)
    ax.invert_yaxis()  # first category on top


def caption(fig: plt.Figure, text: str) -> None:
    """Small source/method note under the figure."""
    fig.text(0.01, -0.02, text, fontsize=8, color=TEXT_SECONDARY, ha="left", va="top")


def save_fig(fig: plt.Figure, path: Path) -> Path:
    """Save at a fixed resolution (figures come from code, never screenshots)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)
    logger.info("Wrote %s", path)
    return path
