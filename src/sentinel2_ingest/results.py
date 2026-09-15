"""Validated provider-neutral outputs for Sentinel-2 workflows."""

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from numbers import Integral, Real
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, TypeAlias, cast

from shapely.geometry import Polygon, mapping

from .aoi import normalize_aoi
from .bands import Band, validate_bands

QualityStatus: TypeAlias = Literal["usable", "risky", "unusable"]
"""The only public classifications for a candidate's AOI quality."""


def _nonempty_string(name: str, value: object) -> str:
    """Return a non-blank string or raise a field-specific validation error."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _finite_number(name: str, value: object) -> float:
    """Return a finite numeric value or raise a field-specific validation error."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number")
    try:
        number = float(value)
    except OverflowError as error:
        raise ValueError(f"{name} must be a finite number") from error
    if not isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    return number


def _percentage(name: str, value: object) -> float:
    """Return an inclusive percentage as a float."""
    percentage = _finite_number(name, value)
    if not 0 <= percentage <= 100:
        raise ValueError(f"{name} must be a percentage from 0 to 100")
    return percentage


def _json_mapping(name: str, value: object) -> dict[str, Any]:
    """Return an independent JSON-safe mapping with string keys."""
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{name} must be a JSON object with string keys")
    try:
        normalized = json.loads(json.dumps(dict(value)))
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be JSON-serializable") from error
    if not isinstance(normalized, dict):  # pragma: no cover - json contract
        raise ValueError(f"{name} must be a JSON object with string keys")
    return cast(dict[str, Any], normalized)


def _frozen_json_mapping(name: str, value: object) -> Mapping[str, Any]:
    """Return an immutable copy of a validated JSON object."""
    return MappingProxyType(_freeze_json(_json_mapping(name, value)))


def _freeze_json(value: object) -> dict[str, Any]:
    """Recursively protect JSON-object values from post-validation mutation."""
    if not isinstance(value, dict):  # pragma: no cover - _json_mapping contract
        raise TypeError("JSON object must be a dictionary")
    return {key: _freeze_json_value(member) for key, member in value.items()}


def _freeze_json_value(value: object) -> object:
    """Return an immutable representation of one JSON value."""
    if isinstance(value, dict):
        return MappingProxyType(
            {key: _freeze_json_value(member) for key, member in value.items()}
        )
    if isinstance(value, list):
        return tuple(_freeze_json_value(member) for member in value)
    return value


def _json_copy(value: Mapping[str, Any]) -> dict[str, Any]:
    """Return an ordinary JSON-ready dictionary from an immutable mapping."""
    return cast(dict[str, Any], json.loads(json.dumps(_thaw_json(value))))


def _thaw_json(value: object) -> object:
    """Convert immutable JSON containers into standard JSON containers."""
    if isinstance(value, Mapping):
        return {key: _thaw_json(member) for key, member in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(member) for member in value]
    return value


def _serialize_polygon(polygon: Polygon) -> dict[str, object]:
    """Return a JSON-ready GeoJSON mapping for a normalized polygon."""
    serialized = mapping(polygon)
    return {
        "type": serialized["type"],
        "coordinates": _json_ready(serialized["coordinates"]),
    }


def _json_ready(value: object) -> object:
    """Convert tuple coordinates to JSON arrays recursively."""
    if isinstance(value, tuple):
        return [_json_ready(member) for member in value]
    return value


def _acquisition_time(value: object) -> datetime:
    """Return an aware acquisition time from a datetime or ISO-8601 string."""
    if isinstance(value, datetime):
        timestamp = value
    elif isinstance(value, str):
        try:
            timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError(
                "acquisition_time must be an ISO-8601 timestamp"
            ) from error
    else:
        raise ValueError("acquisition_time must be an ISO-8601 timestamp")
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("acquisition_time must include a UTC offset")
    return timestamp


