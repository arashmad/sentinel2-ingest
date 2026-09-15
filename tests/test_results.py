"""Public result-model tests."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pytest

import sentinel2_ingest

FOOTPRINT = {
    "type": "Polygon",
    "coordinates": [[(10, 45), (11, 45), (11, 46), (10, 46), (10, 45)]],
}


def test_result_models_normalize_a_complete_workflow_and_round_trip_json() -> None:
    """A provider result must retain all portable workflow details in JSON."""
    scene = sentinel2_ingest.SceneReference(
        scene_id="S2A_MSIL2A_20240101T000000_N0509_R000_T32TMT",
        provider="copernicus",
        provenance={"catalog_id": "item-123", "url": "https://example.test/item-123"},
    )
    quality = sentinel2_ingest.AoiQualityMetrics(
        aoi_coverage=99,
        usable_percentage=82.5,
        scl_percentages={4: 75, 8: 17.5, 9: 7.5},
        status="usable",
    )
    candidate = sentinel2_ingest.CandidateScene(
        scene=scene,
        acquisition_time="2024-01-01T10:30:00Z",
        footprint=FOOTPRINT,
        catalog_cloud_cover=25,
        quality=quality,
        rejection_reasons=(),
        provenance={"collection": "sentinel-2-l2a"},
    )
    inspection = sentinel2_ingest.InspectionResult(
        candidates=(candidate,),
        provenance={"provider": "copernicus"},
    )
    download = sentinel2_ingest.DownloadResult(
        scene=scene,
        output_paths=("red.tif", Path("nir.tif")),
        crs="EPSG:32632",
        bounds=(500000, 5100000, 501000, 5101000),
        transform=(10, 0, 500000, 0, -10, 5101000),
        resolution=10,
        bands=("b04", "B08"),
        checksum="sha256:abc123",
        provenance={"processor": "sentinel2-ingest"},
    )

    assert candidate.acquisition_time == datetime(2024, 1, 1, 10, 30, tzinfo=UTC)
    assert download.output_paths == (Path("red.tif"), Path("nir.tif"))
    assert download.bands == (sentinel2_ingest.Band.B04, sentinel2_ingest.Band.B08)
    assert inspection.to_dict() == {
        "candidates": [
            {
                "scene": {
                    "scene_id": "S2A_MSIL2A_20240101T000000_N0509_R000_T32TMT",
                    "provider": "copernicus",
                    "provenance": {
                        "catalog_id": "item-123",
                        "url": "https://example.test/item-123",
                    },
                },
                "acquisition_time": "2024-01-01T10:30:00+00:00",
                "footprint": {
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
                "catalog_cloud_cover": 25.0,
                "quality": {
                    "aoi_coverage": 99.0,
                    "usable_percentage": 82.5,
                    "scl_percentages": {"4": 75.0, "8": 17.5, "9": 7.5},
                    "status": "usable",
                },
                "rejection_reasons": [],
                "provenance": {"collection": "sentinel-2-l2a"},
            }
        ],
        "provenance": {"provider": "copernicus"},
    }
    assert json.loads(json.dumps(download.to_dict())) == {
        "scene": scene.to_dict(),
        "output_paths": ["red.tif", "nir.tif"],
        "crs": "EPSG:32632",
        "bounds": [500000.0, 5100000.0, 501000.0, 5101000.0],
        "transform": [10.0, 0.0, 500000.0, 0.0, -10.0, 5101000.0],
        "resolution": 10.0,
        "bands": ["B04", "B08"],
        "checksum": "sha256:abc123",
        "provenance": {"processor": "sentinel2-ingest"},
    }


@pytest.mark.parametrize("status", ("unknown", "USABLE", 123, []))
def test_quality_metrics_reject_statuses_outside_the_public_vocabulary(
    status: object,
) -> None:
    """An unsupported status would make automatic download selection ambiguous."""
    with pytest.raises(ValueError, match="status"):
        sentinel2_ingest.AoiQualityMetrics(100, 80, {4: 80}, status)


def test_result_provenance_is_immutable_after_validation() -> None:
    """Mutating provenance after construction would bypass JSON validation."""
    scene = sentinel2_ingest.SceneReference(
        "scene-1", "provider", {"catalog_id": "item-1"}
    )

    with pytest.raises(TypeError):
        cast(dict[str, object], scene.provenance)["non_json"] = object()


@pytest.mark.parametrize(
    ("aoi_coverage", "usable_percentage", "scl_percentages"),
    [(-1, 80, {4: 80}), (100, 101, {4: 80}), (100, 80, {4: 101}), (100, 80, {12: 1})],
)
def test_quality_metrics_reject_invalid_percentages_or_scl_classes(
    aoi_coverage: object,
    usable_percentage: object,
    scl_percentages: object,
) -> None:
    """Invalid quality measurements must not be exposed as candidate evidence."""
    with pytest.raises(ValueError):
        sentinel2_ingest.AoiQualityMetrics(
            aoi_coverage,
            usable_percentage,
            scl_percentages,
            "usable",
        )


@pytest.mark.parametrize(
    ("output_paths", "bounds", "transform", "checksum"),
    [
        ((), (0, 0, 1, 1), (1, 0, 0, 0, -1, 1), "sha256:abc"),
        (("",), (0, 0, 1, 1), (1, 0, 0, 0, -1, 1), "sha256:abc"),
        ((Path("."),), (0, 0, 1, 1), (1, 0, 0, 0, -1, 1), "sha256:abc"),
        (("result.tif",), (0, 0, 0, 1), (1, 0, 0, 0, -1, 1), "sha256:abc"),
        (("result.tif",), (0, 0, 1, 1), (1, 0, 0), "sha256:abc"),
        (("result.tif",), (0, 0, 1, 1), (1, 0, 0, 0, -1, 1), ""),
    ],
)
def test_download_result_rejects_invalid_output_metadata(
    output_paths: object,
    bounds: object,
    transform: object,
    checksum: object,
) -> None:
    """Malformed raster metadata must fail before callers consume the result."""
    scene = sentinel2_ingest.SceneReference("scene-1", "provider", {})

    with pytest.raises(ValueError):
        sentinel2_ingest.DownloadResult(
            scene=scene,
            output_paths=output_paths,
            crs="EPSG:32632",
            bounds=bounds,
            transform=transform,
            resolution=10,
            bands=("B04",),
            checksum=checksum,
            provenance={},
        )


def test_result_models_are_reexported_from_the_package_root() -> None:
    """Callers should not need to import an internal result-model module."""
    assert sentinel2_ingest.SceneReference.__module__ == "sentinel2_ingest.results"
    assert sentinel2_ingest.CandidateScene.__module__ == "sentinel2_ingest.results"
    assert sentinel2_ingest.AoiQualityMetrics.__module__ == "sentinel2_ingest.results"
    assert sentinel2_ingest.InspectionResult.__module__ == "sentinel2_ingest.results"
    assert sentinel2_ingest.DownloadResult.__module__ == "sentinel2_ingest.results"
