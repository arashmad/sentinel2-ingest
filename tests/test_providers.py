"""Internal scene-provider protocol tests."""

from datetime import UTC, datetime

from shapely.geometry import Polygon

from sentinel2_ingest.bands import Band
from sentinel2_ingest.providers import (
    FakeSceneProvider,
    ProviderScene,
    RasterAsset,
    SceneProvider,
)
from sentinel2_ingest.requests import InspectionRequest
from sentinel2_ingest.results import SceneReference

AOI = Polygon([(10, 45), (11, 45), (11, 46), (10, 46), (10, 45)])


def test_fake_provider_fulfills_scene_and_asset_operations_deterministically() -> None:
    """Orchestration can rely on the fake without STAC or raster dependencies."""
    scene = ProviderScene(
        reference=SceneReference("scene-1", "fake", {"catalog_id": "item-1"}),
        acquisition_time=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
        footprint=AOI,
        catalog_cloud_cover=12.5,
        crs="EPSG:32632",
        scl_asset=RasterAsset("memory://scene-1/scl"),
        reflectance_assets={
            Band.B04: RasterAsset("memory://scene-1/B04"),
            Band.B08: RasterAsset("memory://scene-1/B08"),
        },
        provenance={"collection": "test-scenes"},
    )
    provider = FakeSceneProvider((scene,))
    request = InspectionRequest(AOI, "2024-01-01", "2024-01-31")

    assert isinstance(provider, SceneProvider)
    assert provider.search(request) == (scene,)
    assert provider.lookup("scene-1") == scene
    assert provider.scl_asset(scene) == RasterAsset("memory://scene-1/scl")
    assert provider.reflectance_asset(scene, Band.B08) == RasterAsset(
        "memory://scene-1/B08"
    )
