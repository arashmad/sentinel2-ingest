from __future__ import annotations

from datetime import UTC, datetime

from sentinel2_ingest.inspection import classify_quality
from sentinel2_ingest.models import (
    AoiQualityMetrics,
    CandidateScene,
    InspectionRequest,
)


class FakeSceneProvider:
    """Fake provider used for tests and early development.

    This provider does not call external services.
    """

    def inspect(self, request: InspectionRequest) -> list[CandidateScene]:
        first_scene_quality = AoiQualityMetrics(
            total_pixel_count=100,
            valid_data_pixel_count=96,
            usable_pixel_count=84,
            cloud_pixel_count=5,
            shadow_pixel_count=3,
            snow_pixel_count=0,
            no_data_pixel_count=4,
            defective_pixel_count=0,
            dark_area_pixel_count=1,
            unclassified_pixel_count=1,
        )

        second_scene_quality = AoiQualityMetrics(
            total_pixel_count=100,
            valid_data_pixel_count=95,
            usable_pixel_count=50,
            cloud_pixel_count=35,
            shadow_pixel_count=5,
            snow_pixel_count=0,
            no_data_pixel_count=5,
            defective_pixel_count=0,
            dark_area_pixel_count=1,
            unclassified_pixel_count=1,
        )

        first_scene_assessment = _classify_fake_scene_quality(
            metrics=first_scene_quality,
            request=request,
        )
        second_scene_assessment = _classify_fake_scene_quality(
            metrics=second_scene_quality,
            request=request,
        )

        return [
            CandidateScene(
                scene_id="fake-scene-2025-06-12",
                datetime=datetime(2025, 6, 12, 10, 21, tzinfo=UTC),
                collection="sentinel-2-l2a",
                source="fake",
                scene_cloud_coverage=12.5,
                quality=first_scene_quality,
                quality_status=first_scene_assessment.status,
                quality_reasons=first_scene_assessment.reasons,
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
                quality=second_scene_quality,
                quality_status=second_scene_assessment.status,
                quality_reasons=second_scene_assessment.reasons,
                source_metadata={
                    "request_date_from": request.date_from.isoformat(),
                    "request_date_to": request.date_to.isoformat(),
                },
            ),
        ]


def _classify_fake_scene_quality(
    *,
    metrics: AoiQualityMetrics,
    request: InspectionRequest,
):
    return classify_quality(
        metrics=metrics,
        min_usable_pixel_ratio=request.min_usable_pixel_ratio,
        max_cloud_pixel_ratio=request.max_cloud_pixel_ratio,
        max_shadow_pixel_ratio=request.max_shadow_pixel_ratio,
        max_no_data_ratio=request.max_no_data_ratio,
    )
