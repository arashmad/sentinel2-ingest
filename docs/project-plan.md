# Sentinel2 Ingest — Project Plan

_Last updated: 2026-05-16_

## 1. Project Summary

### Project name

Because this package must be completely independent and reusable outside GeoInsight, avoid `geoinsight` in the package/repository/CLI name.

Recommended repository name:

```txt
sentinel2-ingest
```

Recommended Python package name:

```txt
sentinel2_ingest
```

Recommended CLI name:

```txt
sentinel2-ingest
```

Alternative names:

```txt
s2-scene-ingest
sentinel-scene-ingest
sentinel2-scene-downloader
```

GeoInsight API should consume this package as a normal external dependency. It should not be embedded into the package name, models, paths, or public API.

### Goal

Build a small reusable Python package that can inspect and download Sentinel-2 satellite imagery for any Python project.

GeoInsight API is one intended consumer, but the package must not depend on GeoInsight concepts, database schema, project structure, or business logic.

The package is not a full remote-sensing analysis platform. Its job is:

```txt
Inspect Sentinel-2 candidates for a single AOI/date range
→ calculate AOI-level usability/quality
→ generate thumbnails
→ allow one scene to be selected
→ download selected raw bands as one multiband GeoTIFF
→ save metadata
```

### Why this exists

Many geospatial projects need a clean way to inspect Sentinel-2 scenes, estimate AOI-level usability, and download selected raw bands.

GeoInsight API will use this package as a downstream consumer, but this package must remain independent. It should provide a generic Sentinel-2 ingestion boundary so consuming applications do not directly depend on Sentinel Hub implementation details.

### Installation strategy

V1:

```bash
pip install git+https://github.com/<owner>/sentinel2-ingest.git
```

V2:

```bash
pip install sentinel2-ingest
```

---

## 2. Core Decisions

### D0 — The package must be completely independent

This is a standalone Sentinel-2 ingestion library.

It must not depend on:

```txt
GeoInsight API
GeoInsight database schema
GeoInsight domain models
GeoInsight folder structure
GeoInsight naming conventions
GeoInsight business workflows
FastAPI
PostgreSQL/PostGIS
Any specific consuming application
```

The package should expose generic Python and CLI interfaces.

Allowed generic concepts:

```txt
AOI
date range
Sentinel-2 collection
candidate scene
scene quality
cloud/shadow/no-data metrics
thumbnail
raw band download
GeoTIFF output
metadata JSON
```

Disallowed project-specific concepts:

```txt
GeoInsight project
GeoInsight analysis job
GeoInsight source ID
GeoInsight user ID
GeoInsight database record
GeoInsight API route
```

GeoInsight-specific integration must live outside this package, either inside the GeoInsight API repository or in a thin adapter layer.

Recommended integration boundary:

```txt
sentinel2-ingest package
→ generic inspect/download result
→ GeoInsight adapter/service maps result into GeoInsight-specific DB/API models
```

Decision: this package must remain usable in any Python project, CLI workflow, notebook, batch job, or future API service.

### Independence design rules

The following rules protect reusability:

```txt
1. No imports from GeoInsight API.
2. No GeoInsight-specific model names.
3. No database writes in the core package.
4. No FastAPI dependency in the core package.
5. No assumption about where files are stored.
6. No assumption about user/project ownership.
7. No business-specific analysis logic.
8. No hardcoded output paths tied to one repository.
9. Public return values must be serializable and generic.
10. Provider-specific details must stay behind provider abstractions.
```

The package should be usable in:

```txt
standalone Python scripts
Jupyter notebooks
CLI workflows
Airflow/Prefect/n8n pipelines
FastAPI/Django/Flask backends
GeoInsight API
other geospatial products
```

### D1 — V1 supports only Sentinel-2 L2A

Use Sentinel-2 Level-2A as the first supported data collection.

Reason:

- It provides atmospherically corrected surface reflectance.
- It includes the `SCL` scene classification band.
- `SCL` is needed for AOI-level usable-pixel estimation.

Collection identifier:

```txt
sentinel-2-l2a
```

### D2 — V1 uses Sentinel Hub / Copernicus Data Space APIs

Use `sentinelhub-py` as the first provider integration.

The package should hide this behind a provider abstraction so that another source can be added later.

Initial provider:

```txt
SentinelHubProvider
```

Potential later providers:

