"""Inspect and download Sentinel-2 imagery."""

from ._version import resolve_version as _resolve_version
from .errors import (
    InvalidAOIError,
    InvalidBandError,
    InvalidDateError,
    InvalidResolutionError,
    NoCandidatesFoundError,
    OutputError,
    ProviderRequestError,
    Sentinel2IngestError,
    UnacceptableCandidateError,
)

__version__ = _resolve_version()

__all__ = [
    "InvalidAOIError",
    "InvalidBandError",
    "InvalidDateError",
    "InvalidResolutionError",
    "NoCandidatesFoundError",
    "OutputError",
    "ProviderRequestError",
    "Sentinel2IngestError",
    "UnacceptableCandidateError",
    "__version__",
]

del _resolve_version
