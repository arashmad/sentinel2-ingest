"""Offline COG reads for scene-classification AOI windows."""

from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import transform
from shapely.geometry import Polygon

import sentinel2_ingest.providers as providers


def _write_scl_cog(cog_path: Path) -> None:
    """Write the fixed local COG used by every raster-reader test."""
    data = np.array(
        [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11], [12, 13, 14, 15]],
        dtype=np.uint8,
    )
    with rasterio.open(
        cog_path,
        "w",
        driver="COG",
        height=4,
        width=4,
        count=1,
        dtype=data.dtype,
        crs="EPSG:3857",
        transform=from_origin(0, 4000, 1000, 1000),
        nodata=255,
    ) as dataset:
        dataset.write(data, 1)


def _wgs84_ring(points: list[tuple[int, int]]) -> list[tuple[float, float]]:
    """Transform one hand-specified Web Mercator fixture ring to WGS84."""
    eastings, northings = zip(*points, strict=True)
    longitude, latitude = transform(
        "EPSG:3857",
        "EPSG:4326",
        eastings,
        northings,
    )
    return list(zip(longitude, latitude, strict=True))


def test_read_scl_aoi_window_reads_only_transformed_aoi_pixels_from_local_cog(
    tmp_path: Path,
) -> None:
    """A reader that skips CRS conversion or reads a full COG returns wrong pixels."""
    cog_path = tmp_path / "scl.tif"
    _write_scl_cog(cog_path)
    aoi = Polygon(
        _wgs84_ring(
            [(1200, 1200), (2800, 1200), (2800, 2800), (1200, 2800), (1200, 1200)]
        ),
        [
            _wgs84_ring(
                [(1300, 2300), (1700, 2300), (1700, 2700), (1300, 2700), (1300, 2300)]
            )
        ],
    )

    window = providers.read_scl_aoi_window(providers.RasterAsset(str(cog_path)), aoi)

    assert window.values.tolist() == [[5, 6], [9, 10]]
    assert window.transform == from_origin(1000, 3000, 1000, 1000)
    assert window.nodata == 255
    assert window.aoi_mask.tolist() == [[True, True], [True, True]]


def test_read_scl_aoi_window_rejects_a_raster_inside_an_aoi_hole(
    tmp_path: Path,
) -> None:
    """Overlapping bounds alone must not count an AOI hole as a valid read."""
    cog_path = tmp_path / "scl.tif"
    _write_scl_cog(cog_path)
    aoi = Polygon(
        _wgs84_ring(
            [
                (-1000, -1000),
                (5000, -1000),
                (5000, 5000),
                (-1000, 5000),
                (-1000, -1000),
            ]
        ),
        [
            _wgs84_ring(
                [
                    (-100, -100),
                    (4100, -100),
                    (4100, 4100),
                    (-100, 4100),
                    (-100, -100),
                ]
            )
        ],
    )

    with pytest.raises(ValueError, match="AOI does not intersect the SCL asset"):
        providers.read_scl_aoi_window(providers.RasterAsset(str(cog_path)), aoi)


def test_read_scl_aoi_window_includes_every_pixel_touched_by_a_subpixel_aoi(
    tmp_path: Path,
) -> None:
    """Rounding a tiny but intersecting AOI to zero pixels loses its SCL evidence."""
    cog_path = tmp_path / "scl.tif"
    _write_scl_cog(cog_path)
    aoi = Polygon(
        _wgs84_ring(
            [(1999, 1999), (2001, 1999), (2001, 2001), (1999, 2001), (1999, 1999)]
        )
    )

    window = providers.read_scl_aoi_window(providers.RasterAsset(str(cog_path)), aoi)

    assert window.values.tolist() == [[5, 6], [9, 10]]
    assert window.transform == from_origin(1000, 3000, 1000, 1000)
    assert window.aoi_mask.tolist() == [[True, True], [True, True]]


def test_read_scl_aoi_window_rejects_an_aoi_outside_the_cog(tmp_path: Path) -> None:
    """A Rasterio-specific window error must not cross the provider boundary."""
    cog_path = tmp_path / "scl.tif"
    _write_scl_cog(cog_path)
    aoi = Polygon(
        _wgs84_ring(
            [
                (10_000, 10_000),
                (11_000, 10_000),
                (11_000, 11_000),
                (10_000, 11_000),
                (10_000, 10_000),
            ]
        )
    )

    with pytest.raises(ValueError, match="AOI does not intersect the SCL asset"):
        providers.read_scl_aoi_window(providers.RasterAsset(str(cog_path)), aoi)
