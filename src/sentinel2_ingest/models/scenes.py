from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from sentinel2_ingest.models.quality import AoiQualityMetrics


class QualityStatus(StrEnum):
    USABLE = "usable"
    RISKY = "risky"
    REJECTED = "rejected"


class CandidateScene(BaseModel):
    """Provider-independent candidate scene returned by inspection."""

    model_config = ConfigDict(frozen=True)

    scene_id: str = Field(min_length=1)
    datetime: datetime

    collection: str = Field(min_length=1)
    source: str = Field(min_length=1)

    scene_cloud_coverage: float | None = Field(default=None, ge=0, le=100)

    quality: AoiQualityMetrics | None = None
    quality_status: QualityStatus | None = None
    quality_reasons: list[str] = Field(default_factory=list)

    thumbnail_path: Path | None = None

    source_metadata: dict[str, Any] = Field(default_factory=dict)