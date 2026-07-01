from sentinel2_ingest.exceptions import (
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderError,
    Sentinel2IngestError,
)


def test_provider_error_inherits_from_package_error() -> None:
    assert issubclass(ProviderError, Sentinel2IngestError)


def test_provider_configuration_error_inheritance() -> None:
    assert issubclass(ProviderConfigurationError, ProviderError)
    assert issubclass(ProviderConfigurationError, ValueError)


def test_provider_authentication_error_inheritance() -> None:
    assert issubclass(ProviderAuthenticationError, ProviderError)
    assert not issubclass(ProviderAuthenticationError, ValueError)
