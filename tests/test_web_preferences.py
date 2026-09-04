from app.web.preferences import (
    PresentationPreferences,
    load_preferences,
    normalize_layout,
    normalize_palette,
    normalize_theme,
)


def test_invalid_theme_falls_back_to_light():
    assert normalize_theme(
        "unknown"
    ) == "light"


def test_invalid_palette_falls_back_to_standard():
    assert normalize_palette(
        "unknown"
    ) == "standard"


def test_invalid_layout_falls_back_to_balanced():
    assert normalize_layout(
        "unknown"
    ) == "balanced"


def test_load_preferences_accepts_supported_values():
    assert load_preferences(
        theme="dark",
        palette="red_green_safe",
        layout="analysis",
    ) == PresentationPreferences(
        theme="dark",
        palette="red_green_safe",
        layout="analysis",
    )
