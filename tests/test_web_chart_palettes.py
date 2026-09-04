from app.web.charts import (
    PALETTES,
)


def test_all_chart_palettes_have_multiple_distinct_colors():
    assert {
        "standard",
        "red_green_safe",
        "blue_yellow_safe",
    } == set(PALETTES)

    for palette in PALETTES.values():
        assert len(palette) >= 6
        assert len(set(palette)) == len(
            palette
        )
