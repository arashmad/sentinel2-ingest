"""WGS84 area-of-interest normalization utilities."""

from collections.abc import Iterable, Mapping, Sequence
from math import isfinite
from numbers import Real

from shapely.geometry import MultiPolygon, Polygon, shape

from .errors import InvalidAOIError


def _validate_coordinate(
    name: str,
    value: object,
    minimum: float,
    maximum: float,
) -> float:
    """Return a finite coordinate within an inclusive WGS84 range.

    Args:
        name: Human-readable coordinate name used in validation errors.
        value: Numeric coordinate value to convert to a float.
        minimum: Inclusive lower WGS84 bound in degrees.
        maximum: Inclusive upper WGS84 bound in degrees.

    Returns:
        The validated coordinate as a finite float.

    Raises:
        InvalidAOIError: If the value is non-numeric, non-finite, or outside
            the supplied inclusive range.
    """
    if isinstance(value, bool) or not isinstance(value, Real):
        raise InvalidAOIError(f"{name} must be a finite number")

    # ? Catch `OverflowError` when for too large float number (e.g. 10**400).
    try:
        coordinate = float(value)
    except OverflowError as error:
        raise InvalidAOIError(f"{name} must be a finite number") from error

    if not isfinite(coordinate):
        raise InvalidAOIError(f"{name} must be a finite number")

    if not minimum <= coordinate <= maximum:
        raise InvalidAOIError(
            f"{name} must be between {minimum:g} and {maximum:g} degrees"
        )
    return coordinate


def normalize_bbox(
    west: object,
    south: object,
    east: object,
    north: object,
) -> Polygon:
    """Convert WGS84 bounds into a validated rectangular polygon.

    Args:
        west: Western longitude in degrees, in the inclusive range ``[-180, 180]``.
        south: Southern latitude in degrees, in the inclusive range ``[-90, 90]``.
        east: Eastern longitude in degrees, in the inclusive range ``[-180, 180]``.
        north: Northern latitude in degrees, in the inclusive range ``[-90, 90]``.

    Returns:
        A valid rectangular Shapely polygon with ``EPSG:4326`` longitude/latitude
        coordinates. Shapely does not attach CRS metadata to the geometry.

    Raises:
        InvalidAOIError: If a bound is non-numeric or non-finite, outside WGS84
            limits, does not enclose area, or crosses the antimeridian.
    """
    normalized_west = _validate_coordinate("west", west, -180, 180)
    normalized_south = _validate_coordinate("south", south, -90, 90)
    normalized_east = _validate_coordinate("east", east, -180, 180)
    normalized_north = _validate_coordinate("north", north, -90, 90)

    if normalized_west == normalized_east:
        raise InvalidAOIError("west and east must enclose positive width")

    if normalized_west > normalized_east:
        raise InvalidAOIError("antimeridian-crossing boxes are unsupported")

    if normalized_south == normalized_north:
        raise InvalidAOIError("south and north must enclose positive height")

    if normalized_south > normalized_north:
        raise InvalidAOIError("south must be less than north")

    return Polygon(
        [
            (normalized_west, normalized_south),
            (normalized_east, normalized_south),
            (normalized_east, normalized_north),
            (normalized_west, normalized_north),
            (normalized_west, normalized_south),
        ]
    )


def _validate_ring_coordinates(coordinates: Iterable[Sequence[float]]) -> None:
    """Validate a WGS84 ring and reject antimeridian-crossing edges.

    Args:
        coordinates: Ordered coordinate sequences for an exterior or interior
            polygon ring. Each coordinate must provide longitude and latitude
            as its first two values.
    """
    ring = list(coordinates)
    for coordinate in ring:
        if len(coordinate) < 2:
            raise InvalidAOIError("coordinates must contain longitude and latitude")
        longitude, latitude = coordinate[:2]
        if not isfinite(longitude) or not isfinite(latitude):
            raise InvalidAOIError("coordinates must be finite WGS84 values")
        if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
            raise InvalidAOIError("coordinates must be within WGS84 bounds")

    for coordinate, next_coordinate in zip(ring, ring[1:], strict=False):
        longitude = coordinate[0]
        next_longitude = next_coordinate[0]
        if abs(next_longitude - longitude) > 180:
            raise InvalidAOIError("antimeridian-crossing polygons are unsupported")


def _validate_polygon(polygon: Polygon) -> Polygon:
    """Return a valid, non-empty WGS84 polygon without modifying it.

    Args:
        polygon: A Shapely Polygon whose exterior and interior-ring coordinates
            are expected to be WGS84 longitude/latitude values.

    Returns:
        The original Polygon after validating its geometry, coordinate bounds,
        and antimeridian edges.
    """
    if polygon.is_empty:
        raise InvalidAOIError("polygon must not be empty")
    if not polygon.is_valid:
        raise InvalidAOIError("polygon must be valid")
    if polygon.area <= 0:
        raise InvalidAOIError("polygon must enclose positive area")

    _validate_ring_coordinates(polygon.exterior.coords)
    for interior in polygon.interiors:
        _validate_ring_coordinates(interior.coords)
    return polygon


def normalize_aoi(value: object) -> Polygon:
    """Normalize a WGS84 Polygon or singleton MultiPolygon area of interest.

    Args:
        value: A Shapely :class:`~shapely.geometry.Polygon`, a Shapely
            :class:`~shapely.geometry.MultiPolygon` containing exactly one
            polygon, or a GeoJSON geometry mapping of either form. GeoJSON
            coordinates are interpreted as WGS84 longitude/latitude values.

    Returns:
        A validated Shapely Polygon that preserves the input's exterior and
        interior rings. Shapely geometries do not carry CRS metadata.

    Raises:
        InvalidAOIError: If the input is not a valid, non-empty WGS84 Polygon,
            is a MultiPolygon with other than one member, or crosses the
            antimeridian.
    """
    geometry: object = value
    if isinstance(value, Mapping):
        try:
            geometry = shape(dict(value))
        except (
            AttributeError,
            KeyError,
            NotImplementedError,
            OverflowError,
            TypeError,
            ValueError,
        ) as error:
            raise InvalidAOIError("must be a valid GeoJSON geometry mapping") from error

    if isinstance(geometry, MultiPolygon):
        if len(geometry.geoms) != 1:
            raise InvalidAOIError("MultiPolygon must contain exactly one polygon")
        geometry = geometry.geoms[0]

    if not isinstance(geometry, Polygon):
        raise InvalidAOIError("must be a Polygon or singleton MultiPolygon")
    return _validate_polygon(geometry)
