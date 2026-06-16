from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from sentinel2_ingest.models import (
    AoiQualityMetrics,
    CandidateScene,
    DownloadRequest,
    DownloadResult,
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

MULTIPOLYGON_AOI = {
    "type": "MultiPolygon",
    "coordinates": [
        [
            [
                [13.0, 52.0],
                [13.1, 52.0],
                [13.1, 52.1],
                [13.0, 52.1],
                [13.0, 52.0],
            ]
        ]
    ],
}


def test_inspection_request_accepts_valid_date_range() -> None:
    request = InspectionRequest(
        aoi=VALID_POLYGON,
        date_from=date(2025, 6, 1),
        date_to=date(2025, 6, 30),
    )

    assert request.date_from == date(2025, 6, 1)
    assert request.date_to == date(2025, 6, 30)


def test_inspection_request_rejects_invalid_date_range() -> None:
    with pytest.raises(ValidationError, match="date_from must be before or equal to date_to"):
        InspectionRequest(
            aoi=VALID_POLYGON,
            date_from=date(2025, 6, 30),
            date_to=date(2025, 6, 1),
        )


def test_inspection_request_rejects_invalid_thresholds() -> None:
    with pytest.raises(ValidationError):
        InspectionRequest(
            aoi=VALID_POLYGON,
            date_from=date(2025, 6, 1),
            date_to=date(2025, 6, 30),
            min_usable_pixel_ratio=1.5,
        )


def test_inspection_request_rejects_multipolygon_aoi() -> None:
    with pytest.raises(ValidationError, match="Polygon"):
        InspectionRequest(
            aoi=MULTIPOLYGON_AOI,
            date_from=date(2025, 6, 1),
            date_to=date(2025, 6, 30),
        )


def test_aoi_quality_metrics_computes_ratios() -> None:
    metrics = AoiQualityMetrics(
        total_pixel_count=100,
        valid_data_pixel_count=90,
        usable_pixel_count=72,
        cloud_pixel_count=9,
        shadow_pixel_count=3,
        snow_pixel_count=0,
        no_data_pixel_count=10,
        defective_pixel_count=1,
        dark_area_pixel_count=2,
        unclassified_pixel_count=3,
    )

    assert metrics.usable_pixel_ratio == 0.8
    assert metrics.cloud_pixel_ratio == 0.1
    assert metrics.no_data_ratio == 0.1


def test_candidate_scene_is_provider_independent() -> None:
    scene = CandidateScene(
        scene_id="scene-1",
        datetime=datetime.fromisoformat("2025-06-12T10:21:00+00:00"),
        collection="sentinel-2-l2a",
        source="test-source",
        scene_cloud_coverage=12.5,
        quality_status=QualityStatus.USABLE,
    )

    assert scene.scene_id == "scene-1"
    assert scene.source == "test-source"
    assert scene.quality_status == QualityStatus.USABLE


def test_download_request_normalizes_lowercase_bands() -> None:
    request = DownloadRequest(
        scene_id="scene-1",
        aoi=VALID_POLYGON,
        bands=["b02", "b03", "b04", "b08"],
        resolution=10,
        output_dir=Path("data/downloads"),
    )

    assert request.bands == ("B02", "B03", "B04", "B08")


def test_download_request_normalizes_mixed_case_bands() -> None:
    request = DownloadRequest(
        scene_id="scene-1",
        aoi=VALID_POLYGON,
        bands=["b02", "B03", "b04", "B08"],
        resolution=10,
        output_dir=Path("data/downloads"),
    )

    assert request.bands == ("B02", "B03", "B04", "B08")


def test_download_request_normalizes_b8a() -> None:
    request = DownloadRequest(
        scene_id="scene-1",
        aoi=VALID_POLYGON,
        bands=["b8a"],
        resolution=10,
        output_dir=Path("data/downloads"),
    )

    assert request.bands == ("B8A",)


def test_download_request_accepts_supported_bands() -> None:
    request = DownloadRequest(
        scene_id="scene-1",
        aoi=VALID_POLYGON,
        bands=["B02", "B03", "B04", "B08"],
        resolution=10,
        output_dir=Path("data/downloads"),
    )

    assert request.bands == ("B02", "B03", "B04", "B08")


def test_download_request_rejects_duplicate_bands_after_normalization() -> None:
    with pytest.raises(ValidationError, match="bands must not contain duplicates"):
        DownloadRequest(
            scene_id="scene-1",
            aoi=VALID_POLYGON,
            bands=["B02", "b02"],
            resolution=10,
            output_dir=Path("data/downloads"),
        )


def test_download_request_rejects_unsupported_bands() -> None:
    with pytest.raises(
        ValidationError,
        match="unsupported Sentinel-2 L2A bands: B13",
    ):
        DownloadRequest(
            scene_id="scene-1",
            aoi=VALID_POLYGON,
            bands=["B02", "B13"],
            resolution=10,
            output_dir=Path("data/downloads"),
        )


def test_download_request_rejects_unsupported_bands_after_normalization() -> None:
    with pytest.raises(
        ValidationError,
        match="unsupported Sentinel-2 L2A bands: B13",
    ):
        DownloadRequest(
            scene_id="scene-1",
            aoi=VALID_POLYGON,
            bands=["b13"],
            resolution=10,
            output_dir=Path("data/downloads"),
        )


def test_download_request_rejects_b10_for_l2a() -> None:
    with pytest.raises(
        ValidationError,
        match="unsupported Sentinel-2 L2A bands: B10",
    ):
        DownloadRequest(
            scene_id="scene-1",
            aoi=VALID_POLYGON,
            bands=["B02", "B10"],
            resolution=10,
            output_dir=Path("data/downloads"),
        )


def test_download_result_accepts_required_fields() -> None:
    result = DownloadResult(
        scene_id="scene-1",
        collection="sentinel-2-l2a",
        source="test-source",
        bands=["B02", "B03", "B04"],
        file_path=Path("data/downloads/scene-1.tif"),
        resolution=10,
    )

    assert result.scene_id == "scene-1"
    assert result.bands == ["B02", "B03", "B04"]
    assert result.resolution == 10
