from importlib import metadata

from sentinel2_ingest import _version


def test_resolver_returns_unknown_when_distribution_metadata_is_missing(
    monkeypatch,
) -> None:
    def raise_package_not_found(distribution_name: str) -> str:
        raise metadata.PackageNotFoundError(distribution_name)

    monkeypatch.setattr(_version.metadata, "version", raise_package_not_found)

    assert _version.resolve_version() == "0.0.0+unknown"
