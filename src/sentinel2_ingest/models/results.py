from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from sentinel2_ingest.models.scenes import CandidateScene


class InspectionResult(BaseModel):
    """Result of an inspection request."""

    model_config = ConfigDict(frozen=True)

    inspection_id: str = Field(min_length=1)
    candidates: list[CandidateScene]
    created_at: datetime
    metadata_path: Path | None = None


class DownloadResult(BaseModel):
    """Result of downloading selected raw bands as a raster file."""

    model_config = ConfigDict(frozen=True)

    scene_id: str = Field(min_length=1)
    collection: str = Field(min_length=1)
    source: str = Field(min_length=1)

    bands: list[str] = Field(min_length=1)
    file_path: Path
    metadata_path: Path | None = None

    crs: str | None = None
    resolution: int = Field(gt=0)

    width: int | None = Field(default=None, ge=0)
    height: int | None = Field(default=None, ge=0)
    bounds: tuple[float, float, float, float] | None = None