```txt
CDSE STAC/OData
Microsoft Planetary Computer STAC
AWS open data
Local raster files
```

### D3 — V1 is an inspect-then-download package

Do not design the package as a direct downloader only.

Correct workflow:

```txt
inspect()
→ choose candidate
→ download()
```

Inspection must produce enough information to decide whether a candidate scene is worth downloading.

### D4 — V1 supports only single Polygon AOI

Supported:

```json
{
  "type": "Polygon",
  "coordinates": [...]
}
```

Not supported in v1:

```txt
MultiPolygon
Feature
FeatureCollection
GeometryCollection
LineString
Point
```

Reason: this keeps geometry validation, pixel statistics, thumbnail generation, and output clipping simpler.

### D5 — Raw raster data is stored as files

Do not store raster pixels in PostgreSQL/PostGIS in v1.

Use:

```txt
GeoTIFF files + JSON metadata
```

Reason:

- Raster files can become large.
- File storage is simpler for v1.
- GeoInsight API can store metadata later if needed.
- Database insertion would couple this package to GeoInsight API too early.

### D6 — AOI-level usable-pixel check is required in v1

Scene-level cloud coverage is not sufficient.

A scene can have acceptable tile-level cloud coverage but still be unusable over the specific AOI. Therefore v1 inspection must calculate AOI-level quality from `SCL` and `dataMask`.

### D7 — V1 downloads raw bands only

No derived indices in v1.

Out of scope:

```txt
NDVI
NDWI
NBR
Temporal composites
Cloud gap filling
ML cloud detection
Mosaicking across multiple dates
```

---

## 3. External Facts / Provider Assumptions

These assumptions should be rechecked if provider behavior changes.

1. `sentinelhub-py` is the official Python interface for Sentinel Hub services and supports Process API, Catalog API, Statistical API, authentication, and geospatial utilities.
2. Sentinel-2 L2A is accessed with collection identifier `sentinel-2-l2a`.
3. Sentinel-2 L2A exposes optical bands, `SCL`, `CLD`, `SNW`, and `dataMask`.
4. `SCL` is available at 20 m resolution and includes classes for no data, defective pixels, dark areas, cloud shadows, vegetation, bare soils, water, low/medium/high probability clouds, cirrus, and snow/ice.
5. Sentinel Hub `maxCloudCoverage` is a precomputed tile-level metadata filter and may not reflect the actual AOI.
6. Sentinel Hub Statistical API can calculate statistics for an AOI/time period without downloading full imagery.
7. Sentinel Hub Process API can return raw band data and can save downloads to disk.

---

## 4. High-Level Architecture

```txt
sentinel2-ingest
│
├── Public API
│   ├── Sentinel2IngestClient.inspect()
│   ├── Sentinel2IngestClient.download()
│   └── Sentinel2IngestClient.select_best_candidate()
│
├── Domain models
│   ├── InspectionRequest
│   ├── CandidateScene
│   ├── AoiQualityMetrics
│   ├── DownloadRequest
│   └── DownloadResult
│
├── Provider layer
│   ├── BaseSentinelProvider
│   └── SentinelHubProvider
│
├── AOI validation
│   └── single Polygon validation
│
├── Quality inspection
│   ├── SCL statistics
│   ├── dataMask statistics
│   └── quality classification
│
├── Thumbnail generation
│   └── RGB preview PNG
│
├── Download
│   └── selected raw bands → multiband GeoTIFF
│
└── Storage
    ├── inspection metadata JSON
    ├── thumbnails
    ├── downloaded GeoTIFF
    └── download metadata JSON
```

---

## 5. Proposed Repository Structure

```txt
sentinel2-ingest/
  README.md
  pyproject.toml
  .env.example
  .gitignore

  docs/
    project-plan.md
    provider-notes.md
    api-contract.md

  examples/
    aoi.geojson
    inspect_example.py
    download_example.py

  src/
    sentinel2_ingest/
      __init__.py

      client.py
      config.py
      exceptions.py
      logging.py

      models/
        __init__.py
        requests.py
        scenes.py
        quality.py
        results.py

      aoi/
        __init__.py
        validation.py
        geometry.py

      providers/
        __init__.py
        base.py
        sentinel_hub.py
        evalscripts.py

      inspection/
        __init__.py
        service.py
        quality.py
        ranking.py
        thumbnails.py

      download/
        __init__.py
        service.py
        raster_writer.py

      storage/
        __init__.py
        paths.py
        metadata_writer.py

      cli.py

  tests/
    test_aoi_validation.py
    test_request_models.py
    test_quality_metrics.py
    test_candidate_ranking.py
    test_storage_paths.py
```

