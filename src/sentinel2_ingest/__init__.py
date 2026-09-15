"""Inspect and download Sentinel-2 imagery."""

from ._version import resolve_version as _resolve_version
from .bands import DEFAULT_BANDS, Band, validate_bands
from .errors import (
    InvalidAOIError,
    InvalidBandError,
    InvalidDateError,
    InvalidQualityPolicyError,
    InvalidResolutionError,
    NoCandidatesFoundError,
    OutputError,
    ProviderRequestError,
    Sentinel2IngestError,
    UnacceptableCandidateError,
)
from .quality import (
    UNUSABLE_SCL_CLASSES,
    USABLE_SCL_CLASSES,
    QualityPolicy,
)
from .requests import (
    DEFAULT_CANDIDATE_LIMIT,
    DEFAULT_MAX_CLOUD_COVER,
    SUPPORTED_OUTPUT_RESOLUTIONS,
    DownloadBySceneRequest,
    DownloadBySearchRequest,
    InspectionRequest,
)
from .results import (
    AoiQualityMetrics,
    CandidateScene,
    DownloadResult,
    InspectionResult,
    SceneReference,
)

__version__ = _resolve_version()

__all__ = [
    "Band",
    "AoiQualityMetrics",
    "CandidateScene",
    "DEFAULT_BANDS",
    "DEFAULT_CANDIDATE_LIMIT",
    "DEFAULT_MAX_CLOUD_COVER",
    "DownloadBySceneRequest",
    "DownloadBySearchRequest",
    "DownloadResult",
    "InspectionRequest",
    "InspectionResult",
    "InvalidAOIError",
    "InvalidBandError",
    "InvalidDateError",
    "InvalidQualityPolicyError",
    "InvalidResolutionError",
    "NoCandidatesFoundError",
    "OutputError",
    "ProviderRequestError",
    "QualityPolicy",
    "SceneReference",
    "Sentinel2IngestError",
    "SUPPORTED_OUTPUT_RESOLUTIONS",
    "UNUSABLE_SCL_CLASSES",
    "USABLE_SCL_CLASSES",
    "UnacceptableCandidateError",
    "__version__",
    "validate_bands",
]

del _resolve_version
