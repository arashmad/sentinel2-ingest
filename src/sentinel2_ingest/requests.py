"""Validated public inputs for Sentinel-2 inspection and download workflows."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from math import isfinite
from numbers import Integral, Real
from pathlib import Path
from typing import Any, cast

from shapely.geometry import Polygon, mapping

from .aoi import normalize_aoi
from .bands import DEFAULT_BANDS, Band, validate_bands
from .errors import InvalidDateError, InvalidResolutionError, OutputError
from .quality import QualityPolicy

DEFAULT_MAX_CLOUD_COVER = 80.0
"""Default inclusive catalog cloud-cover filter, expressed as a percentage."""

DEFAULT_CANDIDATE_LIMIT = 20
"""Default maximum number of catalog candidates to inspect."""

SUPPORTED_OUTPUT_RESOLUTIONS = frozenset({10, 20, 60})
"""Output resolutions, in metres, supported by the Sentinel-2 workflows."""


def _normalize_date(name: str, value: object) -> date:
    """Return a date from a date object or canonical ISO-8601 date string."""
    if isinstance(value, datetime):
        raise InvalidDateError(f"{name} must be a date or ISO-8601 date string")
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise InvalidDateError(f"{name} must be a date or ISO-8601 date string")

    try:
        normalized = date.fromisoformat(value)
    except ValueError as error:
        raise InvalidDateError(
            f"{name} must be a date or ISO-8601 date string"
        ) from error

    if normalized.isoformat() != value:
        raise InvalidDateError(f"{name} must be a date or ISO-8601 date string")
    return normalized


def _normalize_cloud_cover(value: object) -> float:
    """Return a finite inclusive cloud-cover percentage."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError("max_cloud_cover must be a finite percentage from 0 to 100")
    try:
        normalized = float(value)
    except OverflowError as error:
        raise ValueError(
            "max_cloud_cover must be a finite percentage from 0 to 100"
        ) from error
    if not isfinite(normalized) or not 0 <= normalized <= 100:
        raise ValueError("max_cloud_cover must be a finite percentage from 0 to 100")
    return normalized


def _normalize_candidate_limit(value: object) -> int:
    """Return a positive integral catalog candidate limit."""
    if isinstance(value, bool) or not isinstance(value, Integral) or value < 1:
        raise ValueError("candidate_limit must be a positive integer")
    return int(value)


def _normalize_resolution(value: object) -> int:
    """Return a supported Sentinel-2 output resolution in metres."""
    if (
        isinstance(value, bool)
        or not isinstance(value, Integral)
        or value not in SUPPORTED_OUTPUT_RESOLUTIONS
    ):
        raise InvalidResolutionError("must be one of 10, 20, or 60 metres")
    return int(value)


def _normalize_output_path(value: object) -> Path:
    """Return a non-empty file destination path without touching the filesystem."""
    if not isinstance(value, (str, Path)):
        raise OutputError()
    path = Path(value)
    if not str(value) or str(path) == "." or "\x00" in str(path):
        raise OutputError()
    return path


def _normalize_bool(name: str, value: object) -> bool:
    """Return a real boolean flag rather than accepting truthy values."""
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")
    return value


def _serialize_aoi(aoi: Polygon) -> dict[str, Any]:
    """Return a JSON-ready GeoJSON geometry mapping for a normalized AOI."""
    serialized = mapping(aoi)
    if not isinstance(serialized, Mapping):  # pragma: no cover - Shapely contract
        raise TypeError("Shapely polygon mapping must be a mapping")
    return {
        "type": serialized["type"],
        "coordinates": _json_ready_coordinates(serialized["coordinates"]),
    }


def _json_ready_coordinates(value: object) -> object:
    """Convert Shapely's tuple coordinates to JSON arrays recursively."""
    if isinstance(value, tuple):
        return [_json_ready_coordinates(member) for member in value]
    return value