---

## 6. Public API Design

### 6.1 Client construction

```python
from sentinel2_ingest import Sentinel2IngestClient

client = Sentinel2IngestClient.from_env()
```

Environment variables:

```bash
SENTINELHUB_CLIENT_ID=
SENTINELHUB_CLIENT_SECRET=
SENTINELHUB_BASE_URL=https://sh.dataspace.copernicus.eu
SENTINELHUB_TOKEN_URL=https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token
```

### 6.2 Inspect candidates

```python
candidates = client.inspect(
    aoi=aoi_polygon_geojson,
    date_range=("2025-06-01", "2025-06-30"),
    max_scene_cloud_coverage=60,
    min_usable_pixel_ratio=0.80,
    thumbnail=True,
    output_dir="./data/inspections",
)
```

### 6.3 Select candidate

Manual selection:

```python
selected = candidates[0]
```

Automatic selection:

```python
selected = client.select_best_candidate(candidates)
```

### 6.4 Download selected scene

```python
result = client.download(
    scene_id=selected.scene_id,
    aoi=aoi_polygon_geojson,
    bands=["B02", "B03", "B04", "B08"],
    resolution=10,
    output_dir="./data/downloads",
)
```

---

## 7. CLI Design

### 7.1 Inspect

```bash
sentinel2-ingest inspect \
  --aoi ./examples/aoi.geojson \
  --date-from 2025-06-01 \
  --date-to 2025-06-30 \
  --max-scene-cloud 60 \
  --min-usable-pixel-ratio 0.80 \
  --out ./data/inspections
```

Expected output:

```txt
Inspection completed.

Candidates:
1. 2025-06-12T10:21:00Z | usable=0.86 | cloud=0.06 | shadow=0.03 | status=usable | scene_id=S2A_...
2. 2025-06-17T10:21:00Z | usable=0.58 | cloud=0.33 | shadow=0.04 | status=rejected | scene_id=S2B_...

Files:
- ./data/inspections/<inspection_id>/candidates.json
- ./data/inspections/<inspection_id>/thumbnails/
```

### 7.2 Download

```bash
sentinel2-ingest download \
  --scene-id S2A_MSIL2A_... \
  --aoi ./examples/aoi.geojson \
  --bands B02 B03 B04 B08 \
  --resolution 10 \
  --out ./data/downloads
```

Expected output:

```txt
Download completed.

GeoTIFF:
./data/downloads/<scene_id>/bands_B02_B03_B04_B08.tif

Metadata:
./data/downloads/<scene_id>/metadata.json
```

---

## 8. Data Models

Use Pydantic models for request/response validation.

### 8.1 InspectionRequest

```python
class InspectionRequest(BaseModel):
    aoi: dict
    date_from: date
    date_to: date
    max_scene_cloud_coverage: float = 60.0
    min_usable_pixel_ratio: float = 0.80
    max_cloud_pixel_ratio: float = 0.10
    max_shadow_pixel_ratio: float = 0.10
    max_no_data_ratio: float = 0.05
    thumbnail: bool = True
```

Validation rules:

```txt
date_from <= date_to
aoi.type == "Polygon"
aoi coordinates are valid
aoi is not empty
aoi is not self-intersecting
aoi area is below configured max area
thresholds are between 0 and 1, except scene cloud coverage which is 0–100
```

### 8.2 CandidateScene

```python
class CandidateScene(BaseModel):
    scene_id: str
    datetime: datetime
    provider: str = "sentinel_hub"
    collection: str = "sentinel-2-l2a"

    scene_cloud_coverage: float | None = None

    quality: AoiQualityMetrics
    quality_status: Literal["usable", "risky", "rejected"]
    quality_reasons: list[str]

    thumbnail_path: str | None = None
    provider_metadata: dict = {}
```

### 8.3 AoiQualityMetrics

