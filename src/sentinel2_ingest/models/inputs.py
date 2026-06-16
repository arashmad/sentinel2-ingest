from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sentinel2_ingest.aoi import validate_single_polygon_aoi
from sentinel2_ingest.bands import SUPPORTED_BANDS


class InspectionRequest(BaseModel):
    """Request for inspecting candidate scenes for an AOI and date range."""

    model_config = ConfigDict(frozen=True)

    aoi: dict[str, Any]
    date_from: date
    date_to: date

    max_scene_cloud_coverage: float = Field(default=60.0, ge=0, le=100)

    min_usable_pixel_ratio: float = Field(default=0.80, ge=0, le=1)
    max_cloud_pixel_ratio: float = Field(default=0.10, ge=0, le=1)
    max_shadow_pixel_ratio: float = Field(default=0.10, ge=0, le=1)
    max_no_data_ratio: float = Field(default=0.05, ge=0, le=1)

    thumbnail: bool = True
    output_dir: Path | None = None

    @field_validator("aoi")
    @classmethod
    def validate_aoi(cls, value: dict[str, Any]) -> dict[str, Any]:
        return validate_single_polygon_aoi(value)

    @model_validator(mode="after")
    def validate_date_range(self) -> InspectionRequest:
        if self.date_from > self.date_to:
            raise ValueError("date_from must be before or equal to date_to")
        return self


class DownloadRequest(BaseModel):
    """Request for downloading raw bands for one selected scene."""

    model_config = ConfigDict(frozen=True)

    scene_id: str = Field(min_length=1)
    aoi: dict[str, Any]
    bands: tuple[str, ...] = Field(min_length=1)
    resolution: int = Field(default=10, gt=0)
    output_dir: Path

    @field_validator("aoi")
    @classmethod
    def validate_aoi(cls, value: dict[str, Any]) -> dict[str, Any]:
        return validate_single_polygon_aoi(value)

    @field_validator("bands", mode="before")
    @classmethod
    def normalize_bands(cls, value: Any) -> tuple[str, ...]:
        return tuple(str(band).upper() for band in value)

    @model_validator(mode="after")
    def validate_bands(self) -> DownloadRequest:
        if len(set(self.bands)) != len(self.bands):
            raise ValueError("bands must not contain duplicates")

        unsupported_bands = sorted(set(self.bands) - SUPPORTED_BANDS)

        if unsupported_bands:
            unsupported = ", ".join(unsupported_bands)
            raise ValueError(f"unsupported Sentinel-2 L2A bands: {unsupported}")

        return self
