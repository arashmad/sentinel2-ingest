class Sentinel2IngestError(Exception):
    """Base exception for sentinel2-ingest errors."""


class InvalidAoiError(Sentinel2IngestError, ValueError):
    """Raised when an AOI is not supported or is geometrically invalid."""