```python
class AoiQualityMetrics(BaseModel):
    total_pixel_count: int
    valid_data_pixel_count: int

    usable_pixel_count: int
    cloud_pixel_count: int
    shadow_pixel_count: int
    snow_pixel_count: int
    no_data_pixel_count: int
    defective_pixel_count: int
    dark_area_pixel_count: int
    unclassified_pixel_count: int

    usable_pixel_ratio: float
    cloud_pixel_ratio: float
    shadow_pixel_ratio: float
    snow_pixel_ratio: float
    no_data_ratio: float
    defective_pixel_ratio: float
    dark_area_pixel_ratio: float
    unclassified_pixel_ratio: float
```

### 8.4 DownloadRequest

```python
class DownloadRequest(BaseModel):
    scene_id: str
    aoi: dict
    bands: list[str]
    resolution: int = 10
    output_dir: Path
```

Validation rules:

```txt
scene_id is not empty
aoi is a valid single Polygon
bands are valid Sentinel-2 L2A bands
resolution is supported
```

### 8.5 DownloadResult

```python
class DownloadResult(BaseModel):
    scene_id: str
    provider: str
    collection: str
    bands: list[str]
    file_path: Path
    metadata_path: Path
    crs: str
    resolution: int
    width: int
    height: int
    bounds: tuple[float, float, float, float]
```

---

## 9. Band Support

### 9.1 Supported raw bands in v1

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

Do not expose `B10` for Sentinel-2 L2A.

### 9.2 Default band request

```python
DEFAULT_BANDS = ["B02", "B03", "B04", "B08"]
```

### 9.3 Default thumbnail bands

```python
THUMBNAIL_BANDS = ["B04", "B03", "B02"]
```

### 9.4 Resolution handling

Default:

```python
resolution = 10
```

Important:

- Some bands are native 10 m.
- Some bands are native 20 m.
- Some bands are native 60 m.
- If mixed-resolution bands are requested, the provider will resample to the requested output resolution.
- V1 should document this clearly.
- V1 should use nearest-neighbor resampling for masks/classes and appropriate defaults for optical bands.

---

## 10. AOI-Level Quality Inspection

### 10.1 Why this is required

Do not trust scene/tile-level cloud coverage as the final decision.

The inspection must answer:

```txt
For this specific AOI, how much of the area has usable pixels in this candidate scene?
```

### 10.2 Source bands for quality

Use:

```txt
SCL
dataMask
```

Optional later:

```txt
CLD
SNW
```

### 10.3 SCL class grouping

Usable by default:

```python
USABLE_SCL_CLASSES = {
    4,  # Vegetation
    5,  # Bare soils
    6,  # Water
}
```

Rejected by default:

```python
REJECTED_SCL_CLASSES = {
    0,   # No data
    1,   # Saturated / defective
    2,   # Dark area pixels
    3,   # Cloud shadows
    7,   # Clouds low probability / unclassified
    8,   # Clouds medium probability
    9,   # Clouds high probability
    10,  # Cirrus
    11,  # Snow / ice
}
```

Decision:

- Treat class `2` as non-usable by default.
- Make this configurable later if the analysis can tolerate dark-area pixels.
- Treat class `7` as non-usable by default because it is ambiguous.

### 10.4 Quality thresholds

Defaults:

```python
min_usable_pixel_ratio = 0.80
max_cloud_pixel_ratio = 0.10
max_shadow_pixel_ratio = 0.10
max_no_data_ratio = 0.05
```

### 10.5 Quality status

```txt
usable
risky
rejected
```

Suggested classification:

```python
if (
    usable_pixel_ratio >= min_usable_pixel_ratio
    and cloud_pixel_ratio <= max_cloud_pixel_ratio
    and shadow_pixel_ratio <= max_shadow_pixel_ratio
    and no_data_ratio <= max_no_data_ratio
):
    status = "usable"
elif usable_pixel_ratio >= 0.60:
    status = "risky"
else:
    status = "rejected"
```

### 10.6 Ranking candidates

Default ranking:

```txt
1. usable scenes first
2. highest usable_pixel_ratio
3. lowest cloud_pixel_ratio
4. lowest shadow_pixel_ratio
5. newest acquisition date
```

Do not auto-download in v1 unless the caller explicitly asks for automatic selection.

---

## 11. Storage Layout

### 11.1 Inspection output

```txt
data/
  inspections/
    <inspection_id>/
      request.json
      candidates.json
      thumbnails/
        <scene_id>.png
```

### 11.2 Download output

```txt
data/
  downloads/
    <scene_id>/
      bands_B02_B03_B04_B08.tif
      metadata.json
```

### 11.3 Metadata content

`metadata.json` should include:

