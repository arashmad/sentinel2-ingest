from sentinel2_ingest.models import (
    AoiQualityMetrics,
    CandidateScene,
    DownloadRequest,
    DownloadResult,
    InspectionRequest,
    InspectionResult,
    QualityStatus,
)


def hello() -> str:
    return "Hello from sentinel2-ingest!"


__all__ = [
    "AoiQualityMetrics",
    "CandidateScene",
    "DownloadRequest",
    "DownloadResult",
    "InspectionRequest",
    "InspectionResult",
    "QualityStatus",
    "hello",
]