# Sentinel2 Ingest — Project Plan

_Last updated: 2026-05-20_

## 1. Project Summary

### Project name

Repository name:

```txt
sentinel2-ingest
```

Python package name:

```txt
sentinel2_ingest
```

Planned CLI name:

```txt
sentinel2-ingest
```

This package must remain independent and reusable outside any single consuming application. GeoInsight API is one intended consumer, but this package must not depend on GeoInsight models, database schema, project structure, API routes, or business logic.

### Goal

Build a standalone Python package that can inspect and download Sentinel-2 imagery for any geospatial workflow.

The package follows an inspect-then-download workflow:

```txt
inspect Sentinel-2 candidate scenes
→ calculate AOI-level usability/quality
→ generate thumbnails
→ select a scene
→ download selected raw bands as one multiband GeoTIFF
→ save metadata
```

The package is not a full remote-sensing analysis platform.

---

## 2. Current Status

Completed foundation work:

```txt
TK1  — Bootstrap Python package
TK2  — Add project plan documentation
TK3  — Add core domain models
TK4  — Add single Polygon AOI validation
TK5  — Add fake provider and inspect flow
TK6  — Clean up bootstrap leftovers and package metadata
CI   — Add CI pipeline for tests and linting
```

Current foundation:

```txt
Sentinel2IngestClient.inspect() exists
SceneProvider protocol exists
FakeSceneProvider exists for tests and early development
InspectionRequest, CandidateScene, AoiQualityMetrics, DownloadRequest, DownloadResult exist
AOI validation supports only valid GeoJSON Polygon input
Inspection results are serializable
CI runs uv sync, Ruff, and pytest
```

Open/next planned tickets:

```txt
TK8  — Add quality classification service
TK9  — Add candidate ranking
TK10 — Add band constants and validation
TK11 — Add provider configuration skeleton
TK12 — Add Sentinel Hub candidate search
```

---

## 3. Independence Boundary

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

Recommended integration boundary:

```txt
sentinel2-ingest package
→ generic inspect/download result
→ consuming application maps result into its own API/database/domain models
```

Design rules:

```txt
1. No imports from a consuming application.
2. No application-specific model names.
3. No database writes in the core package.
4. No FastAPI/Django/Flask dependency in the core package.
5. No assumption about where files are stored.
6. No assumption about user/project ownership.
7. No business-specific analysis logic.
8. No hardcoded output paths tied to one repository.
9. Public return values must be serializable and generic.
10. Provider-specific details must stay behind provider abstractions.
```

---

## 4. Core V1 Decisions

### D1 — V1 supports Sentinel-2 L2A first

Use Sentinel-2 Level-2A as the first supported data collection.

Reason:

- It provides atmospherically corrected surface reflectance.
- It includes the `SCL` scene classification band.
- `SCL` is needed for AOI-level usable-pixel estimation.

Collection identifier:

```txt
sentinel-2-l2a
```

### D2 — V1 uses Sentinel Hub / Copernicus Data Space first

Use `sentinelhub-py` as the first real provider integration.

Provider-specific details must stay behind provider abstractions.

Initial real provider:

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

### D3 — V1 is inspect-then-download

Do not design this as a direct downloader only.

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

Reason: this keeps geometry validation, pixel statistics, thumbnail generation, and output clipping simple.

### D5 — Raw raster data is stored as files

Do not store raster pixels in PostgreSQL/PostGIS in v1.

Use:

```txt
GeoTIFF files + JSON metadata
```

Reason:

- Raster files can become large.
- File storage is simpler for v1.
- Consuming applications can store metadata in their own database if needed.
- Database insertion would couple this package to a specific application too early.

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

## 5. External Provider Assumptions

These assumptions should be rechecked if provider behavior changes.

1. `sentinelhub-py` is the first intended Python client for Sentinel Hub services.
2. Sentinel-2 L2A is accessed with collection identifier `sentinel-2-l2a`.
3. Sentinel-2 L2A exposes optical bands, `SCL`, `CLD`, `SNW`, and `dataMask`.
4. `SCL` includes classes for no data, defective pixels, dark areas, cloud shadows, vegetation, bare soils, water, low/medium/high probability clouds, cirrus, and snow/ice.
5. Sentinel Hub scene-level cloud coverage is a coarse pre-filter and may not reflect the actual AOI.
6. Sentinel Hub Statistical API can calculate statistics for an AOI/time period without downloading full imagery.
7. Sentinel Hub Process API can return raw band data for download.

---

## 6. Current / Planned Architecture

