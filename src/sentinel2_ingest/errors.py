"""Public exceptions raised by :mod:`sentinel2_ingest`."""


class Sentinel2IngestError(Exception):
    """Base exception for package-specific failures."""


class InvalidAOIError(Sentinel2IngestError):
    """Raised when an area of interest is invalid."""

    def __init__(self, details: str) -> None:
        super().__init__(f"Invalid area of interest: {details}.")


class InvalidDateError(Sentinel2IngestError):
    """Raised when requested dates are invalid."""

    def __init__(self, details: str) -> None:
        super().__init__(f"Invalid dates: {details}.")


class InvalidBandError(Sentinel2IngestError):
    """Raised when requested bands are invalid."""

    def __init__(self, details: str) -> None:
        super().__init__(f"Invalid bands: {details}.")


class InvalidResolutionError(Sentinel2IngestError):
    """Raised when a requested resolution is invalid."""

    def __init__(self, details: str) -> None:
        super().__init__(f"Invalid resolution: {details}.")


class ProviderRequestError(Sentinel2IngestError):
    """Raised when a provider request fails."""

    def __init__(self) -> None:
        super().__init__("Unable to retrieve Sentinel-2 candidates from the provider.")


class NoCandidatesFoundError(Sentinel2IngestError):
    """Raised when a search returns no Sentinel-2 candidates."""

    def __init__(self) -> None:
        super().__init__("No Sentinel-2 candidates were found.")


class UnacceptableCandidateError(Sentinel2IngestError):
    """Raised when candidates do not meet the requested constraints."""

    def __init__(self, details: str) -> None:
        super().__init__(f"No acceptable Sentinel-2 candidates: {details}.")


class OutputError(Sentinel2IngestError):
    """Raised when requested output cannot be produced."""

    def __init__(self) -> None:
        super().__init__("Unable to produce the requested output.")
