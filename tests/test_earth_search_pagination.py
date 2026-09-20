"""Offline pagination tests for Element 84 scene searches."""

from collections.abc import Iterator, Sequence
from datetime import UTC, datetime

from pystac import Asset, Item

from sentinel2_ingest.bands import Band
from sentinel2_ingest.providers import EarthSearchClient
from sentinel2_ingest.requests import InspectionRequest


class PagedItemSearch:
    """A local STAC search result that exposes each consumed page."""

    def __init__(self, pages: Sequence[Sequence[Item]]) -> None:
        self.pages = pages
        self.pages_consumed = 0

    def items(self) -> Iterator[Item]:
        for page in self.pages:
            self.pages_consumed += 1
            yield from page


class PagedStacClient:
    """A local STAC client returning one predefined paginated result."""

    def __init__(self, search: PagedItemSearch) -> None:
        self.search_result = search

    def search(self, **_: object) -> PagedItemSearch:
        return self.search_result


def _item(scene_id: str) -> Item:
    item = Item(
        id=scene_id,
        geometry={
            "type": "Polygon",
            "coordinates": [[[10, 45], [11, 45], [11, 46], [10, 46], [10, 45]]],
        },
        bbox=[10, 45, 11, 46],
        datetime=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
        properties={"proj:epsg": 32632, "eo:cloud_cover": 12.5},
        collection="sentinel-2-c1-l2a",
    )
    item.add_asset(
        "scl",
        Asset(
            href=f"https://example.test/{scene_id}/scl.tif",
            title="Scene classification map (SCL)",
        ),
    )
    for band in Band:
        item.add_asset(
            band.earth_search_name,
            Asset(
                href=f"https://example.test/{scene_id}/{band.earth_search_name}.tif",
                extra_fields={"eo:bands": [{"name": band.value}]},
            ),
        )
    return item


def _request(candidate_limit: int = 20) -> InspectionRequest:
    return InspectionRequest(
        {
            "type": "Polygon",
            "coordinates": [[[10, 45], [11, 45], [11, 46], [10, 46], [10, 45]]],
        },
        "2024-01-01",
        "2024-01-31",
        candidate_limit=candidate_limit,
    )


def test_search_scenes_follows_multiple_pages_in_catalog_order() -> None:
    """Stopping after the first STAC page would lose eligible catalog scenes."""
    search = PagedItemSearch(((_item("first"),), (_item("second"),)))

    scenes = EarthSearchClient(PagedStacClient(search)).search_scenes(_request())

    assert [scene.reference.scene_id for scene in scenes] == ["first", "second"]
    assert search.pages_consumed == 2


def test_search_scenes_deduplicates_scene_ids_without_reordering() -> None:
    """Repeated items must retain the first catalog occurrence only."""
    search = PagedItemSearch(((_item("first"), _item("first")), (_item("second"),)))

    scenes = EarthSearchClient(PagedStacClient(search)).search_scenes(_request())

    assert [scene.reference.scene_id for scene in scenes] == ["first", "second"]


def test_search_scenes_returns_empty_results_for_empty_pages() -> None:
    """An empty STAC result must remain an empty provider-scene sequence."""
    search = PagedItemSearch(((),))

    assert EarthSearchClient(PagedStacClient(search)).search_scenes(_request()) == ()


def test_search_scenes_stops_before_later_pages_after_reaching_the_limit() -> None:
    """Continuing after the requested cap wastes catalog calls and breaks the limit."""
    search = PagedItemSearch(((_item("first"),), (_item("second"),)))

    scenes = EarthSearchClient(PagedStacClient(search)).search_scenes(_request(1))

    assert [scene.reference.scene_id for scene in scenes] == ["first"]
    assert search.pages_consumed == 1