```json
{
  "scene_id": "...",
  "provider": "sentinel_hub",
  "collection": "sentinel-2-l2a",
  "aoi": {},
  "bands": ["B02", "B03", "B04", "B08"],
  "resolution": 10,
  "crs": "EPSG:...",
  "bounds": [],
  "width": 0,
  "height": 0,
  "quality": {},
  "source_datetime": "...",
  "created_at": "..."
}
```

---

## 12. Phase Plan

## Phase 0 — Repository Setup

### Goal

Create a clean Python package structure that can be installed from GitHub.

### Tasks

- Create repository.
- Add `pyproject.toml`.
- Configure package under `src/sentinel2_ingest`.
- Add Ruff or similar formatting/linting.
- Add pytest.
- Add `.env.example`.
- Add README with basic purpose and warning that this is v1.
- Add empty `docs/project-plan.md`.

### Boundary

No Sentinel API calls yet.

### Done when

- `pip install -e .` works.
- `pytest` runs.
- Package imports successfully:

```python
import sentinel2_ingest
```

---

## Phase 1 — Domain Models and AOI Validation

### Goal

Define the core request/response models and reject unsupported input early.

### Tasks

- Add Pydantic models:
  - `InspectionRequest`
  - `CandidateScene`
  - `AoiQualityMetrics`
  - `DownloadRequest`
  - `DownloadResult`
- Add `validate_single_polygon_aoi()`.
- Add AOI geometry normalization.
- Add supported-band validation.
- Add date-range validation.
- Add max AOI area validation.

### Boundary

No provider integration yet.

### Done when

- Valid Polygon passes.
- MultiPolygon fails with clear error.
- FeatureCollection fails with clear error.
- Invalid/self-intersecting polygon fails with clear error.
- Invalid bands fail with clear error.
- Tests cover all above cases.

---

## Phase 2 — Provider Abstraction

### Goal

Keep Sentinel Hub details isolated from public package logic.

### Tasks

- Add `BaseSentinelProvider`.
- Add method contracts:
  - `search_candidates()`
  - `calculate_aoi_quality()`
  - `generate_thumbnail()`
  - `download_bands()`
- Add `SentinelHubProvider`.
- Add config loading from environment variables.

### Boundary

Provider methods can initially raise `NotImplementedError`.

### Done when

- Public client can be created.
- Provider can be injected into client.
- Unit tests can use a fake provider.

---

## Phase 3 — Candidate Search

### Goal

Search Sentinel-2 L2A candidates for AOI/date range.

### Tasks

- Use Sentinel Hub Catalog API through `sentinelhub-py`.
- Search by:
  - AOI bbox/geometry
  - date range
  - collection `sentinel-2-l2a`
  - scene-level cloud coverage filter
- Normalize provider response into internal `CandidateScene` partial objects.
- Include provider metadata in `provider_metadata`.

### Boundary

No quality calculation yet.

### Done when

- `inspect()` can return candidate scene IDs, acquisition datetime, and scene cloud coverage.
- Results are sorted by acquisition datetime.
- Candidate search output is deterministic enough for tests through fake provider fixtures.

---

## Phase 4 — AOI Quality Inspection

### Goal

Calculate AOI-level usability for each candidate scene.

### Tasks

- Implement SCL/dataMask evalscript for selected candidate/date.
- Use Statistical API to calculate class counts over AOI.
- Convert SCL histogram/class counts into `AoiQualityMetrics`.
- Classify candidate as `usable`, `risky`, or `rejected`.
- Add quality reasons.
- Rank candidates.

### Boundary

No download of raw requested bands yet.

### Done when

- Each candidate has `quality`.
- Each candidate has `quality_status`.
- Rejected candidates include reasons.
- Ranking prefers high AOI usability over scene-level cloud coverage.
- Tests cover quality classification with mocked SCL counts.

---

## Phase 5 — Thumbnail Generation

### Goal

Generate a small visual preview for manual candidate selection.

### Tasks

- Generate RGB thumbnail using B04/B03/B02.
- Save PNG to inspection output folder.
- Link thumbnail path into `CandidateScene`.
- Use fixed thumbnail dimensions or max dimension.
- Do not let thumbnail generation failure fail the entire inspection unless strict mode is enabled.

### Boundary

Thumbnail is for visual selection only. It is not the source of quality metrics.

### Done when

