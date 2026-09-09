"""Resolve the installed distribution version."""

from importlib import metadata


def resolve_version() -> str:
    """Return the installed sentinel2-ingest distribution version."""
    try:
        return metadata.version("sentinel2-ingest")
    except metadata.PackageNotFoundError:
        return "0.0.0+unknown"
