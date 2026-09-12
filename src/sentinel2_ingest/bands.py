"""Provider-neutral Sentinel-2 Level-2A reflectance band catalog."""

from collections.abc import Iterable
from enum import StrEnum
from typing import Self

from .errors import InvalidBandError


class Band(StrEnum):
    """A supported Sentinel-2 Level-2A reflectance band."""

    B01 = ("B01", 60, "Coastal aerosol", "coastal")
    B02 = ("B02", 10, "Blue", "blue")
    B03 = ("B03", 10, "Green", "green")
    B04 = ("B04", 10, "Red", "red")
    B05 = ("B05", 20, "Red edge 1", "rededge1")
    B06 = ("B06", 20, "Red edge 2", "rededge2")
    B07 = ("B07", 20, "Red edge 3", "rededge3")
    B08 = ("B08", 10, "Near infrared", "nir")
    B8A = ("B8A", 20, "Narrow near infrared", "nir08")
    B09 = ("B09", 60, "Water vapour", "nir09")
    B11 = ("B11", 20, "Short-wave infrared 1", "swir16")
    B12 = ("B12", 20, "Short-wave infrared 2", "swir22")

    resolution: int
    display_name: str
    earth_search_name: str

    def __new__(
        cls,
        identifier: str,
        resolution: int,
        display_name: str,
        earth_search_name: str,
    ) -> Self:
        member = str.__new__(cls, identifier)
        member._value_ = identifier
        member.resolution = resolution
        member.display_name = display_name
        member.earth_search_name = earth_search_name
        return member

    @classmethod
    def _missing_(cls, value: object) -> Self | None:
        if isinstance(value, str):
            return cls.__members__.get(value.upper())
        return None

    @classmethod
    def parse(cls, value: str | Self) -> Self:
        """Return a catalog member, normalizing a string identifier's case."""
        if isinstance(value, cls):
            return value
        band = cls.__members__.get(value.upper())
        if band is None:
            raise InvalidBandError(f"{value!r} is unsupported")
        return band


DEFAULT_BANDS = (Band.B04, Band.B03, Band.B02)
"""Default true-color band order: red, green, blue."""


def validate_bands(bands: Iterable[Band | str]) -> tuple[Band, ...]:
    """Normalize requested bands and reject duplicate identifiers."""
    normalized_bands = tuple(Band.parse(band) for band in bands)
    if len(set(normalized_bands)) != len(normalized_bands):
        raise InvalidBandError("duplicate bands are not allowed")
    return normalized_bands