- Each candidate can have a thumbnail path.
- Missing thumbnail is represented cleanly.
- Inspection still returns quality metrics even if thumbnail fails.

---

## Phase 6 — Download Selected Scene

### Goal

Download the selected scene as one multiband GeoTIFF.

### Tasks

- Accept `scene_id`, AOI, bands, resolution, output directory.
- Use Process API to request selected bands.
- Return one multiband GeoTIFF.
- Save download metadata JSON.
- Include quality metadata when available.
- Write consistent output paths.

### Boundary

No NDVI or derived analysis.

### Done when

- Downloaded file is a readable GeoTIFF.
- Band count equals requested band count.
- Metadata contains scene ID, bands, resolution, CRS, bounds, width, height, and source datetime.
- Tests can verify output path and metadata using mocked provider or small fixture.

---

## Phase 7 — CLI

### Goal

Make the package usable without writing Python code.

### Tasks

- Add CLI command:
  - `sentinel2-ingest inspect`
  - `sentinel2-ingest download`
- Add argument validation.
- Print concise result summary.
- Exit with non-zero code on validation/provider failure.

### Boundary

No interactive UI.

### Done when

- `sentinel2-ingest inspect --help` works.
- `sentinel2-ingest download --help` works.
- CLI writes files to expected paths.

---

## Phase 8 — Generic Integration Contract

### Goal

Define the generic integration contract for any consuming application, including but not limited to GeoInsight API.

### Tasks

- Add `docs/api-contract.md`.
- Document Python API usage.
- Document returned metadata.
- Document error types.
- Document expected storage layout.
- Document that GeoInsight API owns database insertion if needed.

### Boundary

No changes inside any consuming application repository yet.

### Done when

- Any consuming application can call `inspect()` and `download()` without knowing Sentinel Hub internals.
- The package returns serializable outputs that can be stored in GeoInsight API DB later.

---

## Phase 9 — Hardening

### Goal

Make v1 reliable enough for real use.

### Tasks

- Add structured exceptions:
  - `InvalidAoiError`
  - `InvalidBandError`
  - `ProviderAuthenticationError`
  - `ProviderRequestError`
  - `NoCandidatesFoundError`
  - `NoUsableCandidatesFoundError`
  - `DownloadFailedError`
- Add logging.
- Add retry behavior for transient provider errors.
- Add timeout configuration.
- Add max candidate limit.
- Add max AOI area guard.
- Add documentation examples.

### Boundary

Still no database insertion, no job queue, no cloud storage.

### Done when

- Common failures return clear actionable messages.
- Public API is stable enough for GeoInsight API integration.

---

## 13. Testing Strategy

### Unit tests

Focus on:

```txt
AOI validation
Band validation
Date validation
Quality metric calculation
Quality status classification
Candidate ranking
Storage path generation
Metadata serialization
```

### Integration tests

Optional and gated behind environment variables:

```bash
RUN_SENTINELHUB_INTEGRATION_TESTS=1
```

Test:

```txt
real inspect call
real thumbnail generation
real small AOI download
```

Do not run provider integration tests by default in CI unless credentials and cost/rate limits are controlled.

### Fixture strategy

Use fake provider responses for normal tests.

Example fake SCL counts:

```python
{
    0: 10,
    3: 20,
    4: 500,
    5: 300,
    6: 100,
    8: 40,
    9: 30,
}
```

---

## 14. Error Handling

### Validation errors

Raise before provider calls.

Examples:

```txt
AOI must be a GeoJSON Polygon. Received MultiPolygon.
Unsupported band: B10. Supported bands are: ...
date_from must be before or equal to date_to.
```

### Provider errors

Wrap provider-specific exceptions.

Example:

```txt
Sentinel Hub authentication failed. Check SENTINELHUB_CLIENT_ID and SENTINELHUB_CLIENT_SECRET.
```

### No usable candidates

There are two different states:

```txt
NoCandidatesFoundError
NoUsableCandidatesFoundError
```

Do not merge them.

Reason:

- No candidates means no Sentinel-2 scenes were found in the date range/filter.
- No usable candidates means scenes exist, but AOI quality was not good enough.

---

## 15. Non-Goals for V1

Do not include:

```txt
Database insertion
Any consuming application's API endpoint implementation
Frontend selection UI
User authentication
Async job queue
Cloud storage
STAC provider fallback
NDVI/NDWI/NBR
Temporal compositing
Mosaicking across scenes
Cloud gap filling
COG optimization
Large-area tiling
MultiPolygon support
Batch processing
```