def _paths(value: object) -> tuple[Path, ...]:
    """Return one or more non-empty output paths without accessing the filesystem."""
    if isinstance(value, (str, Path)) or not isinstance(value, Iterable):
        raise ValueError("output_paths must contain at least one path")
    values = tuple(value)
    if not values or any(
        not isinstance(path, (str, Path))
        or not str(path)
        or str(path) == "."
        or "\x00" in str(path)
        for path in values
    ):
        raise ValueError("output_paths must contain at least one non-empty path")
    return tuple(Path(cast(str | Path, path)) for path in values)


def _numeric_tuple(name: str, value: object, length: int) -> tuple[float, ...]:
    """Return a fixed-size tuple of finite numeric values."""
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{name} must contain exactly {length} finite numbers")
    if len(value) != length:
        raise ValueError(f"{name} must contain exactly {length} finite numbers")
    return tuple(_finite_number(name, member) for member in value)


@dataclass(frozen=True)
class SceneReference:
    """Provider-neutral identity and source metadata for one catalog scene."""

    scene_id: str
    provider: str
    provenance: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "scene_id", _nonempty_string("scene_id", self.scene_id)
        )
        object.__setattr__(
            self, "provider", _nonempty_string("provider", self.provider)
        )
        object.__setattr__(
            self, "provenance", _frozen_json_mapping("provenance", self.provenance)
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready scene reference."""
        return {
            "scene_id": self.scene_id,
            "provider": self.provider,
            "provenance": _json_copy(self.provenance),
        }


@dataclass(frozen=True)
class AoiQualityMetrics:
    """AOI coverage and SCL-derived quality evidence for a candidate scene."""

    aoi_coverage: float
    usable_percentage: float
    scl_percentages: Mapping[int, float]
    status: QualityStatus

    def __post_init__(self) -> None:
        if not isinstance(self.status, str) or self.status not in {
            "usable",
            "risky",
            "unusable",
        }:
            raise ValueError("status must be usable, risky, or unusable")
        if not isinstance(self.scl_percentages, Mapping):
            raise ValueError("scl_percentages must be a mapping")
        normalized_scl: dict[int, float] = {}
        for scl_class, percentage in self.scl_percentages.items():
            if (
                isinstance(scl_class, bool)
                or not isinstance(scl_class, Integral)
                or not 0 <= scl_class <= 11
            ):
                raise ValueError("SCL classes must be integers from 0 to 11")
            normalized_scl[int(scl_class)] = _percentage("SCL percentage", percentage)
        object.__setattr__(
            self,
            "aoi_coverage",
            _percentage("aoi_coverage", self.aoi_coverage),
        )
        object.__setattr__(
            self,
            "usable_percentage",
            _percentage("usable_percentage", self.usable_percentage),
        )
        object.__setattr__(self, "scl_percentages", MappingProxyType(normalized_scl))

    def to_dict(self) -> dict[str, object]:
        """Return JSON-ready quality evidence with deterministic SCL ordering."""
        return {
            "aoi_coverage": self.aoi_coverage,
            "usable_percentage": self.usable_percentage,
            "scl_percentages": {
                str(scl_class): percentage
                for scl_class, percentage in sorted(self.scl_percentages.items())
            },
            "status": self.status,
        }


@dataclass(frozen=True)
class CandidateScene:
    """A catalog candidate plus AOI-specific quality and rejection evidence."""

    scene: SceneReference
    acquisition_time: datetime | str
    footprint: object
    catalog_cloud_cover: float
    quality: AoiQualityMetrics
    rejection_reasons: tuple[str, ...]
    provenance: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.scene, SceneReference):
            raise ValueError("scene must be a SceneReference")
        if not isinstance(self.quality, AoiQualityMetrics):
            raise ValueError("quality must be an AoiQualityMetrics")
        if isinstance(self.rejection_reasons, str) or not isinstance(
            self.rejection_reasons, Iterable
        ):
            raise ValueError("rejection_reasons must be strings")
        reasons = tuple(
            _nonempty_string("rejection reason", reason)
            for reason in self.rejection_reasons
        )
        object.__setattr__(
            self,
            "acquisition_time",
            _acquisition_time(self.acquisition_time),
        )
        object.__setattr__(self, "footprint", normalize_aoi(self.footprint))
        object.__setattr__(
            self,
            "catalog_cloud_cover",
            _percentage("catalog_cloud_cover", self.catalog_cloud_cover),
        )
        object.__setattr__(self, "rejection_reasons", reasons)
        object.__setattr__(
            self, "provenance", _frozen_json_mapping("provenance", self.provenance)
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready candidate representation."""
        return {
            "scene": self.scene.to_dict(),
            "acquisition_time": cast(datetime, self.acquisition_time).isoformat(),
            "footprint": _serialize_polygon(cast(Polygon, self.footprint)),
            "catalog_cloud_cover": self.catalog_cloud_cover,
            "quality": self.quality.to_dict(),
            "rejection_reasons": list(self.rejection_reasons),
            "provenance": _json_copy(self.provenance),
        }


@dataclass(frozen=True)
class InspectionResult:
    """Provider-neutral result of inspecting candidate Sentinel-2 scenes."""

    candidates: tuple[CandidateScene, ...]
    provenance: Mapping[str, Any]

    def __post_init__(self) -> None:
        if isinstance(self.candidates, (str, bytes)) or not isinstance(
            self.candidates, Iterable
        ):
            raise ValueError("candidates must be CandidateScene values")
        candidates = tuple(self.candidates)
        if not all(isinstance(candidate, CandidateScene) for candidate in candidates):
            raise ValueError("candidates must be CandidateScene values")
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(
            self, "provenance", _frozen_json_mapping("provenance", self.provenance)
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready inspection result."""
        return {
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "provenance": _json_copy(self.provenance),
        }


@dataclass(frozen=True)
class DownloadResult:
    """Provider-neutral metadata for a completed Sentinel-2 download."""

    scene: SceneReference
    output_paths: tuple[Path | str, ...]
    crs: str
    bounds: tuple[float, float, float, float]
    transform: tuple[float, float, float, float, float, float]
    resolution: float
    bands: tuple[Band | str, ...]
    checksum: str | None
    provenance: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.scene, SceneReference):
            raise ValueError("scene must be a SceneReference")
        bounds = _numeric_tuple("bounds", self.bounds, 4)
        if bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
            raise ValueError("bounds must enclose a positive area")
        if self.checksum is not None:
            _nonempty_string("checksum", self.checksum)
        normalized_bands = validate_bands(self.bands)
        if not normalized_bands:
            raise ValueError("bands must contain at least one band")
        object.__setattr__(self, "output_paths", _paths(self.output_paths))
        object.__setattr__(self, "crs", _nonempty_string("crs", self.crs))
        object.__setattr__(self, "bounds", bounds)
        object.__setattr__(
            self,
            "transform",
            _numeric_tuple("transform", self.transform, 6),
        )
        resolution = _finite_number("resolution", self.resolution)
        if resolution <= 0:
            raise ValueError("resolution must be greater than zero")
        object.__setattr__(self, "resolution", resolution)
        object.__setattr__(self, "bands", normalized_bands)
        object.__setattr__(
            self, "provenance", _frozen_json_mapping("provenance", self.provenance)
        )

    def to_dict(self) -> dict[str, object]:
        """Return JSON-ready metadata for a completed output raster."""
        return {
            "scene": self.scene.to_dict(),
            "output_paths": [str(path) for path in self.output_paths],
            "crs": self.crs,
            "bounds": list(self.bounds),
            "transform": list(self.transform),
            "resolution": self.resolution,
            "bands": [band.value for band in cast(tuple[Band, ...], self.bands)],
            "checksum": self.checksum,
            "provenance": _json_copy(self.provenance),
        }
