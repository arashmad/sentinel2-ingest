"""Inspect and download Sentinel-2 imagery."""

from ._version import resolve_version as _resolve_version

__version__ = _resolve_version()

__all__ = ["__version__"]

del _resolve_version