These can be considered after the v1 inspect/download loop works.

---

## 16. Integration Boundary

### Recommended boundary

This package should be consumed as a normal external dependency.

The consuming application owns:

```txt
API routes
UI
user/project ownership
database records
job orchestration
authorization
business-specific analysis
deployment-specific storage decisions
```

This package owns:

```txt
Sentinel provider interaction
AOI validation for ingestion
candidate inspection
AOI quality metrics
thumbnail generation
raw band download
file + metadata output
generic Python/CLI API
```

### Example consuming application flow

```txt
Application endpoint/job/notebook
→ calls sentinel2_ingest.inspect()
→ receives generic candidate metadata
→ optionally stores/maps metadata into its own schema
→ user/system selects scene_id
→ calls sentinel2_ingest.download()
→ receives generic GeoTIFF + metadata output
→ application decides what to do next
```

### Example GeoInsight-specific adapter boundary

GeoInsight-specific code should live outside this package:

```txt
geoinsight_api/
  services/
    satellite_ingestion_service.py

satellite_ingestion_service.py
→ calls sentinel2_ingest
→ maps CandidateScene into GeoInsight DB model
→ maps DownloadResult into GeoInsight analysis/source records
```

This keeps `sentinel2-ingest` reusable everywhere.

---

## 17. Minimal First Development Slice

Build this first:

```txt
1. Repository setup
2. Pydantic models
3. Single Polygon AOI validation
4. Fake provider
5. inspect() returns mocked candidates
6. quality calculation from mocked SCL counts
7. candidate ranking
8. metadata JSON writing
```

Only after that, connect Sentinel Hub.

Reason:

- It prevents provider/API complexity from driving the whole design.
- It gives a stable internal contract.
- It makes tests useful before credentials/API calls are involved.

---

## 18. Suggested Implementation Order

```txt
1. Create repo and pyproject
2. Add package skeleton
3. Add models
4. Add validation
5. Add fake provider
6. Add inspection service with fake data
7. Add quality metrics and ranking
8. Add metadata writers
9. Add SentinelHubProvider.search_candidates()
10. Add SentinelHubProvider.calculate_aoi_quality()
11. Add thumbnail generation
12. Add download selected scene
13. Add CLI
14. Add docs/examples
15. Add integration tests
```

---

## 19. Initial README Positioning

Suggested README opening:

```md
# Sentinel2 Ingest

Small standalone Python package for inspecting and downloading Sentinel-2 L2A imagery for any geospatial workflow.

The package follows an inspect-then-download workflow:

1. Search Sentinel-2 candidates for a single Polygon AOI and date range.
2. Calculate AOI-level usable-pixel quality using SCL/dataMask.
3. Generate thumbnails for candidate review.
4. Download selected raw bands as one multiband GeoTIFF.
5. Save metadata for downstream applications.

V1 intentionally does not perform derived index calculation, database insertion, mosaicking, or large-area tiling.
```

---

## 20. Open Questions

These are not blocking for starting v1.

1. What should the default max AOI area be?
2. Should class `2` dark-area pixels always be rejected, or configurable per analysis type?
3. Should class `7` low-probability cloud/unclassified always be rejected?
4. Should download require a candidate returned by inspection, or allow direct scene ID download?
5. Should quality metadata be required before download?
6. What naming convention should be used for `aoi_id` if the caller does not provide one?

Recommended defaults:

```txt
1. Start with a conservative max AOI size and make it configurable.
2. Reject class 2 by default.
3. Reject class 7 by default.
4. Allow direct scene ID download, but warn that inspection is recommended.
5. Do not require quality metadata, but include it when available.
6. Generate deterministic hash from normalized AOI geometry.
```

---

## 21. References

- sentinelhub-py documentation: https://sentinelhub-py.readthedocs.io/
- Sentinel-2 L2A Copernicus/Sentinel Hub documentation: https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/S2L2A.html
- Sentinel Hub Statistical API documentation: https://docs.sentinel-hub.com/api/latest/api/statistical/
- Sentinel Hub Catalog API documentation: https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Catalog.html
- sentinelhub-py Process API examples: https://sentinelhub-py.readthedocs.io/en/latest/examples/process_request.html
- Copernicus Sentinel-2 data collection overview: https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-2
