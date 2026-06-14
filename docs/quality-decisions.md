# Quality Decisions

This document explains how Sentinel2 Ingest classifies, ranks, and selects candidate Sentinel-2 scenes during inspection.

The goal is to keep local inspection decisions explicit, testable, and provider-independent before adding Sentinel Hub / Copernicus Data Space integration.

## Quality inputs

Quality decisions are based on AOI-level metrics stored in `AoiQualityMetrics`.

Important ratios:

- `usable_pixel_ratio`
- `cloud_pixel_ratio`
- `shadow_pixel_ratio`
- `no_data_ratio`

Scene-level cloud coverage can be used as a coarse provider-side pre-filter, but it is not enough to decide whether a scene is usable for the requested AOI.

A candidate should only be considered truly usable after AOI-level quality metrics have been calculated from SCL/dataMask or equivalent mask data.

## Default thresholds

The current default thresholds are:

```python
min_usable_pixel_ratio = 0.80
max_cloud_pixel_ratio = 0.10
max_shadow_pixel_ratio = 0.10
max_no_data_ratio = 0.05
```