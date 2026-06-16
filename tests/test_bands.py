from __future__ import annotations

from sentinel2_ingest import DEFAULT_BANDS, SUPPORTED_BANDS, THUMBNAIL_BANDS


def test_supported_bands_contains_expected_sentinel2_l2a_raw_bands() -> None:
    assert {
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
    } == SUPPORTED_BANDS


def test_supported_bands_excludes_b10() -> None:
    assert "B10" not in SUPPORTED_BANDS


def test_default_bands_are_supported() -> None:
    assert DEFAULT_BANDS == ("B02", "B03", "B04", "B08")
    assert set(DEFAULT_BANDS).issubset(SUPPORTED_BANDS)


def test_thumbnail_bands_are_supported_rgb_order() -> None:
    assert THUMBNAIL_BANDS == ("B04", "B03", "B02")
    assert set(THUMBNAIL_BANDS).issubset(SUPPORTED_BANDS)


def test_supported_bands_is_immutable() -> None:
    assert isinstance(SUPPORTED_BANDS, frozenset)
