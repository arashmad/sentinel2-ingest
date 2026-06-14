from __future__ import annotations

from datetime import UTC, datetime

from sentinel2_ingest import FakeSceneProvider, Sentinel2IngestClient
from sentinel2_ingest.models import (
    AoiQualityMetrics,
    CandidateScene,
    InspectionRequest,
    QualityStatus,
)

VALID_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [13.0, 52.0],
            [13.1, 52.0],
            [13.1, 52.1],
            [13.0, 52.1],
            [13.0, 52.0],
        ]
    ],
}


def test_client_inspect_returns_inspection_result() -> None:
    client = Sentinel2IngestClient(provider=FakeSceneProvider())

    result = client.inspect(
        aoi=VALID_POLYGON,
        date_range=("2025-06-01", "2025-06-30"),
    )

    assert result.inspection_id
    assert len(result.candidates) == 2
    assert result.candidates[0].source == "fake"


def test_client_inspect_result_is_serializable() -> None:
    client = Sentinel2IngestClient(provider=FakeSceneProvider())

    result = client.inspect(
        aoi=VALID_POLYGON,
        date_range=("2025-06-01", "2025-06-30"),
    )

    dumped = result.model_dump(mode="json")

    assert dumped["inspection_id"]
    assert dumped["candidates"][0]["scene_id"] == "fake-scene-2025-06-12"
    assert dumped["candidates"][0]["quality"]["usable_pixel_ratio"] > 0


def test_client_inspect_accepts_date_objects() -> None:
    from datetime import date

    client = Sentinel2IngestClient(provider=FakeSceneProvider())

    result = client.inspect(
        aoi=VALID_POLYGON,
        date_range=(date(2025, 6, 1), date(2025, 6, 30)),
    )

    assert len(result.candidates) == 2


def test_fake_provider_uses_quality_classifier_defaults() -> None:
    client = Sentinel2IngestClient(provider=FakeSceneProvider())

    result = client.inspect(
        aoi=VALID_POLYGON,
        date_range=("2025-06-01", "2025-06-30"),
    )

    assert result.candidates[0].quality_status == QualityStatus.USABLE
    assert result.candidates[0].quality_reasons == []

    assert result.candidates[1].quality_status == QualityStatus.REJECTED
    assert result.candidates[1].quality_reasons


def test_fake_provider_quality_status_changes_when_thresholds_change() -> None:
    client = Sentinel2IngestClient(provider=FakeSceneProvider())

    result = client.inspect(
        aoi=VALID_POLYGON,
        date_range=("2025-06-01", "2025-06-30"),
        min_usable_pixel_ratio=0.90,
    )

    assert result.candidates[0].quality_status == QualityStatus.RISKY
    assert any("usable pixel ratio" in reason for reason in result.candidates[0].quality_reasons)


class UnsortedSceneProvider:
    def inspect(self, request: InspectionRequest) -> list[CandidateScene]:
        return [
            CandidateScene(
                scene_id="rejected-scene",
                datetime=datetime(2025, 6, 2, 10, 0, tzinfo=UTC),
                collection="sentinel-2-l2a",
                source="test",
                quality=AoiQualityMetrics(
                    total_pixel_count=100,
                    valid_data_pixel_count=100,
                    usable_pixel_count=40,
                    cloud_pixel_count=50,
                    shadow_pixel_count=5,
                    snow_pixel_count=0,
                    no_data_pixel_count=0,
                    defective_pixel_count=0,
                    dark_area_pixel_count=0,
                    unclassified_pixel_count=0,
                ),
                quality_status=QualityStatus.REJECTED,
            ),
            CandidateScene(
                scene_id="usable-scene",
                datetime=datetime(2025, 6, 1, 10, 0, tzinfo=UTC),
                collection="sentinel-2-l2a",
                source="test",
                quality=AoiQualityMetrics(
                    total_pixel_count=100,
                    valid_data_pixel_count=100,
                    usable_pixel_count=85,
                    cloud_pixel_count=5,
                    shadow_pixel_count=2,
                    snow_pixel_count=0,
                    no_data_pixel_count=0,
                    defective_pixel_count=0,
                    dark_area_pixel_count=0,
                    unclassified_pixel_count=0,
                ),
                quality_status=QualityStatus.USABLE,
            ),
        ]


def test_client_inspect_returns_ranked_candidates() -> None:
    client = Sentinel2IngestClient(provider=UnsortedSceneProvider())

    result = client.inspect(
        aoi=VALID_POLYGON,
        date_range=("2025-06-01", "2025-06-30"),
    )

    assert [candidate.scene_id for candidate in result.candidates] == [
        "usable-scene",
        "rejected-scene",
    ]
