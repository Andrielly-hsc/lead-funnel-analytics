"""Figure style helpers."""

from __future__ import annotations

from pathlib import Path

from lead_funnel.analysis import viz
from lead_funnel.generator import params as p


def test_every_category_has_a_fixed_colour_and_label() -> None:
    assert set(viz.CHANNEL_COLORS) == set(p.CHANNELS)
    assert set(viz.SOURCE_COLORS) == set(p.SOURCES)
    assert len(set(viz.SOURCE_COLORS.values())) == len(p.SOURCES)  # no colour reused
    assert all(viz.label(c) != c for c in (*p.CHANNELS, *p.SOURCES))


def test_status_colours_are_not_categorical_colours() -> None:
    assert viz.STATUS_GOOD not in viz.SERIES[:6]
    assert viz.STATUS_CRITICAL not in viz.SERIES


def test_sequential_ramp_gets_darker() -> None:
    def lightness(hex_colour: str) -> float:
        r, g, b = (int(hex_colour[i : i + 2], 16) for i in (1, 3, 5))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    values = [lightness(c) for c in viz.SEQUENTIAL]
    assert values == sorted(values, reverse=True)


def test_bars_with_ci_and_save(tmp_path: Path) -> None:
    viz.apply_style()
    fig, ax = viz.plt.subplots()
    viz.bars_with_ci(ax, ["A", "B"], [0.2, 0.3], [0.15, 0.25], [0.25, 0.35], [100, 2000],
                     [viz.SERIES[0], viz.SERIES[1]])  # fmt: skip
    viz.percent_axis(ax, "x")
    texts = [t.get_text() for t in ax.texts]
    assert texts == ["20.0%  (n=100)", "30.0%  (n=2,000)"]
    out = viz.save_fig(fig, tmp_path / "f.png")
    assert out.exists() and out.stat().st_size > 1000
