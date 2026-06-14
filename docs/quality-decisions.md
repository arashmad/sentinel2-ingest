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

## Quality decisions

Sentinel2 Ingest classifies, ranks, and selects candidate scenes during local inspection.

These rules are provider-independent. They apply to fake-provider results today and should also apply to real Sentinel Hub / Copernicus Data Space results after AOI-level quality metrics are available.

### Quality source

Scene-level cloud coverage is only a coarse pre-filter.

A scene must not be treated as truly usable only because the provider reports low scene-level cloud coverage. The final decision should be based on AOI-level quality metrics calculated for the requested polygon.

For Sentinel-2 L2A, AOI-level quality should eventually be calculated from:

```txt
SCL
dataMask
```

The package stores the normalized result in `AoiQualityMetrics`.

### Default thresholds

The default local thresholds are:

```python
min_usable_pixel_ratio = 0.80
max_cloud_pixel_ratio = 0.10
max_shadow_pixel_ratio = 0.10
max_no_data_ratio = 0.05
```

These values mean:

| Threshold | Meaning |
| --- | --- |
| `min_usable_pixel_ratio` | Minimum acceptable ratio of usable pixels inside the AOI |
| `max_cloud_pixel_ratio` | Maximum acceptable cloud ratio inside the AOI |
| `max_shadow_pixel_ratio` | Maximum acceptable cloud-shadow ratio inside the AOI |
| `max_no_data_ratio` | Maximum acceptable no-data ratio inside the AOI |

### Quality statuses

`classify_quality()` returns a quality status and a list of reasons.

#### `usable`

A candidate is `usable` when all configured thresholds pass.

Expected behavior:

```txt
status = usable
reasons = []
```

#### `risky`

A candidate is `risky` when one or more thresholds fail, but the usable-pixel ratio is still moderate enough that a caller may choose to inspect or allow it explicitly.

Risky candidates are not selected by default by `select_best_candidate()`.

#### `rejected`

A candidate is `rejected` when quality is too poor to be selected.

Rejected candidates are never selected by `select_best_candidate()`.

### Quality reasons

When a candidate fails one or more thresholds, the classifier returns human-readable reasons.

Examples:

```txt
AOI usable pixel ratio 0.700 is below threshold 0.800.
AOI cloud pixel ratio 0.200 is above threshold 0.100.
AOI shadow pixel ratio 0.120 is above threshold 0.100.
AOI no-data ratio 0.200 is above threshold 0.050.
```

Multiple reasons can be returned for the same candidate.

### Candidate ranking

`rank_candidates()` sorts candidates from best to worst.

Ranking order:

1. Candidates with quality metrics and quality status before incomplete candidates.
2. `usable` before `risky`.
3. `risky` before `rejected`.
4. Higher usable-pixel ratio.
5. Lower cloud-pixel ratio.
6. Lower shadow-pixel ratio.
7. Newer acquisition datetime.
8. Deterministic final tie-breaker, such as `scene_id`.

Candidates without quality metrics or without quality status are ranked last.

`Sentinel2IngestClient.inspect()` returns ranked candidates so callers get stable default ordering.

### Best-candidate selection

`select_best_candidate()` selects the best acceptable candidate from a list.

Default behavior:

```python
best = select_best_candidate(candidates)
```

This returns the best `usable` candidate, or `None` if no usable candidate exists.

Risky candidates must be allowed explicitly:

```python
best = select_best_candidate(candidates, allow_risky=True)
```

Even when risky candidates are allowed, usable candidates are still preferred.

Rejected candidates are never selected.

The helper only selects a candidate. It does not trigger downloads.

### Provider boundary

Providers may fetch, calculate, or map quality data, but the final provider-independent decision should stay in the inspection layer.

Provider-specific response shapes must be mapped into package models before classification and ranking.

### Non-goals

Quality decisions do not:

- download raster bands
- generate thumbnails
- write database rows
- decide application ownership
- depend on GeoInsight-specific behavior
- treat scene-level cloud coverage as final AOI quality