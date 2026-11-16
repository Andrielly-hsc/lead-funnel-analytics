"""Shared figure style: one visual identity for every chart in the project.

Colour tokens follow a validated, colour-blind-safe reference palette:

* categorical series use the fixed slot order (never cycled);
* status colours (good/critical) are reserved for pass/fail and always ship with an
  icon + label, never colour alone;
* text uses text tokens, never a series colour.

F07-T04 extends this module (categorical helpers, small multiples, CI bands).
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: figures are written to files, never shown

import matplotlib.pyplot as plt  # noqa: E402

logger = logging.getLogger(__name__)

SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e4e3df"
SERIES = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948")
STATUS_GOOD = "#0ca30c"
STATUS_CRITICAL = "#d03b3b"


def apply_style() -> None:
    """Recessive axes and grid, readable text, consistent surface."""
    plt.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.labelcolor": TEXT_SECONDARY,
            "axes.edgecolor": GRID,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "xtick.color": TEXT_SECONDARY,
            "ytick.color": TEXT_PRIMARY,
            "text.color": TEXT_PRIMARY,
            "legend.frameon": False,
            "svg.hashsalt": "lead-funnel",  # deterministic SVG ids
        }
    )


def save_fig(fig: plt.Figure, path: Path) -> Path:
    """Save at a fixed size and resolution (figures come from code, never screenshots)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", metadata={"Software": None})
    plt.close(fig)
    logger.info("Wrote %s", path)
    return path
