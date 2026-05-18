
from sentinel2_ingest.client import Sentinel2IngestClient
from sentinel2_ingest.models import (
    AoiQualityMetrics,
    CandidateScene,
    DownloadRequest,
    DownloadResult,
    InspectionRequest,
    InspectionResult,
    QualityStatus,
)
from sentinel2_ingest.providers import FakeSceneProvider


def hello() -> str:
    return "Hello from sentinel2-ingest!"


__all__ = [
    "Sentinel2IngestClient",
    "AoiQualityMetrics",
    "CandidateScene",
    "FakeSceneProvider",
    "DownloadRequest",
    "DownloadResult",
    "InspectionRequest",
    "InspectionResult",
    "QualityStatus",
    "hello",
]