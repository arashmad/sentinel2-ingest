class Sentinel2IngestError(Exception):
    """Base exception for sentinel2-ingest errors."""


class ProviderError(Sentinel2IngestError):
    """Base exception for provider-related failure."""


class ProviderConfigurationError(ProviderError, ValueError):
    """Raised when provider configuration is missing or invalid."""


class ProviderAuthenticationError(ProviderError):
    """Raised when a provider rejects the supplied credentials."""


class InvalidAoiError(Sentinel2IngestError, ValueError):
    """Raised when an AOI is not supported or is geometrically invalid."""
