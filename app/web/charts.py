from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from io import StringIO
from typing import Iterable

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from app.web.preferences import (
    PresentationPreferences,
)

PALETTES: dict[str, tuple[str, ...]] = {
    "standard": (
        "#2f7e79",
        "#5177a8",
        "#9a77b7",
        "#d59655",
        "#6f9f7d",
        "#7e8ea3",
        "#b67b86",
        "#7e6f9b",
    ),
    "red_green_safe": (
        "#0072B2",
        "#E69F00",
        "#56B4E9",
        "#CC79A7",
        "#F0E442",
        "#000000",
        "#999999",
        "#D55E00",
    ),
    "blue_yellow_safe": (
        "#8B1A1A",
        "#6A3D9A",
        "#E67E22",
        "#1F1F1F",
        "#C44E52",
        "#8C6D31",
        "#6B6B6B",
        "#A65628",
    ),
}


@dataclass(frozen=True)
class ChartTheme:
    background: str
    panel: str
    text: str
    muted: str
    grid: str


def chart_theme(
    preferences: PresentationPreferences,
) -> ChartTheme:
    if preferences.theme == "dark":
        return ChartTheme(
            background="#0f1718",
            panel="#172224",
            text="#e9efed",
            muted="#9fafaa",
            grid="#334143",
        )

    return ChartTheme(
        background="#ffffff",
        panel="#ffffff",
        text="#17312c",
        muted="#667773",
        grid="#e1e8e5",
    )


def _money(value: float, _position: int) -> str:
    if abs(value) >= 1000:
        return (
            "R$ "
            f"{value / 1000:.1f}k"
        )
    return f"R$ {value:.0f}"


def _svg_from_figure(
    figure: plt.Figure,
) -> str:
    stream = StringIO()
    figure.savefig(
        stream,
        format="svg",
        bbox_inches="tight",
        transparent=False,
    )
    plt.close(figure)
    return stream.getvalue()


def category_chart_svg(
    rows: Iterable[
        tuple[str, Decimal]
    ],
    preferences: PresentationPreferences,
) -> str:
    data = list(rows)[:8]
    theme = chart_theme(preferences)
    colors = PALETTES[
        preferences.palette
    ]

    figure, axis = plt.subplots(
        figsize=(8.2, 4.8),
    )
    figure.patch.set_facecolor(
        theme.background
    )
    axis.set_facecolor(theme.panel)

    if not data:
        axis.text(
            0.5,
            0.5,
            "Sem despesas neste período",
            ha="center",
            va="center",
            color=theme.muted,
            transform=axis.transAxes,
        )
        axis.axis("off")
        return _svg_from_figure(
            figure
        )

    labels = [
        label
        for label, _value in data
    ]
    values = [
        float(value)
        for _label, value in data
    ]

    y_positions = list(
        range(len(data))
    )

    axis.barh(
        y_positions,
        values,
        color=[
            colors[index % len(colors)]
            for index
            in range(len(data))
        ],
        edgecolor=theme.text,
        linewidth=0.4,
    )

    axis.set_yticks(
        y_positions,
        labels=labels,
    )
    axis.invert_yaxis()
    axis.xaxis.set_major_formatter(
        FuncFormatter(_money)
    )
    axis.grid(
        axis="x",
        alpha=0.35,
        color=theme.grid,
    )
    axis.set_axisbelow(True)

    for spine in axis.spines.values():
        spine.set_visible(False)

    axis.tick_params(
        colors=theme.muted,
        labelsize=9,
    )

    axis.set_title(
        "Gastos por categoria",
        loc="left",
        color=theme.text,
        fontsize=13,
        fontweight="bold",
        pad=14,
    )

    return _svg_from_figure(
        figure
    )


def comparison_chart_svg(
    current_total: Decimal,
    previous_total: Decimal,
    preferences: PresentationPreferences,
) -> str:
    theme = chart_theme(preferences)
    colors = PALETTES[
        preferences.palette
    ]

    figure, axis = plt.subplots(
        figsize=(6.8, 4.2),
    )
    figure.patch.set_facecolor(
        theme.background
    )
    axis.set_facecolor(theme.panel)

    labels = [
        "Mês anterior",
        "Mês atual",
    ]
    values = [
        float(previous_total),
        float(current_total),
    ]

    axis.bar(
        labels,
        values,
        color=(
            colors[1 % len(colors)],
            colors[0],
        ),
        edgecolor=theme.text,
        linewidth=0.4,
        width=0.56,
    )

    axis.yaxis.set_major_formatter(
        FuncFormatter(_money)
    )
    axis.grid(
        axis="y",
        alpha=0.35,
        color=theme.grid,
    )
    axis.set_axisbelow(True)

    for spine in axis.spines.values():
        spine.set_visible(False)

    axis.tick_params(
        colors=theme.muted,
        labelsize=9,
    )
    axis.set_title(
        "Ritmo de gastos",
        loc="left",
        color=theme.text,
        fontsize=13,
        fontweight="bold",
        pad=14,
    )

    return _svg_from_figure(
        figure
    )
