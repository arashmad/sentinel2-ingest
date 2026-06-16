from __future__ import annotations

SUPPORTED_BANDS = frozenset(
    {
        "B01",
        "B02",
        "B03",
        "B04",
        "B05",
        "B06",
        "B07",
        "B08",
        "B8A",
        "B09",
        "B11",
        "B12",
    }
)

DEFAULT_BANDS = ("B02", "B03", "B04", "B08")

THUMBNAIL_BANDS = ("B04", "B03", "B02")
