"""WGS84 area-of-interest normalization tests."""

import math

import pytest
from shapely.geometry import Polygon

from sentinel2_ingest.aoi import normalize_bbox
from sentinel2_ingest.errors import InvalidAOIError


def test_normalize_bbox_returns_a_valid_wgs84_rectangle() -> None:
    """A swapped coordinate order would return a geometrically wrong AOI."""
    polygon = normalize_bbox(-3.2, 40.1, -3.0, 40.3)

    assert isinstance(polygon, Polygon)
    assert polygon.is_valid
    assert list(polygon.exterior.coords) == [
        (-3.2, 40.1),
        (-3.0, 40.1),
        (-3.0, 40.3),
        (-3.2, 40.3),
        (-3.2, 40.1),
    ]
    assert polygon.area == pytest.approx(0.04)


@pytest.mark.parametrize(
    "bounds",
    [
        (-180, -90, 180, 90),
        (-180, 0, -179, 1),
        (179, -1, 180, 0),
    ],
)
def test_normalize_bbox_accepts_wgs84_boundaries(
    bounds: tuple[float, float, float, float],
) -> None:
    """Rejecting a legal edge coordinate would unnecessarily narrow WGS84."""
    assert normalize_bbox(*bounds).is_valid


@pytest.mark.parametrize(
    "bounds",
    [
        (1, 0, 0, 1),
        (170, -1, -170, 1),
        (0, 1, 1, 0),
        (0, 0, 0, 1),
        (0, 0, 1, 0),
        (-181, 0, 0, 1),
        (0, -91, 1, 0),
        (0, 0, 181, 1),
        (0, 0, 1, 91),
        (math.nan, 0, 1, 1),
        (0, 0, math.inf, 1),
        ("0", 0, 1, 1),
        (True, 0, 1, 1),
    ],
)
def test_normalize_bbox_rejects_invalid_bounds(
    bounds: tuple[object, object, object, object],
) -> None:
    """Invalid bounds must not become provider-bound geometry."""
    with pytest.raises(InvalidAOIError):
        normalize_bbox(*bounds)


def test_normalize_bbox_is_not_reexported_from_package_root() -> None:
    """The AOI API must remain explicit rather than become a root import."""
    import sentinel2_ingest

    assert not hasattr(sentinel2_ingest, "normalize_bbox")
