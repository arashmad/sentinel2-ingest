from __future__ import annotations

from datetime import UTC, datetime

from sentinel2_ingest.models import (
    AoiQualityMetrics,
    CandidateScene,
    InspectionRequest,
    QualityStatus,
)


class FakeSceneProvider:
    """Fake provider used for tests and early development.

    This provider does not call external services.
    """

    def inspect(self, request: InspectionRequest) -> list[CandidateScene]:
        return [
            CandidateScene(
                scene_id="fake-scene-2025-06-12",
                datetime=datetime(2025, 6, 12, 10, 21, tzinfo=UTC),
                collection="sentinel-2-l2a",
                source="fake",
                scene_cloud_coverage=12.5,
                quality=AoiQualityMetrics(
                    total_pixel_count=100,
                    valid_data_pixel_count=90,
                    usable_pixel_count=80,
                    cloud_pixel_count=5,
                    shadow_pixel_count=3,
                    snow_pixel_count=0,
                    no_data_pixel_count=10,
                    defective_pixel_count=0,
                    dark_area_pixel_count=1,
                    unclassified_pixel_count=1,
                ),
                quality_status=QualityStatus.USABLE,
                quality_reasons=[],
                source_metadata={
                    "request_date_from": request.date_from.isoformat(),
                    "request_date_to": request.date_to.isoformat(),
                },
            ),
            CandidateScene(
                scene_id="fake-scene-2025-06-17",
                datetime=datetime(2025, 6, 17, 10, 21, tzinfo=UTC),
                collection="sentinel-2-l2a",
                source="fake",
                scene_cloud_coverage=55.0,
                quality=AoiQualityMetrics(
                    total_pixel_count=100,
                    valid_data_pixel_count=95,
                    usable_pixel_count=58,
                    cloud_pixel_count=30,
                    shadow_pixel_count=5,
                    snow_pixel_count=0,
                    no_data_pixel_count=5,
                    defective_pixel_count=0,
                    dark_area_pixel_count=1,
                    unclassified_pixel_count=1,
                ),
                quality_status=QualityStatus.REJECTED,
                quality_reasons=["AOI usable pixel ratio is below the requested threshold."],
            ),
        ]