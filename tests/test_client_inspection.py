from __future__ import annotations

from sentinel2_ingest import FakeSceneProvider, Sentinel2IngestClient
from sentinel2_ingest.models import QualityStatus

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
