"""WGS84 area-of-interest normalization tests."""

import math

import pytest
from shapely.geometry import MultiPolygon, Point, Polygon

from sentinel2_ingest.aoi import normalize_aoi, normalize_bbox
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
        (10**400, 0, 1, 1),
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


@pytest.mark.parametrize(
    "aoi",
    [
        Polygon(
            [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)],
            [[(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5)]],
        ),
        {
            "type": "Polygon",
            "coordinates": [
                [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)],
                [(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5)],
            ],
        },
        MultiPolygon(
            [
                Polygon(
                    [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)],
                    [[(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5)]],
                )
            ]
        ),
        {
            "type": "MultiPolygon",
            "coordinates": [
                [
                    [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)],
                    [
                        (0.5, 0.5),
                        (1.5, 0.5),
                        (1.5, 1.5),
                        (0.5, 1.5),
                        (0.5, 0.5),
                    ],
                ]
            ],
        },
    ],
)
def test_normalize_aoi_returns_wgs84_polygon_with_holes(
    aoi: object,
) -> None:
    """AOI normalization must retain valid Polygon interiors across input forms."""
    polygon = normalize_aoi(aoi)

    assert isinstance(polygon, Polygon)
    assert polygon.is_valid
    assert polygon.area == pytest.approx(3)
    assert len(polygon.interiors) == 1
    assert list(polygon.interiors[0].coords) == [
        (0.5, 0.5),
        (1.5, 0.5),
        (1.5, 1.5),
        (0.5, 1.5),
        (0.5, 0.5),
    ]


@pytest.mark.parametrize(
    "aoi",
    [
        {"type": "Point", "coordinates": [0, 0]},
        Point(0, 0),
        {"type": "Polygon", "coordinates": []},
        Polygon(),
        Polygon([(0, 0), (2, 2), (2, 0), (0, 2), (0, 0)]),
        MultiPolygon(
            [
                Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]),
                Polygon([(2, 0), (3, 0), (3, 1), (2, 1), (2, 0)]),
            ]
        ),
        {
            "type": "MultiPolygon",
            "coordinates": [
                [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]],
                [[(2, 0), (3, 0), (3, 1), (2, 1), (2, 0)]],
            ],
        },
        {"type": "Polygon", "coordinates": [[(181, 0), (181, 1), (180, 1), (181, 0)]]},
        Polygon([(170, 0), (-170, 0), (-170, 1), (170, 1), (170, 0)]),
        Polygon(
            [(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)],
            [[(170, 1), (-170, 1), (-170, 2), (170, 2), (170, 1)]],
        ),
        {"type": "Polygon", "coordinates": "not coordinates"},
    ],
)
def test_normalize_aoi_rejects_unsupported_or_invalid_geometries(aoi: object) -> None:
    """Invalid AOIs must not be repaired or passed to provider requests."""
    with pytest.raises(InvalidAOIError):
        normalize_aoi(aoi)


def test_normalize_aoi_translates_coordinate_overflow_from_geojson() -> None:
    """Oversized GeoJSON coordinates must surface as the public AOI error."""
    aoi = {
        "type": "Polygon",
        "coordinates": [[(0, 0), (10**400, 0), (10**400, 1), (0, 0)]],
    }

    with pytest.raises(InvalidAOIError):
        normalize_aoi(aoi)
