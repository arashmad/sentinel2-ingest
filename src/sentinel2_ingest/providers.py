"""Internal provider boundary for catalog scenes and raster assets.

This module deliberately uses only provider-neutral values. Provider adapters
translate STAC and raster-library objects at this boundary rather than exposing
them to the package's public request and result models.
"""

from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from math import ceil, floor, isfinite
from numbers import Integral, Real
from time import sleep as default_sleep
from typing import Any, Protocol, TypeVar, cast, runtime_checkable

import numpy as np
from pystac import Asset, Item
from pystac_client import Client
from pystac_client.exceptions import APIError
from pystac_client.stac_api_io import StacApiIO
from rasterio import open as open_raster
from rasterio.enums import Resampling
from rasterio.errors import WindowError
from rasterio.features import bounds, geometry_mask
from rasterio.transform import Affine
from rasterio.warp import transform_geom
from rasterio.windows import Window
from shapely.geometry import Polygon, mapping

from .aoi import normalize_aoi
from .bands import Band
from .errors import InvalidAOIError, ProviderRequestError
from .requests import InspectionRequest
from .results import SceneReference

EARTH_SEARCH_URL = "https://earth-search.aws.element84.com/v1/"
"""Public, anonymous Element 84 Earth Search STAC API endpoint."""

EARTH_SEARCH_COLLECTION = "sentinel-2-c1-l2a"
"""Element 84's current Sentinel-2 Collection 1 Level-2A collection."""

EARTH_SEARCH_SORTBY = (
    {"field": "properties.datetime", "direction": "desc"},
    {"field": "id", "direction": "asc"},
)
"""Stable Element 84 ordering before pagination and candidate limiting."""

EARTH_SEARCH_CONNECT_TIMEOUT = 5.0
"""Maximum seconds allowed to establish an Earth Search connection."""

EARTH_SEARCH_READ_TIMEOUT = 30.0
"""Maximum seconds allowed to read one Earth Search response."""

EARTH_SEARCH_MAX_RETRIES = 3
"""Maximum retry attempts after a retryable Earth Search failure."""

EARTH_SEARCH_RETRY_BACKOFF = 0.25
"""Initial retry delay in seconds; it doubles up to one second."""

_RetryResult = TypeVar("_RetryResult")


def _is_retryable_catalog_error(error: APIError) -> bool:
    """Return whether an API failure is transient enough to retry."""
    status_code = getattr(error, "status_code", None)
    return status_code is None or status_code == 429 or status_code >= 500


def _retry_catalog_call(
    operation: Callable[[], _RetryResult],
    sleep: Callable[[float], None],
) -> _RetryResult:
    """Run a catalog operation with bounded retries for transient API errors."""
    for retry_count in range(EARTH_SEARCH_MAX_RETRIES + 1):
        try:
            return operation()
        except APIError as error:
            if (
                not _is_retryable_catalog_error(error)
                or retry_count == EARTH_SEARCH_MAX_RETRIES
            ):
                raise
            sleep(min(EARTH_SEARCH_RETRY_BACKOFF * 2**retry_count, 1.0))
    raise AssertionError("retry loop must return or raise")  # pragma: no cover


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
        sortby: list[dict[str, str]],
        limit: int,
    ) -> object:
        """Submit a STAC item search and return its unprocessed response."""


class StacItemSearch(Protocol):
    """The paginated STAC item iterator used by the provider adapter."""

    def items(self) -> Iterator[Item]:
        """Yield STAC items across all linked result pages."""


class ProtectedStacItemSearch:
    """A STAC item stream that defers protected retrieval until iteration."""

    def __init__(self, read_items: Callable[[], Iterator[Item]]) -> None:
        self._read_items = read_items

    def items(self) -> Iterator[Item]:
        """Yield provider-protected items as each STAC page arrives."""
        yield from self._read_items()


