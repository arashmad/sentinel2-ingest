# Sentinel-2 Bands and Resolution

This document describes the Sentinel-2 L2A raw band support and resolution expectations for `sentinel2-ingest`.

The goal is to keep band validation, download behavior, and future raster processing decisions explicit before real download/resampling code is added.

## Supported Sentinel-2 L2A bands

V1 supports raw Sentinel-2 L2A bands only.

Supported bands:

```python
SUPPORTED_BANDS = {
    "B01",
    "B02",
    "B03",
    "B04",
    "B05",
    "B06",
    "B07",
    "B08",
    "B8A",
    "B09",
    "B11",
    "B12",
}
```

`B10` is intentionally not supported because it is not available as a Sentinel-2 L2A surface reflectance band.

## Native resolution groups

Sentinel-2 bands do not all have the same native spatial resolution.

### 10 m bands

```txt
B02, B03, B04, B08
```

These are the highest-resolution visible/NIR bands and are used as the default download band set.

### 20 m bands

```txt
B05, B06, B07, B8A, B11, B12
```

These bands have lower native resolution than the 10 m bands. If they are requested together with 10 m bands, a later download/raster implementation must decide how output resolution and resampling are handled.

### 60 m bands

```txt
B01, B09
```

These bands have lower native resolution than both 10 m and 20 m bands. Mixed requests including 60 m bands may require additional care in later provider-side or raster-side processing.

## Default download bands

The default raw-band request is:

```python
DEFAULT_BANDS = ("B02", "B03", "B04", "B08")
```

These are all 10 m bands.

## Thumbnail bands

The default thumbnail band request is RGB order:

```python
THUMBNAIL_BANDS = ("B04", "B03", "B02")
```

These are all 10 m bands.

## Output resolution behavior

`DownloadRequest.resolution` currently defines the requested output resolution value, with a default of `10`.

At the M4 stage, the package validates band names and normalizes requested band names, but it does not download rasters and does not perform resampling.

This means:

* validation can reject unsupported bands;
* validation can normalize band names such as `b02` to `B02`;
* validation can detect duplicate bands after normalization;
* validation does not guarantee that mixed-resolution bands have been resampled;
* validation does not define provider-specific output raster behavior.

Actual output-resolution handling belongs to later download/raster implementation work.

## Mixed-resolution requests

A request such as:

```python
bands = ("B02", "B03", "B04", "B08")
resolution = 10
```

uses only 10 m native bands and should not require mixed-resolution resampling.

A request such as:

```python
bands = ("B02", "B03", "B04", "B8A", "B11")
resolution = 10
```

mixes 10 m and 20 m native bands. A later implementation must decide whether resampling happens provider-side, raster-side, or through another explicit strategy.

A request such as:

```python
bands = ("B02", "B09")
resolution = 10
```

mixes 10 m and 60 m native bands. This also requires explicit output-resolution handling later.

## Current M4 boundary

M4 only covers band support and request validation.

M4 does not implement:

* raster downloads;
* thumbnail generation;
* provider-side resampling;
* raster-side resampling;
* GeoTIFF writing;
* Sentinel Hub integration;
* Rasterio integration.

The download implementation should use this document as the baseline for later output-resolution decisions.
