from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

from sentinel2_ingest.models import InspectionRequest, InspectionResult
from sentinel2_ingest.providers import SceneProvider


class Sentinel2IngestClient:
    """Public client for inspecting and downloading Sentinel-2 scenes."""

    def __init__(self, provider: SceneProvider) -> None:
        self._provider = provider

    def inspect(
        self,
        *,
        aoi: dict[str, Any],
        date_range: tuple[str | date, str | date],
        max_scene_cloud_coverage: float = 60.0,
        min_usable_pixel_ratio: float = 0.80,
        max_cloud_pixel_ratio: float = 0.10,
        max_shadow_pixel_ratio: float = 0.10,
        max_no_data_ratio: float = 0.05,
        thumbnail: bool = True,
    ) -> InspectionResult:
        """Inspect candidate scenes for a single Polygon AOI and date range."""
        date_from, date_to = date_range

        request = InspectionRequest(
            aoi=aoi,
            date_from=_parse_date(date_from),
            date_to=_parse_date(date_to),
            max_scene_cloud_coverage=max_scene_cloud_coverage,
            min_usable_pixel_ratio=min_usable_pixel_ratio,
            max_cloud_pixel_ratio=max_cloud_pixel_ratio,
            max_shadow_pixel_ratio=max_shadow_pixel_ratio,
            max_no_data_ratio=max_no_data_ratio,
            thumbnail=thumbnail,
        )

        candidates = self._provider.inspect(request)

        return InspectionResult(
            inspection_id=str(uuid4()),
            candidates=candidates,
            created_at=datetime.now(UTC),
        )


def _parse_date(value: str | date) -> date:
    if isinstance(value, date):
        return value

    return date.fromisoformat(value)