class EarthSearchClient:
    """Anonymous Element 84 STAC adapter with bounded provider failures."""

    def __init__(
        self,
        client: StacSearchClient,
        sleep: Callable[[float], None] = default_sleep,
    ) -> None:
        self.client = client
        self._sleep = sleep

    @classmethod
    def open_anonymous(
        cls, sleep: Callable[[float], None] = default_sleep
    ) -> "EarthSearchClient":
        """Open the public Element 84 catalog with bounded transport settings."""
        try:
            client = _retry_catalog_call(
                lambda: Client.open(
                    EARTH_SEARCH_URL,
                    stac_io=StacApiIO(
                        timeout=(
                            EARTH_SEARCH_CONNECT_TIMEOUT,
                            EARTH_SEARCH_READ_TIMEOUT,
                        ),
                        max_retries=0,
                    ),
                ),
                sleep,
            )
        except Exception as error:
            raise ProviderRequestError() from error
        return cls(client, sleep)

    def search(self, request: InspectionRequest) -> StacItemSearch:
        """Return a protected lazy stream for one normalized Earth Search request."""
        return ProtectedStacItemSearch(lambda: self._stream_items(request))

    def _stream_items(self, request: InspectionRequest) -> Iterator[Item]:
        """Yield a bounded item stream while retrying only transient failures."""
        yielded_ids: set[str] = set()
        for retry_count in range(EARTH_SEARCH_MAX_RETRIES + 1):
            try:
                item_search = cast(StacItemSearch, self._search_once(request))
                for item in item_search.items():
                    if item.id in yielded_ids:
                        continue
                    yielded_ids.add(item.id)
                    yield item
                    if len(yielded_ids) == request.candidate_limit:
                        return
                return
            except APIError as error:
                if (
                    not _is_retryable_catalog_error(error)
                    or retry_count == EARTH_SEARCH_MAX_RETRIES
                ):
                    raise ProviderRequestError() from error
                self._sleep(min(EARTH_SEARCH_RETRY_BACKOFF * 2**retry_count, 1.0))
            except Exception as error:
                raise ProviderRequestError() from error
        raise AssertionError(  # pragma: no cover
            "stream retry loop must return or raise"
        )

    def _search_once(self, request: InspectionRequest) -> object:
        """Submit one normalized inspection request without retry handling."""
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
            sortby=list(EARTH_SEARCH_SORTBY),
            limit=candidate_limit,
        )

    def search_scenes(self, request: InspectionRequest) -> "tuple[ProviderScene, ...]":
        """Map paginated STAC items into unique scenes up to the requested limit."""
        return self._catalog_operation(lambda: self._search_scenes_once(request))

    def _catalog_operation(self, operation: Callable[[], _RetryResult]) -> _RetryResult:
        """Retry external catalog failures and map them to the public error."""
        try:
            return _retry_catalog_call(operation, self._sleep)
        except ProviderRequestError:
            raise
        except Exception as error:
            raise ProviderRequestError() from error

    def _search_scenes_once(
        self, request: InspectionRequest
    ) -> "tuple[ProviderScene, ...]":
        """Retrieve and map one complete paginated search attempt."""
        item_search = cast(StacItemSearch, self._search_once(request))
        scene_ids: set[str] = set()
        scenes: list[ProviderScene] = []
        for item in item_search.items():
            if item.id in scene_ids:
                continue
            scene = map_earth_search_item(item)
            scene_ids.add(scene.reference.scene_id)
            scenes.append(scene)
            if len(scenes) == request.candidate_limit:
                break
        return tuple(scenes)


def _raster_asset(asset: Asset | None, label: str) -> "RasterAsset":
    """Return a STAC asset href or reject an incomplete catalog item."""
    if asset is None or not isinstance(asset.href, str) or not asset.href.strip():
        raise ValueError(f"Earth Search item is missing required {label} asset")
    return RasterAsset(asset.href)


def _asset_band_name(asset: Asset) -> str | None:
    """Return the one STAC EO band identity carried by a reflectance asset."""
    bands = asset.extra_fields.get("eo:bands")
    if not isinstance(bands, list) or len(bands) != 1:
        return None
    band = bands[0]
    if not isinstance(band, Mapping) or not isinstance(band.get("name"), str):
        return None
    return cast(str, band["name"])


def _reflectance_asset(item: Item, band: Band) -> "RasterAsset":
    """Resolve a reflectance asset from STAC band metadata or its common name."""
    matching_assets = [
        asset for asset in item.assets.values() if _asset_band_name(asset) == band.value
    ]
    if len(matching_assets) == 1:
        return _raster_asset(matching_assets[0], "reflectance")
    if len(matching_assets) > 1:
        raise ValueError("Earth Search item has ambiguous reflectance assets")
    return _raster_asset(item.assets.get(band.earth_search_name), "reflectance")