```txt
sentinel2-ingest
│
├── Public API
│   ├── Sentinel2IngestClient.inspect()          # implemented
│   ├── Sentinel2IngestClient.download()         # planned
│   └── Sentinel2IngestClient.from_env()         # planned after config
│
├── Domain models
│   ├── InspectionRequest                        # implemented
│   ├── CandidateScene                           # implemented
│   ├── AoiQualityMetrics                        # implemented
│   ├── DownloadRequest                          # implemented
│   └── DownloadResult                           # implemented
│
├── Provider layer
│   ├── SceneProvider                            # implemented
│   ├── FakeSceneProvider                        # implemented
│   └── SentinelHubProvider                      # planned
│
├── AOI validation
│   └── single Polygon validation                # implemented
│
├── Quality inspection
│   ├── quality classification                   # next
│   ├── candidate ranking                        # next
│   ├── SCL statistics                           # planned
│   └── dataMask statistics                      # planned
│
├── Band support
│   └── Sentinel-2 L2A raw band validation       # planned
│
├── Thumbnail generation
│   └── RGB preview PNG                          # planned
│
├── Download
│   └── selected raw bands → multiband GeoTIFF   # planned
│
└── Storage
    ├── inspection metadata JSON                 # planned
    ├── thumbnails                               # planned
    ├── downloaded GeoTIFF                       # planned
    └── download metadata JSON                   # planned
```

---

## 7. Repository Structure

Current/planned structure:

```txt
sentinel2-ingest/
  README.md
  pyproject.toml
  uv.lock
  .python-version
  .github/
    workflows/
      ci.yml

  docs/
    project-plan.md
    provider-notes.md        # planned
    api-contract.md          # planned

  examples/                  # planned
    aoi.geojson
    inspect_example.py
    download_example.py

  src/
    sentinel2_ingest/
      __init__.py
      client.py
      config.py              # planned
      exceptions.py

      models/
        __init__.py
        inputs.py
        scenes.py
        quality.py
        results.py

      aoi/
        __init__.py
        validation.py

      providers/
        __init__.py
        base.py
        fake.py
        sentinel_hub.py       # planned
        evalscripts.py        # planned

      inspection/             # planned
        __init__.py
        quality.py
        ranking.py
        thumbnails.py

      download/               # planned
        __init__.py
        service.py
        raster_writer.py

      storage/                # planned
        __init__.py
        paths.py
        metadata_writer.py

      cli.py                  # planned

  tests/
    test_aoi_validation.py
    test_client_inspection.py
    test_models.py
    test_config.py            # planned
    test_quality.py           # planned
    test_candidate_ranking.py # planned
    test_band_validation.py   # planned
```

Important naming decisions:

```txt
models/inputs.py, not models/requests.py
SceneProvider, not BaseSentinelProvider
source/source_metadata, not provider/provider_metadata
```

---

## 8. Public API Design

### 8.1 Current development/test usage

The current client is dependency-injected with a provider:

```python
from sentinel2_ingest import FakeSceneProvider, Sentinel2IngestClient

client = Sentinel2IngestClient(provider=FakeSceneProvider())

result = client.inspect(
    aoi=aoi_polygon_geojson,
    date_range=("2025-06-01", "2025-06-30"),
)
```

This is intentional. It keeps the client testable and provider-independent.

### 8.2 Planned real-provider usage

After provider config exists:

```python
from sentinel2_ingest import Sentinel2IngestClient
from sentinel2_ingest.providers import SentinelHubProvider

provider = SentinelHubProvider.from_env()
client = Sentinel2IngestClient(provider=provider)
```

A convenience constructor may be added later:

```python
client = Sentinel2IngestClient.from_env()
```

Do not document `from_env()` as implemented until it exists.

### 8.3 Inspect candidates

```python
result = client.inspect(
    aoi=aoi_polygon_geojson,
    date_range=("2025-06-01", "2025-06-30"),
    max_scene_cloud_coverage=60,
    min_usable_pixel_ratio=0.80,
    thumbnail=True,
)

candidates = result.candidates
```

### 8.4 Select candidate

Manual selection:

```python
selected = candidates[0]
```

Automatic selection is planned after ranking:

```python
selected = client.select_best_candidate(candidates)
```

### 8.5 Download selected scene

Planned:

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

## 9. Data Models

Use Pydantic models for request/response validation.

### 9.1 InspectionRequest

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
    output_dir: Path | None = None
```

Validation rules:

```txt
date_from <= date_to
aoi.type == "Polygon"
aoi coordinates are valid
aoi is not empty
aoi is not self-intersecting
thresholds are between 0 and 1, except scene cloud coverage which is 0–100
```

Planned validation:

```txt
aoi area is below configured max area
```

### 9.2 CandidateScene

```python
class CandidateScene(BaseModel):
    scene_id: str
    datetime: datetime
    collection: str
    source: str

    scene_cloud_coverage: float | None = None

    quality: AoiQualityMetrics | None = None
    quality_status: QualityStatus | None = None
    quality_reasons: list[str]

    thumbnail_path: Path | None = None
    source_metadata: dict = {}
