"""Public inspection and download request-model tests."""

from datetime import date
from pathlib import Path

import pytest
from shapely.geometry import Polygon

import sentinel2_ingest

AOI = {
    "type": "Polygon",
    "coordinates": [[(10, 45), (11, 45), (11, 46), (10, 46), (10, 45)]],
}


def test_inspection_request_normalizes_inputs_and_serializes_defaults() -> None:
    """A changed default or serialization must not alter catalog search behavior."""
    request = sentinel2_ingest.InspectionRequest(
        aoi=AOI,
        start_date="2024-01-01",
        end_date=date(2024, 1, 31),
    )

    assert isinstance(request.aoi, Polygon)
    assert request.start_date == date(2024, 1, 1)
    assert request.end_date == date(2024, 1, 31)
    assert request.to_dict() == {
        "aoi": {
            "type": "Polygon",
            "coordinates": [
                [
                    [10.0, 45.0],
                    [11.0, 45.0],
                    [11.0, 46.0],
                    [10.0, 46.0],
                    [10.0, 45.0],
                ]
            ],
        },
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "max_cloud_cover": 80.0,
        "candidate_limit": 20,
        "quality_policy": {
            "usable_threshold": 80.0,
            "risky_threshold": 50.0,
            "usable_scl_classes": [2, 4, 5, 6, 7],
            "unusable_scl_classes": [0, 1, 3, 8, 9, 10, 11],
        },
    }


@pytest.mark.parametrize(
    ("start_date", "end_date"),
    [
        ("2024-01-31", "2024-01-01"),
        ("2024-02-30", "2024-03-01"),
        ("2024/01/01", "2024-01-31"),
        (123, "2024-01-31"),
    ],
)
def test_inspection_request_rejects_invalid_date_ranges(
    start_date: object,
    end_date: object,
) -> None:
    """Invalid dates must not reach a provider catalog request."""
    with pytest.raises(sentinel2_ingest.InvalidDateError):
        sentinel2_ingest.InspectionRequest(AOI, start_date, end_date)


@pytest.mark.parametrize("max_cloud_cover", (0, 100, 12.5))
def test_inspection_request_accepts_inclusive_cloud_cover_bounds(
    max_cloud_cover: float,
) -> None:
    """The catalog must allow callers to include the legal endpoint filters."""
    request = sentinel2_ingest.InspectionRequest(
        AOI,
        "2024-01-01",
        "2024-01-31",
        max_cloud_cover=max_cloud_cover,
    )

    assert request.max_cloud_cover == float(max_cloud_cover)


@pytest.mark.parametrize("max_cloud_cover", (-0.1, 100.1, float("inf"), True))
def test_inspection_request_rejects_invalid_cloud_cover(
    max_cloud_cover: object,
) -> None:
    """Non-percent or out-of-range cloud filters must not reach a catalog."""
    with pytest.raises(ValueError, match="cloud"):
        sentinel2_ingest.InspectionRequest(
            AOI,
            "2024-01-01",
            "2024-01-31",
            max_cloud_cover=max_cloud_cover,
        )


@pytest.mark.parametrize("candidate_limit", (1, 20))
def test_inspection_request_accepts_positive_candidate_limits(
    candidate_limit: int,
) -> None:
    """A positive catalog cap must retain its caller-provided value."""
    request = sentinel2_ingest.InspectionRequest(
        AOI,
        "2024-01-01",
        "2024-01-31",
        candidate_limit=candidate_limit,
    )

    assert request.candidate_limit == candidate_limit


@pytest.mark.parametrize("candidate_limit", (0, -1, 1.5, True))
def test_inspection_request_rejects_non_positive_or_non_integral_limits(
    candidate_limit: object,
) -> None:
    """A malformed cap must not create an ambiguous provider request."""
    with pytest.raises(ValueError, match="candidate"):
        sentinel2_ingest.InspectionRequest(
            AOI,
            "2024-01-01",
            "2024-01-31",
            candidate_limit=candidate_limit,
        )


def test_download_by_search_request_normalizes_output_bands_and_resolution() -> None:
    """Download settings must serialize in provider-independent normalized form."""
    inspection = sentinel2_ingest.InspectionRequest(
        AOI,
        "2024-01-01",
        "2024-01-31",
    )
    request = sentinel2_ingest.DownloadBySearchRequest(
        inspection_request=inspection,
        output_path="output.tif",
        bands=("b08", "B04"),
        resolution=20,
        allow_risky=True,
        overwrite=True,
    )

    assert request.output_path == Path("output.tif")
    assert request.to_dict() == {
        "inspection_request": inspection.to_dict(),
        "output_path": "output.tif",
        "bands": ["B08", "B04"],
        "resolution": 20,
        "allow_risky": True,
        "overwrite": True,
    }


@pytest.mark.parametrize("resolution", (0, 12, 30, 61, True))
def test_download_by_search_request_rejects_unsupported_resolution(
    resolution: object,
) -> None:
    """Only Sentinel-2 output resolutions may be requested."""
    inspection = sentinel2_ingest.InspectionRequest(
        AOI,
        "2024-01-01",
        "2024-01-31",
    )

    with pytest.raises(sentinel2_ingest.InvalidResolutionError):
        sentinel2_ingest.DownloadBySearchRequest(
            inspection_request=inspection,
            output_path="output.tif",
            resolution=resolution,
        )


def test_download_by_scene_request_serializes_provider_neutral_scene_id() -> None:
    """Explicit downloads must preserve an opaque selected-scene reference."""
    request = sentinel2_ingest.DownloadBySceneRequest(
        scene_id="S2A_MSIL2A_20240101T000000_N0509_R000_T32TMT_20240101T000000",
        aoi=AOI,
        output_path=Path("scene.tif"),
        bands=("b04", "B03"),
        resolution=60,
    )

    assert request.to_dict() == {
        "scene_id": "S2A_MSIL2A_20240101T000000_N0509_R000_T32TMT_20240101T000000",
        "aoi": {
            "type": "Polygon",
            "coordinates": [
                [
                    [10.0, 45.0],
                    [11.0, 45.0],
                    [11.0, 46.0],
                    [10.0, 46.0],
                    [10.0, 45.0],
                ]
            ],
        },
        "output_path": "scene.tif",
        "bands": ["B04", "B03"],
        "resolution": 60,
        "overwrite": False,
    }


@pytest.mark.parametrize("scene_id", ("", "   ", 123))
def test_download_by_scene_request_rejects_missing_scene_reference(
    scene_id: object,
) -> None:
    """An explicit download without a scene reference cannot be fulfilled."""
    with pytest.raises(ValueError, match="scene"):
        sentinel2_ingest.DownloadBySceneRequest(
            scene_id=scene_id,
            aoi=AOI,
            output_path="scene.tif",
        )


@pytest.mark.parametrize("output_path", ("", Path(""), 123))
def test_download_requests_reject_invalid_output_paths(output_path: object) -> None:
    """An absent or non-path destination must not defer failure to raster writing."""
    inspection = sentinel2_ingest.InspectionRequest(
        AOI,
        "2024-01-01",
        "2024-01-31",
    )

    with pytest.raises(sentinel2_ingest.OutputError):
        sentinel2_ingest.DownloadBySearchRequest(
            inspection_request=inspection,
            output_path=output_path,
        )