def _scl_asset(item: Item) -> "RasterAsset":
    """Resolve the SCL asset from STAC title metadata or its common name."""
    matching_assets = [
        asset
        for name, asset in item.assets.items()
        if name.lower() == "scl"
        or (
            isinstance(asset.title, str)
            and "scene classification" in asset.title.lower()
        )
    ]
    if len(matching_assets) != 1:
        raise ValueError("Earth Search item is missing required SCL asset")
    return _raster_asset(matching_assets[0], "SCL")


def map_earth_search_item(item: Item) -> "ProviderScene":
    """Convert one Element 84 STAC item into validated provider-neutral data."""
    if not isinstance(item.id, str) or not item.id.strip():
        raise ValueError("Earth Search item is missing required identity")
    if (
        not isinstance(item.datetime, datetime)
        or item.datetime.tzinfo is None
        or item.datetime.utcoffset() is None
    ):
        raise ValueError("Earth Search item is missing required acquisition time")
    if item.geometry is None:
        raise ValueError("Earth Search item is missing required footprint")
    try:
        footprint = normalize_aoi(item.geometry)
    except InvalidAOIError as error:
        raise ValueError("Earth Search item has an invalid footprint") from error

    projection = item.properties.get("proj:epsg")
    if isinstance(projection, bool) or not isinstance(projection, Integral):
        raise ValueError("Earth Search item is missing required projection")
    normalized_projection = int(projection)
    if (
        not 32601 <= normalized_projection <= 32660
        and not 32701 <= normalized_projection <= 32760
    ):
        raise ValueError("Earth Search item is missing required projection")

    cloud_cover = item.properties.get("eo:cloud_cover")
    if isinstance(cloud_cover, bool) or not isinstance(cloud_cover, Real):
        raise ValueError("Earth Search item is missing required cloud cover")
    normalized_cloud_cover = float(cloud_cover)
    if not isfinite(normalized_cloud_cover) or not 0 <= normalized_cloud_cover <= 100:
        raise ValueError("Earth Search item is missing required cloud cover")

    properties = cast(dict[str, Any], item.to_dict()["properties"])
    provenance = {"collection": item.collection_id, "properties": properties}
    reflectance_assets = {band: _reflectance_asset(item, band) for band in Band}
    return ProviderScene(
        reference=SceneReference(item.id, "earth-search", provenance),
        acquisition_time=item.datetime,
        footprint=footprint,
        catalog_cloud_cover=normalized_cloud_cover,
        crs=f"EPSG:{normalized_projection}",
        scl_asset=_scl_asset(item),
        reflectance_assets=reflectance_assets,
        provenance=provenance,
    )


@dataclass(frozen=True)
class RasterAsset:
    """A provider-neutral reference to one raster asset."""

    href: str


@dataclass(frozen=True)
class SclAoiWindow:
    """SCL pixels and spatial metadata for the part of a raster inside one AOI."""

    values: np.ndarray[Any, Any]
    transform: Affine
    nodata: float | int | None
    aoi_mask: np.ndarray[Any, np.dtype[np.bool_]]


def read_scl_aoi_window(asset: RasterAsset, aoi: Polygon) -> SclAoiWindow:
    """Read only one WGS84 AOI's categorical SCL pixels from a raster asset."""
    normalized_aoi = normalize_aoi(aoi)
    with open_raster(asset.href) as dataset:
        if dataset.crs is None:
            raise ValueError("SCL asset is missing a coordinate reference system")
        projected_aoi = transform_geom(
            "EPSG:4326", dataset.crs, mapping(normalized_aoi)
        )
        requested_window = dataset.window(*bounds(projected_aoi))
        col_off = floor(requested_window.col_off)
        row_off = floor(requested_window.row_off)
        window = Window(
            col_off,
            row_off,
            ceil(requested_window.col_off + requested_window.width) - col_off,
            ceil(requested_window.row_off + requested_window.height) - row_off,
        )
        try:
            window = window.intersection(Window(0, 0, dataset.width, dataset.height))
        except WindowError as error:
            raise ValueError("AOI does not intersect the SCL asset") from error
        transform = dataset.window_transform(window)
        values = dataset.read(1, window=window, resampling=Resampling.nearest)
        aoi_mask = geometry_mask(
            [projected_aoi],
            out_shape=values.shape,
            transform=transform,
            invert=True,
        )
        return SclAoiWindow(values, transform, dataset.nodata, aoi_mask)


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
