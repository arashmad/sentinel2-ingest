"""Internal provider boundary for catalog scenes and raster assets.

This module deliberately uses only provider-neutral values. Provider adapters
translate STAC and raster-library objects at this boundary rather than exposing
them to the package's public request and result models.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol, cast, runtime_checkable

from shapely.geometry import Polygon

from .bands import Band
from .requests import InspectionRequest
from .results import SceneReference


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
        start_date = cast(date, request.start_date)
        end_date = cast(date, request.end_date)
        return tuple(
            scene
            for scene in self._scenes
            if start_date <= scene.acquisition_time.date() <= end_date
            and scene.catalog_cloud_cover <= request.max_cloud_cover
        )

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
