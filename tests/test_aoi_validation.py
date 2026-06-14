from __future__ import annotations

import pytest

from sentinel2_ingest.aoi import validate_single_polygon_aoi
from sentinel2_ingest.exceptions import InvalidAoiError

VALID_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [13.0, 52.0],
            [13.1, 52.0],
            [13.1, 52.1],
            [13.0, 52.1],
            [13.0, 52.0],
        ]
    ],
}


def test_valid_polygon_passes() -> None:
    result = validate_single_polygon_aoi(VALID_POLYGON)

    assert result == VALID_POLYGON


def test_multipolygon_fails() -> None:
    aoi = {
        "type": "MultiPolygon",
        "coordinates": [
            [
                [
                    [13.0, 52.0],
                    [13.1, 52.0],
                    [13.1, 52.1],
                    [13.0, 52.1],
                    [13.0, 52.0],
                ]
            ]
        ],
    }

    with pytest.raises(InvalidAoiError, match="Polygon"):
        validate_single_polygon_aoi(aoi)


def test_feature_fails_with_clear_message() -> None:
    aoi = {
        "type": "Feature",
        "properties": {},
        "geometry": VALID_POLYGON,
    }

    with pytest.raises(InvalidAoiError, match="Feature"):
        validate_single_polygon_aoi(aoi)


def test_feature_collection_fails_with_clear_message() -> None:
    aoi = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": VALID_POLYGON,
            }
        ],
    }

    with pytest.raises(InvalidAoiError, match="FeatureCollection"):
        validate_single_polygon_aoi(aoi)


def test_self_intersecting_polygon_fails() -> None:
    aoi = {
        "type": "Polygon",
        "coordinates": [
            [
                [0.0, 0.0],
                [1.0, 1.0],
                [1.0, 0.0],
                [0.0, 1.0],
                [0.0, 0.0],
            ]
        ],
    }

    with pytest.raises(InvalidAoiError, match="invalid"):
        validate_single_polygon_aoi(aoi)


def test_empty_polygon_fails() -> None:
    aoi = {
        "type": "Polygon",
        "coordinates": [],
    }

    with pytest.raises(InvalidAoiError):
        validate_single_polygon_aoi(aoi)


def test_non_mapping_aoi_fails() -> None:
    with pytest.raises(InvalidAoiError, match="GeoJSON"):
        validate_single_polygon_aoi("not-a-geojson-object")  # type: ignore[arg-type]
