"""Internal provider boundary for catalog scenes and raster assets.

This module deliberately uses only provider-neutral values. Provider adapters
translate STAC and raster-library objects at this boundary rather than exposing
them to the package's public request and result models.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol, cast, runtime_checkable

from pystac_client import Client
from shapely.geometry import Polygon

from .bands import Band
from .requests import InspectionRequest
from .results import SceneReference

EARTH_SEARCH_URL = "https://earth-search.aws.element84.com/v1/"
"""Public, anonymous Element 84 Earth Search STAC API endpoint."""

EARTH_SEARCH_COLLECTION = "sentinel-2-c1-l2a"
"""Element 84's current Sentinel-2 Collection 1 Level-2A collection."""


class StacSearchClient(Protocol):
    """The narrow STAC client surface needed to construct catalog searches."""

    def search(
        self,
        *,
        method: str,
        collections: list[str],
        intersects: dict[str, object],
        datetime: str,
        query: dict[str, dict[str, float]],
        limit: int,
    ) -> object:
        """Submit a STAC item search and return its unprocessed response."""


class EarthSearchClient:
    """Anonymous Element 84 STAC request adapter.

    This class intentionally returns the unprocessed STAC response. Item mapping,
    pagination, and provider error handling are separate provider responsibilities.
    """

    def __init__(self, client: StacSearchClient) -> None:
        self.client = client

    @classmethod
    def open_anonymous(cls) -> "EarthSearchClient":
        """Open the public Element 84 catalog without credentials."""
        return cls(Client.open(EARTH_SEARCH_URL))

    def search(self, request: InspectionRequest) -> object:
        """Submit one normalized inspection request as an Element 84 item search."""
        serialized_request = request.to_dict()
        aoi = cast(dict[str, object], serialized_request["aoi"])
        start_date = cast(str, serialized_request["start_date"])
        end_date = cast(str, serialized_request["end_date"])
        max_cloud_cover = cast(float, serialized_request["max_cloud_cover"])
        candidate_limit = cast(int, serialized_request["candidate_limit"])

        return self.client.search(
            method="POST",
            collections=[EARTH_SEARCH_COLLECTION],
            intersects=aoi,
            datetime=(f"{start_date}T00:00:00Z/{end_date}T23:59:59Z"),
            query={"eo:cloud_cover": {"lte": max_cloud_cover}},
            limit=candidate_limit,
        )


@dataclass(frozen=True)
class RasterAsset:
    """A provider-neutral reference to one raster asset."""

    href: str


@dataclass(frozen=True)
class ProviderScene:
    """Internal normalized scene data supplied by a catalog provider."""

    reference: SceneReference
    acquisition_time: datetime
    footprint: Polygon
    catalog_cloud_cover: float
    crs: str
    scl_asset: RasterAsset
    reflectance_assets: Mapping[Band, RasterAsset]
    provenance: Mapping[str, object]


@runtime_checkable
class SceneProvider(Protocol):
    """Operations orchestration needs from the single Tier 1 provider."""

    def search(self, request: InspectionRequest) -> Sequence[ProviderScene]:
        """Return catalog scenes matching a normalized inspection request."""

    def lookup(self, scene_id: str) -> ProviderScene:
        """Return the provider scene identified by its opaque scene ID."""

    def scl_asset(self, scene: ProviderScene) -> RasterAsset:
        """Return the scene's SCL raster asset."""

    def reflectance_asset(self, scene: ProviderScene, band: Band) -> RasterAsset:
        """Return one requested reflectance-band raster asset."""


class FakeSceneProvider:
    """Deterministic in-memory provider for workflow orchestration tests."""

    def __init__(self, scenes: Sequence[ProviderScene]) -> None:
        self._scenes = tuple(scenes)

    def search(self, request: InspectionRequest) -> tuple[ProviderScene, ...]:
        """Return configured scenes that satisfy the request's catalog filters."""
        aoi = cast(Polygon, request.aoi)
        start_date = cast(date, request.start_date)
        end_date = cast(date, request.end_date)
        matching_scenes = (
            scene
            for scene in self._scenes
            if scene.footprint.intersects(aoi)
            and start_date <= scene.acquisition_time.date() <= end_date
            and scene.catalog_cloud_cover <= request.max_cloud_cover
        )
        return tuple(matching_scenes)[: request.candidate_limit]

    def lookup(self, scene_id: str) -> ProviderScene:
        """Return a configured scene by ID or raise KeyError when it is absent."""
        for scene in self._scenes:
            if scene.reference.scene_id == scene_id:
                return scene
        raise KeyError(scene_id)

    def scl_asset(self, scene: ProviderScene) -> RasterAsset:
        """Return the configured SCL asset for a scene."""
        return scene.scl_asset

    def reflectance_asset(self, scene: ProviderScene, band: Band) -> RasterAsset:
        """Return the configured reflectance asset for a requested band."""
        return scene.reflectance_assets[band]
