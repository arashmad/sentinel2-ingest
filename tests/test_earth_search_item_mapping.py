"""Offline Earth Search STAC-item mapping tests."""

from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from pystac import Asset, Item

from sentinel2_ingest.bands import Band
from sentinel2_ingest.providers import map_earth_search_item


def _item(use_opaque_asset_keys: bool = False) -> Item:
    item = Item(
        id="S2A_32TMT_20240115_0_L2A",
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
        "classification" if use_opaque_asset_keys else "scl",
        Asset(
            href="https://example.test/scene/scl.tif",
            title="Scene classification map (SCL)",
        ),
    )
    for band in Band:
        asset_name = (
            f"asset-{band.value.lower()}"
            if use_opaque_asset_keys
            else band.earth_search_name
        )
        item.add_asset(
            asset_name,
            Asset(
                href=f"https://example.test/scene/{band.earth_search_name}.tif",
                extra_fields={
                    "eo:bands": [
                        {"name": band.value, "common_name": band.earth_search_name}
                    ]
                },
            ),
        )
    return item


def test_map_earth_search_item_converts_stac_metadata_and_asset_hrefs() -> None:
    """A mapper that rewrites metadata or fabricates URLs corrupts a scene record."""
    scene = map_earth_search_item(_item())

    assert scene.reference.scene_id == "S2A_32TMT_20240115_0_L2A"
    assert scene.reference.provider == "earth-search"
    assert scene.acquisition_time == datetime(2024, 1, 15, 10, 30, tzinfo=UTC)
    assert scene.footprint.wkt == "POLYGON ((10 45, 11 45, 11 46, 10 46, 10 45))"
    assert scene.catalog_cloud_cover == 12.5
    assert scene.crs == "EPSG:32632"
    assert scene.scl_asset.href == "https://example.test/scene/scl.tif"
    assert (
        scene.reflectance_assets[Band.B08].href == "https://example.test/scene/nir.tif"
    )
    assert scene.provenance == {
        "collection": "sentinel-2-c1-l2a",
        "properties": {
            "datetime": "2024-01-15T10:30:00Z",
            "eo:cloud_cover": 12.5,
            "proj:epsg": 32632,
        },
    }


def test_map_earth_search_item_uses_asset_metadata_when_common_asset_keys_change() -> (
    None
):
    """Opaque asset keys must not prevent STAC metadata from selecting a band."""
    scene = map_earth_search_item(_item(use_opaque_asset_keys=True))

    assert scene.scl_asset.href == "https://example.test/scene/scl.tif"
    assert (
        scene.reflectance_assets[Band.B08].href == "https://example.test/scene/nir.tif"
    )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda item: setattr(item, "id", ""), "identity"),
        (lambda item: setattr(item, "datetime", None), "acquisition time"),
        (
            lambda item: setattr(item, "datetime", datetime(2024, 1, 15, 10, 30)),
            "acquisition time",
        ),
        (lambda item: setattr(item, "geometry", None), "footprint"),
        (lambda item: item.properties.pop("proj:epsg"), "projection"),
        (lambda item: item.properties.__setitem__("proj:epsg", 4326), "projection"),
        (lambda item: item.properties.pop("eo:cloud_cover"), "cloud cover"),
        (lambda item: item.assets.pop("scl"), "SCL"),
        (lambda item: item.assets.pop("nir"), "reflectance"),
    ],
)
def test_map_earth_search_item_rejects_missing_required_metadata_and_assets(
    mutate: Callable[[Item], None],
    message: str,
) -> None:
    """Missing required STAC identity, metadata, or assets must not make a scene."""
    item = _item()
    mutate(item)

    with pytest.raises(ValueError, match=message):
        map_earth_search_item(item)


def test_map_earth_search_item_rejects_malformed_footprint() -> None:
    """A self-intersecting STAC polygon must not cross the provider boundary."""
    item = _item()
    item.geometry = {
        "type": "Polygon",
        "coordinates": [[[10, 45], [11, 46], [11, 45], [10, 46], [10, 45]]],
    }

    with pytest.raises(ValueError, match="footprint"):
        map_earth_search_item(item)