```

### 9.3 AoiQualityMetrics

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

Ratios are computed from counts.

### 9.4 DownloadRequest

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
bands must not contain duplicates
```

Planned validation:

```txt
bands are valid Sentinel-2 L2A raw bands
resolution is supported
```

### 9.5 DownloadResult

```python
class DownloadResult(BaseModel):
    scene_id: str
    collection: str
    source: str
    bands: list[str]
    file_path: Path
    metadata_path: Path | None
    crs: str | None
    resolution: int
    width: int | None
    height: int | None
    bounds: tuple[float, float, float, float] | None
```

---

## 10. Provider Layer

### 10.1 Current provider protocol

```python
class SceneProvider(Protocol):
    def inspect(self, request: InspectionRequest) -> list[CandidateScene]:
        ...
```

This is intentionally narrow for now.

### 10.2 Current fake provider

`FakeSceneProvider` exists for tests and early development.

Purpose:

```txt
make inspect() testable without external credentials
stabilize the public API before real provider integration
provide deterministic candidate scenes
```

### 10.3 Planned Sentinel Hub provider

`SentinelHubProvider` should be added after provider config.

First real capability:

```txt
search Sentinel-2 L2A candidate scenes by AOI/date/cloud pre-filter
```

Out of scope for first Sentinel Hub ticket:

```txt
AOI-level SCL/dataMask quality
thumbnails
downloads
```

---

## 11. AOI-Level Quality Inspection

### 11.1 Why this is required

Do not trust scene/tile-level cloud coverage as the final decision.

The inspection must answer:

```txt
For this specific AOI, how much of the area has usable pixels in this candidate scene?
```

### 11.2 Source bands for quality

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

### 11.3 SCL class grouping

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

```txt
Treat class 2 as non-usable by default.
Treat class 7 as non-usable by default because it is ambiguous.
Make these choices configurable later only if needed.
```

### 11.4 Default quality thresholds

```python
min_usable_pixel_ratio = 0.80
max_cloud_pixel_ratio = 0.10
max_shadow_pixel_ratio = 0.10
max_no_data_ratio = 0.05
```

### 11.5 Quality status

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

---

## 12. Candidate Ranking

Default ranking should be:

```txt
1. usable scenes first
2. highest usable_pixel_ratio
3. lowest cloud_pixel_ratio
4. lowest shadow_pixel_ratio
5. newest acquisition date
```

Do not auto-download in v1 unless the caller explicitly asks for automatic selection.

---

## 13. Band Support

### 13.1 Supported raw bands in v1

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

### 13.2 Default band request

```python
DEFAULT_BANDS = ["B02", "B03", "B04", "B08"]
```

### 13.3 Default thumbnail bands

```python
THUMBNAIL_BANDS = ["B04", "B03", "B02"]
```

### 13.4 Resolution handling

Default:

```python
resolution = 10
```

Important:

```txt
Some bands are native 10 m.
Some bands are native 20 m.
Some bands are native 60 m.
If mixed-resolution bands are requested, the provider will resample to the requested output resolution.
V1 should document this clearly.
Use nearest-neighbor resampling for masks/classes and appropriate defaults for optical bands.
```

---

## 14. Storage Layout

Planned inspection output:

```txt
data/
  inspections/
    <inspection_id>/
      request.json
      candidates.json
      thumbnails/
        <scene_id>.png
```

Planned download output:

```txt
data/
  downloads/
    <scene_id>/
      bands_B02_B03_B04_B08.tif
      metadata.json
```

Metadata should use generic names:

```json
{
  "scene_id": "...",
  "source": "sentinel_hub",
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

## 15. Phase Plan

### Phase 0 — Foundation setup

Status: mostly complete.

Includes:

```txt
repository setup
uv package setup
Ruff and pytest
README
project plan
CI workflow
```

### Phase 1 — Domain models and validation

Status: mostly complete.

Includes:

```txt
Pydantic request/result models
single Polygon AOI validation
date-range validation
basic duplicate band validation
```

Still planned:

```txt
max AOI area validation
Sentinel-2 L2A band validation
```

### Phase 2 — Provider abstraction

Status: partially complete.

Complete:

```txt
SceneProvider protocol
FakeSceneProvider
Sentinel2IngestClient.inspect()
```

Planned:

```txt
provider configuration skeleton
SentinelHubProvider skeleton
```

### Phase 3 — Local inspection logic

Planned next.

Includes:

```txt
quality classification service
candidate ranking
band constants and validation
```

Boundary:

```txt
No real API calls required.
No downloads.
```

### Phase 4 — Sentinel Hub candidate search

Planned after local inspection logic and provider config.

Includes:

```txt
SentinelHubProvider.inspect()
Catalog search
map provider results into CandidateScene
scene-level cloud coverage pre-filter
```

Boundary:

```txt
No AOI-level quality yet.
No thumbnails.
No downloads.
```

### Phase 5 — AOI quality with Statistical API

Planned.

Includes:

```txt
SCL/dataMask evalscript
Statistical API request
convert SCL histogram/class counts into AoiQualityMetrics
apply quality classification
rank candidates
```

Boundary:

```txt
No raw band download yet.
```

### Phase 6 — Thumbnail generation

Planned.

Includes:

```txt
RGB thumbnail from B04/B03/B02
thumbnail paths on CandidateScene
non-fatal thumbnail failures by default
```

Boundary:

```txt
Thumbnail is visual only, not quality source.
```

### Phase 7 — Download selected scene

Planned.

Includes:

```txt
selected scene ID
AOI
bands
resolution
multiband GeoTIFF
metadata JSON
```

Boundary:

```txt
No NDVI or derived indices.
No database insertion.
```

### Phase 8 — CLI

Planned.

Includes:

```txt
sentinel2-ingest inspect
sentinel2-ingest download
```

### Phase 9 — Generic integration contract

Planned.

Includes:

```txt
docs/api-contract.md
Python usage examples
returned metadata
error types
expected storage layout
```

### Phase 10 — Hardening

Planned.

Includes:

```txt
structured provider errors
retry/timeout config
max candidate limit
max AOI area guard
examples and integration tests
```

---

## 16. Implementation Order

Current recommended order:

```txt
1. TK13 — Update project plan after foundation phase
2. TK8  — Add quality classification service
3. TK9  — Add candidate ranking
4. TK10 — Add band constants and validation
5. TK11 — Add provider configuration skeleton
6. TK12 — Add Sentinel Hub candidate search
7. Add AOI-level quality inspection with Statistical API
8. Add thumbnail generation
9. Add selected-scene raw band download
10. Add CLI
11. Add docs/examples/integration contract
12. Add integration tests and hardening
```

Do not jump directly to Sentinel Hub candidate search before quality classification, ranking, and band validation unless there is a specific reason. The local domain logic should be stable before external API complexity enters the codebase.

---

## 17. Testing Strategy

### Unit tests

Focus on:

```txt
AOI validation
band validation
date validation
quality metric calculation
quality status classification
candidate ranking
metadata serialization
provider mapping with mocked responses
```

### CI

CI should run on push and pull requests:

```bash
uv sync --locked --all-extras --dev
uv run ruff check
uv run pytest
```

### Integration tests

Optional and gated behind environment variables:

```bash
RUN_SENTINELHUB_INTEGRATION_TESTS=1
```

Integration tests should not run by default in CI until credentials, costs, and rate limits are controlled.

### Fixture strategy

Use fake provider responses and mocked provider outputs for normal tests.

---

## 18. Error Handling

Validation errors should be raised before provider calls.

Examples:

```txt
AOI must be a GeoJSON Polygon. Received MultiPolygon.
Unsupported band: B10. Supported bands are: ...
date_from must be before or equal to date_to.
```

Provider-specific errors should be wrapped in package-specific exceptions.

Planned structured exceptions:

```txt
InvalidAoiError
InvalidBandError
ProviderAuthenticationError
ProviderRequestError
NoCandidatesFoundError
NoUsableCandidatesFoundError
DownloadFailedError
```

Do not merge these two states:

```txt
NoCandidatesFoundError
NoUsableCandidatesFoundError
```

Reason:

```txt
No candidates = no scenes found in date/filter range.
No usable candidates = scenes exist, but AOI quality is not good enough.
```

---

## 19. Non-Goals for V1

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

## 20. Integration Boundary

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
provider interaction
AOI validation for ingestion
candidate inspection
AOI quality metrics
thumbnail generation
raw band download
file + metadata output
generic Python/CLI API
```

Example consuming application flow:

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

Example GeoInsight-specific adapter boundary:

```txt
geoinsight_api/
  services/
    satellite_ingestion_service.py

satellite_ingestion_service.py
→ calls sentinel2_ingest
→ maps CandidateScene into GeoInsight DB model
→ maps DownloadResult into GeoInsight analysis/source records
```

GeoInsight-specific code should live outside this package.
