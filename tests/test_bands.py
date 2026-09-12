"""Public Sentinel-2 reflectance band catalog tests."""

import pytest

import sentinel2_ingest

SUPPORTED_BANDS = (
    ("B01", 60, "Coastal aerosol", "coastal"),
    ("B02", 10, "Blue", "blue"),
    ("B03", 10, "Green", "green"),
    ("B04", 10, "Red", "red"),
    ("B05", 20, "Red edge 1", "rededge1"),
    ("B06", 20, "Red edge 2", "rededge2"),
    ("B07", 20, "Red edge 3", "rededge3"),
    ("B08", 10, "Near infrared", "nir"),
    ("B8A", 20, "Narrow near infrared", "nir08"),
    ("B09", 60, "Water vapour", "nir09"),
    ("B11", 20, "Short-wave infrared 1", "swir16"),
    ("B12", 20, "Short-wave infrared 2", "swir22"),
)


@pytest.mark.parametrize(
    ("identifier", "resolution", "display_name", "earth_search_name"),
    SUPPORTED_BANDS,
)
def test_band_catalog_exposes_supported_band_metadata(
    identifier: str,
    resolution: int,
    display_name: str,
    earth_search_name: str,
) -> None:
    """A missing band or incorrect provider metadata must be observable."""
    band_type = getattr(sentinel2_ingest, "Band", None)

    assert band_type is not None
    band = band_type[identifier]
    assert band.value == identifier
    assert band.resolution == resolution
    assert band.display_name == display_name
    assert band.earth_search_name == earth_search_name


def test_default_bands_are_true_color_in_rgb_order() -> None:
    """A changed default must not silently alter rendered true-color imagery."""
    default_bands = getattr(sentinel2_ingest, "DEFAULT_BANDS", None)

    assert default_bands is not None
    assert tuple(band.value for band in default_bands) == ("B04", "B03", "B02")


@pytest.mark.parametrize("value", ("b04", "B04", "b8a"))
def test_parse_normalizes_band_identifier_case(value: str) -> None:
    """Case normalization must preserve the selected catalog member."""
    band_type = getattr(sentinel2_ingest, "Band", None)

    assert band_type is not None
    assert band_type.parse(value).value == value.upper()


@pytest.mark.parametrize("value", ("B10", "B13", "red", ""))
def test_parse_rejects_unsupported_band(value: str) -> None:
    """Unsupported inputs must never reach a provider request."""
    band_type = getattr(sentinel2_ingest, "Band", None)

    assert band_type is not None
    with pytest.raises(sentinel2_ingest.InvalidBandError):
        band_type.parse(value)


def test_direct_enum_lookup_rejects_non_string_value() -> None:
    """Non-string values must remain invalid direct enum inputs."""
    with pytest.raises(ValueError):
        sentinel2_ingest.Band(123)


def test_validate_bands_normalizes_case_and_rejects_duplicates() -> None:
    """Duplicate requests must be rejected after normalization."""
    validate_bands = getattr(sentinel2_ingest, "validate_bands", None)

    assert validate_bands is not None
    assert tuple(band.value for band in validate_bands(("b04", "B03"))) == (
        "B04",
        "B03",
    )
    with pytest.raises(sentinel2_ingest.InvalidBandError):
        validate_bands(("b04", "B04"))
