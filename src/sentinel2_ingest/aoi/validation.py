from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from shapely.validation import explain_validity

from sentinel2_ingest.exceptions import InvalidAoiError


def validate_single_polygon_aoi(aoi: Mapping[str, Any]) -> dict[str, Any]:
    """Validate that an AOI is a valid GeoJSON Polygon geometry.

    V1 intentionally supports only single Polygon geometries.

    Supported:
    - GeoJSON Polygon geometry

    Not supported:
    - Feature
    - FeatureCollection
    - MultiPolygon
    - GeometryCollection
    - Point / LineString
    - empty or self-intersecting geometries
    """
    if not isinstance(aoi, Mapping):
        raise InvalidAoiError("AOI must be a GeoJSON geometry object.")

    aoi_type = aoi.get("type")

    if aoi_type == "Feature":
        raise InvalidAoiError(
            "AOI must be a GeoJSON Polygon geometry, not a Feature. "
            "Pass the Feature's geometry instead."
        )

    if aoi_type == "FeatureCollection":
        raise InvalidAoiError(
            "AOI must be a GeoJSON Polygon geometry, not a FeatureCollection."
        )

    if aoi_type != "Polygon":
        raise InvalidAoiError(
            f"AOI must be a GeoJSON Polygon geometry. Received: {aoi_type!r}."
        )

    geometry = _parse_geometry(aoi)
    _validate_geometry(geometry)

    return dict(aoi)


def _parse_geometry(aoi: Mapping[str, Any]) -> BaseGeometry:
    try:
        return shape(aoi)
    except Exception as exc:
        raise InvalidAoiError(f"AOI is not valid GeoJSON geometry: {exc}") from exc


def _validate_geometry(geometry: BaseGeometry) -> None:
    if geometry.is_empty:
        raise InvalidAoiError("AOI Polygon must not be empty.")

    if geometry.geom_type != "Polygon":
        raise InvalidAoiError(
            f"AOI must be a single Polygon geometry. Received: {geometry.geom_type}."
        )

    if not geometry.is_valid:
        reason = explain_validity(geometry)
        raise InvalidAoiError(f"AOI Polygon is invalid: {reason}.")