"""WGS84 area-of-interest normalization utilities."""

from math import isfinite
from numbers import Real

from shapely.geometry import Polygon

from .errors import InvalidAOIError


def _validate_coordinate(
    name: str,
    value: object,
    minimum: float,
    maximum: float,
) -> float:
    """Return a finite coordinate within an inclusive WGS84 range."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise InvalidAOIError(f"{name} must be a finite number")

    coordinate = float(value)

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
