from __future__ import annotations

from dataclasses import dataclass

THEMES = {"light", "dark"}
PALETTES = {
    "standard",
    "red_green_safe",
    "blue_yellow_safe",
}
LAYOUTS = {
    "balanced",
    "compact",
    "analysis",
}


@dataclass(frozen=True)
class PresentationPreferences:
    theme: str = "light"
    palette: str = "standard"
    layout: str = "balanced"


def normalize_theme(value: str | None) -> str:
    if value in THEMES:
        return value
    return "light"


def normalize_palette(value: str | None) -> str:
    if value in PALETTES:
        return value
    return "standard"


def normalize_layout(value: str | None) -> str:
    if value in LAYOUTS:
        return value
    return "balanced"


def load_preferences(
    *,
    theme: str | None,
    palette: str | None,
    layout: str | None,
) -> PresentationPreferences:
    return PresentationPreferences(
        theme=normalize_theme(theme),
        palette=normalize_palette(palette),
        layout=normalize_layout(layout),
    )
