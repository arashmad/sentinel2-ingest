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

__version__ = _resolve_version()

__all__ = [
    "Band",
    "DEFAULT_BANDS",
    "InvalidAOIError",
    "InvalidBandError",
    "InvalidDateError",
    "InvalidQualityPolicyError",
    "InvalidResolutionError",
    "NoCandidatesFoundError",
    "OutputError",
    "ProviderRequestError",
    "QualityPolicy",
    "Sentinel2IngestError",
    "UNUSABLE_SCL_CLASSES",
    "USABLE_SCL_CLASSES",
    "UnacceptableCandidateError",
    "__version__",
    "validate_bands",
]

del _resolve_version
