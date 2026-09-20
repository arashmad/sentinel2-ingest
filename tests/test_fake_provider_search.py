"""Behavior tests for deterministic fake provider search."""

from datetime import UTC, datetime

from shapely.geometry import Polygon

from sentinel2_ingest.bands import Band
from sentinel2_ingest.providers import FakeSceneProvider, ProviderScene, RasterAsset
from sentinel2_ingest.requests import InspectionRequest
from sentinel2_ingest.results import SceneReference

AOI = Polygon([(10, 45), (11, 45), (11, 46), (10, 46), (10, 45)])


def _scene(
    scene_id: str,
    acquired: datetime,
    cloud_cover: float,
    footprint: Polygon = AOI,
) -> ProviderScene:
    return ProviderScene(
        reference=SceneReference(scene_id, "fake", {}),
        acquisition_time=acquired,
        footprint=footprint,
        catalog_cloud_cover=cloud_cover,
        crs="EPSG:32632",
        scl_asset=RasterAsset(f"memory://{scene_id}/scl"),
        reflectance_assets={Band.B04: RasterAsset(f"memory://{scene_id}/B04")},
        provenance={},
    )


def test_fake_provider_search_excludes_scenes_outside_catalog_filters() -> None:
    """A fake search must not return out-of-date or too-cloudy candidates."""
    matching = _scene("matching", datetime(2024, 1, 15, tzinfo=UTC), 20)
    old = _scene("old", datetime(2023, 12, 31, tzinfo=UTC), 20)
    cloudy = _scene("cloudy", datetime(2024, 1, 20, tzinfo=UTC), 21)
    provider = FakeSceneProvider((old, matching, cloudy))
    request = InspectionRequest(
        AOI,
        "2024-01-01",
        "2024-01-31",
        max_cloud_cover=20,
    )

    assert provider.search(request) == (matching,)


def test_fake_provider_search_respects_candidate_limit() -> None:
    """A fake search must not return more candidates than requested."""
    first = _scene("first", datetime(2024, 1, 15, tzinfo=UTC), 20)
    second = _scene("second", datetime(2024, 1, 16, tzinfo=UTC), 20)
    provider = FakeSceneProvider((first, second))
    request = InspectionRequest(
        AOI,
        "2024-01-01",
        "2024-01-31",
        candidate_limit=1,
    )

    assert provider.search(request) == (first,)


def test_fake_provider_search_excludes_scenes_outside_request_aoi() -> None:
    """A fake search must not return catalog candidates outside the request AOI."""
    matching = _scene("matching", datetime(2024, 1, 15, tzinfo=UTC), 20)
    outside = _scene(
        "outside",
        datetime(2024, 1, 16, tzinfo=UTC),
        20,
        Polygon([(20, 50), (21, 50), (21, 51), (20, 51), (20, 50)]),
    )
    provider = FakeSceneProvider((matching, outside))
    request = InspectionRequest(AOI, "2024-01-01", "2024-01-31")

    assert provider.search(request) == (matching,)