@dataclass(frozen=True)
class InspectionRequest:
    """Validated parameters for a provider-neutral Sentinel-2 catalog search."""

    aoi: object
    start_date: date | str
    end_date: date | str
    max_cloud_cover: float = DEFAULT_MAX_CLOUD_COVER
    candidate_limit: int = DEFAULT_CANDIDATE_LIMIT
    quality_policy: QualityPolicy = field(default_factory=QualityPolicy)

    def __post_init__(self) -> None:
        """Normalize fields and enforce the inclusive inspection date range."""
        aoi = normalize_aoi(self.aoi)
        start_date = _normalize_date("start_date", self.start_date)
        end_date = _normalize_date("end_date", self.end_date)
        if start_date > end_date:
            raise InvalidDateError("start_date must be on or before end_date")
        if not isinstance(self.quality_policy, QualityPolicy):
            raise ValueError("quality_policy must be a QualityPolicy")

        object.__setattr__(self, "aoi", aoi)
        object.__setattr__(self, "start_date", start_date)
        object.__setattr__(self, "end_date", end_date)
        object.__setattr__(
            self, "max_cloud_cover", _normalize_cloud_cover(self.max_cloud_cover)
        )
        object.__setattr__(
            self, "candidate_limit", _normalize_candidate_limit(self.candidate_limit)
        )

    def to_dict(self) -> dict[str, object]:
        """Return the deterministic JSON-ready representation of this request."""
        return {
            "aoi": _serialize_aoi(cast(Polygon, self.aoi)),
            "start_date": cast(date, self.start_date).isoformat(),
            "end_date": cast(date, self.end_date).isoformat(),
            "max_cloud_cover": self.max_cloud_cover,
            "candidate_limit": self.candidate_limit,
            "quality_policy": self.quality_policy.to_dict(),
        }


@dataclass(frozen=True)
class DownloadBySearchRequest:
    """Validated parameters for inspection followed by automatic download."""

    inspection_request: InspectionRequest
    output_path: Path | str
    bands: tuple[Band | str, ...] = DEFAULT_BANDS
    resolution: int = 10
    allow_risky: bool = False
    overwrite: bool = False

    def __post_init__(self) -> None:
        """Normalize download settings without changing the inspection request."""
        if not isinstance(self.inspection_request, InspectionRequest):
            raise ValueError("inspection_request must be an InspectionRequest")
        object.__setattr__(
            self, "output_path", _normalize_output_path(self.output_path)
        )
        object.__setattr__(self, "bands", validate_bands(self.bands))
        object.__setattr__(self, "resolution", _normalize_resolution(self.resolution))
        object.__setattr__(
            self, "allow_risky", _normalize_bool("allow_risky", self.allow_risky)
        )
        object.__setattr__(
            self, "overwrite", _normalize_bool("overwrite", self.overwrite)
        )

    def to_dict(self) -> dict[str, object]:
        """Return the deterministic JSON-ready representation of this request."""
        return {
            "inspection_request": self.inspection_request.to_dict(),
            "output_path": str(self.output_path),
            "bands": [band.value for band in cast(tuple[Band, ...], self.bands)],
            "resolution": self.resolution,
            "allow_risky": self.allow_risky,
            "overwrite": self.overwrite,
        }


@dataclass(frozen=True)
class DownloadBySceneRequest:
    """Validated parameters for downloading a caller-selected scene."""

    scene_id: str
    aoi: object
    output_path: Path | str
    bands: tuple[Band | str, ...] = DEFAULT_BANDS
    resolution: int = 10
    overwrite: bool = False

    def __post_init__(self) -> None:
        """Normalize explicit-scene download settings and validate its reference."""
        if not isinstance(self.scene_id, str) or not self.scene_id.strip():
            raise ValueError(
                "scene_id must be a non-empty provider-neutral scene reference"
            )
        object.__setattr__(self, "aoi", normalize_aoi(self.aoi))
        object.__setattr__(
            self, "output_path", _normalize_output_path(self.output_path)
        )
        object.__setattr__(self, "bands", validate_bands(self.bands))
        object.__setattr__(self, "resolution", _normalize_resolution(self.resolution))
        object.__setattr__(
            self, "overwrite", _normalize_bool("overwrite", self.overwrite)
        )

    def to_dict(self) -> dict[str, object]:
        """Return the deterministic JSON-ready representation of this request."""
        return {
            "scene_id": self.scene_id,
            "aoi": _serialize_aoi(cast(Polygon, self.aoi)),
            "output_path": str(self.output_path),
            "bands": [band.value for band in cast(tuple[Band, ...], self.bands)],
            "resolution": self.resolution,
            "overwrite": self.overwrite,
        }
