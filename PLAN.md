# Sentinel2 Ingest Project Plan

## Product idea

**Sentinel2 Ingest** — a standalone Python package for inspecting and downloading Sentinel-2 imagery.

The package lets a caller inspect Sentinel-2 L2A candidate scenes for a single GeoJSON Polygon AOI and date range, estimate whether each candidate has enough usable AOI pixels, generate thumbnails, choose a scene, and download selected raw bands as one multiband GeoTIFF.

This is intentionally a **generic ingestion library**, not a GeoInsight-specific module and not a full remote-sensing analysis platform.

## Portfolio goal

Build a realistic geospatial Python package that demonstrates:

- Python package design with `src/` layout
- uv-based project workflow
- Pydantic request/result models
- Shapely-based GeoJSON AOI validation
- Provider abstraction and dependency injection
- Test-first development with a fake provider
- Sentinel Hub / Copernicus Data Space integration
- AOI-level quality inspection using SCL/dataMask
- Raw raster band download as GeoTIFF
- Clean CLI design
- CI with GitHub Actions
- Clear documentation and implementation milestones
- Portfolio-grade engineering discipline without overengineering

## Core stack decision

Use a small Python package first. Do **not** build an API service in this repository.

Reason: this project should be reusable in notebooks, scripts, CLIs, batch jobs, FastAPI services, and GeoInsight API. Adding an API server now would couple the package to one deployment style before the core ingestion workflow is stable.

Current/proposed stack:

- Package manager: uv
- Language: Python 3.11+
- Models/validation: Pydantic
- Geometry validation: Shapely
- Provider API: Sentinel Hub / Copernicus Data Space through `sentinelhub-py`
- Raster output: Rasterio later
- Geospatial tabular support: GeoPandas later if needed
- CLI: Typer or Click later
- Tests: pytest
- Linting: Ruff
- CI: GitHub Actions

## Current project status

Foundation work and local inspection decision logic are complete.

Completed:

| Area | Status | Notes |
| ---- | ------ | ----- |
| Package bootstrap | Done | uv package, `src/` layout, pytest, Ruff |
| CI | Done | GitHub Actions runs uv sync, Ruff, pytest |
| README | Done | Basic purpose and workflow documented |
| Core models | Done | Inspection/download requests and results |
| AOI validation | Done | V1 accepts only valid GeoJSON Polygon |
| Provider boundary | Done | `SceneProvider` protocol exists |
| Fake provider | Done | `FakeSceneProvider` supports testable inspect flow |
| Public inspect flow | Done | `Sentinel2IngestClient.inspect()` exists |
| Quality classification | Done | Pure `classify_quality()` returns status and reasons |
| Fake provider quality | Done | Fake candidates use the shared quality classifier |
| Candidate ranking | Done | Candidates are ranked by status, quality metrics, and date |
| Best-candidate helper | Done | Explicit helper selects the best usable or allowed risky candidate |
| Quality decision docs | Done | Thresholds, statuses, ranking, and selection are documented |
| Band support and validation | Done | Supported bands, defaults, validation, normalization, and resolution behavior are documented |

Current implemented public usage:

```python
from sentinel2_ingest import FakeSceneProvider, Sentinel2IngestClient

client = Sentinel2IngestClient(provider=FakeSceneProvider())

result = client.inspect(
    aoi=aoi_polygon_geojson,
    date_range=("2025-06-01", "2025-06-30"),
)
```

Current important files:

```txt
docs/quality-decisions.md
src/sentinel2_ingest/client.py
src/sentinel2_ingest/models/inputs.py
src/sentinel2_ingest/models/quality.py
src/sentinel2_ingest/models/results.py
src/sentinel2_ingest/models/scenes.py
src/sentinel2_ingest/aoi/validation.py
src/sentinel2_ingest/providers/base.py
src/sentinel2_ingest/providers/fake.py
src/sentinel2_ingest/inspection/quality.py
src/sentinel2_ingest/inspection/ranking.py
src/sentinel2_ingest/inspection/selection.py
tests/test_models.py
tests/test_aoi_validation.py
tests/test_client_inspection.py
tests/test_quality.py
tests/test_candidate_ranking.py
tests/test_candidate_selection.py
.github/workflows/ci.yml
```

## Architecture standards

The project should be built as a portfolio-quality package, not just a working downloader script.

### Layering model

Use a package structure with clear boundaries:

- `client.py`: public orchestration API.
- `models/`: provider-independent request/result/domain models.
- `aoi/`: GeoJSON AOI validation and geometry helpers.
- `providers/`: provider interfaces and concrete provider implementations.
- `inspection/`: quality classification, candidate ranking, thumbnails.
- `download/`: selected-scene download orchestration and raster writing.
- `storage/`: path generation and metadata JSON writing.
- `cli.py`: command-line interface later.
- `tests/`: unit tests, fake provider tests, mocked provider tests.

### Dependency rules

- Public client code may depend on models and provider protocols.
- Domain models must not import Sentinel Hub, Rasterio, GeoPandas, or application-specific code.
- Provider-specific code stays inside `providers/`.
- Sentinel Hub response shapes must be mapped into provider-independent models.
- AOI validation happens before provider calls.
- Quality classification should be pure and testable without provider credentials.
- Candidate ranking should be pure and testable without provider credentials.
- Download code should not decide business/application ownership.
- No database writes in the core package.
- No GeoInsight-specific imports, model names, IDs, or assumptions.

### API contract rule

Public inputs and outputs should use explicit models or stable typed structures:

- `InspectionRequest`
- `InspectionResult`
- `CandidateScene`
- `AoiQualityMetrics`
- `DownloadRequest`
- `DownloadResult`

Provider metadata may be preserved in `source_metadata`, but public behavior must not require callers to understand raw Sentinel Hub response structures.

### Error-handling rule

Use package-specific exceptions for meaningful boundaries:

- `InvalidAoiError`
- `InvalidBandError` later
- `ProviderAuthenticationError` later
- `ProviderRequestError` later
- `NoCandidatesFoundError` later
- `NoUsableCandidatesFoundError` later
- `DownloadFailedError` later

Do not collapse these two states:

- no scenes found for AOI/date/filter
- scenes exist, but AOI quality is not good enough

They require different caller behavior.

### Provider rule

Scene-level cloud coverage is only a coarse pre-filter.

A candidate must not be considered truly usable until AOI-level quality has been calculated from SCL/dataMask or equivalent mask data.

### Storage rule

V1 stores rasters as files, not database rows.

Use:

```txt
GeoTIFF files + JSON metadata
```

Reason:

- Raster files can become large.
- Files are easier to inspect and reuse.
- Consuming applications can decide whether/how to store metadata in their own database.
- Database insertion would couple this package to one application too early.

### Best-practice rule

Before starting each provider or raster-processing milestone, check official/current documentation and document any important API choice briefly.

Prefer boring, testable abstractions over impressive architecture. Add abstraction only when it protects package independence, provider boundaries, or testability.

## Domain scope

### V1 input scope

V1 supports:

- GeoJSON `Polygon` AOI only
- date range
- Sentinel-2 L2A collection
- raw band list
- scene-level cloud pre-filter
- AOI-level usable-pixel thresholds

V1 does not support:

- `MultiPolygon`
- `Feature`
- `FeatureCollection`
- `GeometryCollection`
- `Point`
- `LineString`
- large-area tiling
- mosaicking
- temporal compositing

### V1 imagery scope

V1 should support raw Sentinel-2 L2A bands:

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

Default band request:

```python
DEFAULT_BANDS = ["B02", "B03", "B04", "B08"]
```

Default thumbnail bands:

```python
THUMBNAIL_BANDS = ["B04", "B03", "B02"]
```

### AOI-level quality scope

V1 inspection must estimate quality for the actual AOI, not only the scene/tile.

Use:

- `SCL`
- `dataMask`

Default usable SCL classes:

```python
USABLE_SCL_CLASSES = {
    4,  # vegetation
    5,  # bare soils
    6,  # water
}
```

Default rejected SCL classes:

```python
REJECTED_SCL_CLASSES = {
    0,   # no data
    1,   # saturated / defective
    2,   # dark area pixels
    3,   # cloud shadows
    7,   # unclassified / low probability cloud
    8,   # medium probability cloud
    9,   # high probability cloud
    10,  # cirrus
    11,  # snow / ice
}
```

Default thresholds:

```python
min_usable_pixel_ratio = 0.80
max_cloud_pixel_ratio = 0.10
max_shadow_pixel_ratio = 0.10
max_no_data_ratio = 0.05
```

### Non-goals for v1

- No database insertion
- No API server
- No frontend UI
- No user accounts
- No GeoInsight-specific integration
- No NDVI/NDWI/NBR
- No cloud gap filling
- No custom ML cloud masking
- No mosaicking
- No large-area tiling
- No async job queue
- No cloud storage abstraction
- No STAC fallback provider in the first pass

## Branch and development strategy

- `main`: stable branch.
- `feat/<ticket-id>-short-name`: feature branches.
- `chore/<short-name>`: maintenance/tooling branches.
- `docs/<short-name>`: documentation-only branches.
- Pull requests are required for meaningful changes.
- CI runs on every PR.
- Keep PRs focused and small.
- Avoid mixing docs, provider logic, and raster download behavior in one PR.

## Milestones and tickets

### Milestone 0 — Project foundation

Status: mostly complete.

| ID | Ticket | Short description | Status |
| --- | --- | --- | --- |
| M0-01 | Bootstrap Python package | Create uv package with `src/` layout, pytest, Ruff, README. | Done |
| M0-02 | Add project plan | Add first planning document. | Done |
| M0-03 | Clean package metadata | Relax Python target, remove bootstrap `hello()`, clean exports. | Done |
| M0-04 | Add CI workflow | Run uv sync, Ruff, and pytest on PRs. | Done |
| M0-05 | Move plan to root | Replace `docs/project-plan.md` with root `PLAN.md`. | Current |

### Milestone 1 — Core models and AOI validation

Status: mostly complete.

| ID | Ticket | Short description | Status |
| --- | --- | --- | --- |
| M1-01 | Add core domain models | Add inspection/download requests, candidate scene, quality metrics, results. | Done |
| M1-02 | Add date/threshold validation | Validate date range and numeric thresholds. | Done |
| M1-03 | Add single Polygon AOI validation | Accept only valid GeoJSON Polygon AOIs. | Done |
| M1-04 | Add package exceptions | Add base package exception and `InvalidAoiError`. | Done |
| M1-05 | Add max AOI area validation | Reject AOIs that are too large for v1. | Planned |

### Milestone 2 — Provider abstraction and fake inspection

Status: mostly complete.

| ID | Ticket | Short description | Status |
| --- | --- | --- | --- |
| M2-01 | Add provider protocol | Define `SceneProvider.inspect()`. | Done |
| M2-02 | Add fake provider | Return deterministic fake candidate scenes. | Done |
| M2-03 | Add public inspect flow | Add `Sentinel2IngestClient.inspect()`. | Done |
| M2-04 | Ensure inspect result serialization | Verify `InspectionResult.model_dump(mode="json")`. | Done |

### Milestone 3 — Local inspection decision logic

Status: complete.

| ID | Ticket | Short description | Status |
| --- | --- | --- | --- |
| M3-01 | Add quality classification service | Add pure `classify_quality()` returning status and reasons. | Done |
| M3-02 | Use classifier in fake provider | Stop hardcoding fake quality statuses. | Done |
| M3-03 | Add candidate ranking | Sort candidates by status, usable ratio, cloud, shadow, date. | Done |
| M3-04 | Add best-candidate helper | Add helper for choosing the first ranked usable/risky scene. | Done |
| M3-05 | Add quality docs | Document threshold behavior and status meanings. | Done |

### Milestone 4 — Band support and request validation

Status: complete.

| ID | Ticket | Short description | Status |
| --- | --- | --- | --- |
| M4-01 | Add Sentinel-2 L2A band constants | Define supported raw bands, defaults, thumbnail bands. | Done |
| M4-02 | Validate download bands | Reject unsupported bands and duplicates. | Done |
| M4-03 | Normalize band names | Normalize lowercase user input consistently. | Done |
| M4-04 | Document resolution behavior | Explain native 10/20/60 m bands and resampling implication. | Done |

### Milestone 5 — Provider configuration

| ID | Ticket | Short description | Status |
| --- | --- | --- | --- |
| M5-01 | Add provider config model | Add generic config module and Sentinel Hub config model. | Planned / existing TK11 |
| M5-02 | Load config from environment | Load Sentinel Hub credentials and endpoints from env vars. | Planned / existing TK11 |
| M5-03 | Add `.env.example` | Document expected Sentinel Hub variables without secrets. | Planned |
| M5-04 | Add SentinelHubProvider skeleton | Add provider class without real API calls. | Planned / existing TK11 |
| M5-05 | Add provider auth errors | Add package-specific auth/config errors. | Planned |

### Milestone 6 — Sentinel Hub candidate search

| ID | Ticket | Short description | Status |
| --- | --- | --- | --- |
| M6-01 | Add Sentinel Hub dependency | Add `sentinelhub` runtime dependency. | Planned / existing TK12 |
| M6-02 | Implement Catalog search | Search Sentinel-2 L2A by AOI/date/cloud pre-filter. | Planned / existing TK12 |
| M6-03 | Map provider results | Convert Sentinel Hub results into `CandidateScene`. | Planned / existing TK12 |
| M6-04 | Preserve source metadata | Store useful raw metadata in `source_metadata`. | Planned / existing TK12 |
| M6-05 | Add mocked provider tests | Test mapping without real credentials. | Planned / existing TK12 |
| M6-06 | Add optional integration notes | Document env-gated real provider test path. | Planned |

Boundary: scene-level cloud coverage is only a coarse pre-filter. No AOI-level quality in this milestone.

### Milestone 7 — AOI-level quality via Statistical API

| ID | Ticket | Short description | Status |
| --- | --- | --- | --- |
| M7-01 | Add SCL/dataMask evalscript | Request class/mask data for AOI quality. | Planned |
| M7-02 | Call Statistical API | Calculate AOI-level class counts without downloading imagery. | Planned |
| M7-03 | Convert counts to metrics | Build `AoiQualityMetrics` from SCL/dataMask output. | Planned |
| M7-04 | Apply quality classifier | Populate status and reasons for real candidates. | Planned |
| M7-05 | Rank real candidates | Apply ranking after AOI quality is available. | Planned |
| M7-06 | Add no-usable-candidates behavior | Distinguish no candidates from no usable candidates. | Planned |

### Milestone 8 — Thumbnail generation

| ID | Ticket | Short description | Status |
| --- | --- | --- | --- |
| M8-01 | Generate RGB thumbnail | Create B04/B03/B02 preview for each candidate. | Planned |
| M8-02 | Save thumbnail files | Store thumbnails in inspection output folder. | Planned |
| M8-03 | Link thumbnail path | Add thumbnail path to `CandidateScene`. | Planned |
| M8-04 | Make thumbnail failures non-fatal | Inspection can still return quality metrics if thumbnails fail. | Planned |

### Milestone 9 — Selected-scene download

| ID | Ticket | Short description | Status |
| --- | --- | --- | --- |
| M9-01 | Add download provider method | Extend provider boundary for selected-scene band download. | Planned |
| M9-02 | Implement Process API download | Request selected raw bands for AOI/scene. | Planned |
| M9-03 | Write multiband GeoTIFF | Save one GeoTIFF with requested bands. | Planned |
| M9-04 | Save download metadata | Write scene, bands, CRS, bounds, resolution, quality metadata. | Planned |
| M9-05 | Add raster output tests | Test metadata/path behavior with mocked provider or fixtures. | Planned |

### Milestone 10 — Storage, examples, and CLI

| ID | Ticket | Short description | Status |
| --- | --- | --- | --- |
| M10-01 | Add storage path helpers | Generate deterministic inspection/download paths. | Planned |
| M10-02 | Add metadata writers | Save request, candidates, and download metadata JSON. | Planned |
| M10-03 | Add inspect CLI | Implement `sentinel2-ingest inspect`. | Planned |
| M10-04 | Add download CLI | Implement `sentinel2-ingest download`. | Planned |
| M10-05 | Add example AOI | Add small valid Polygon example. | Planned |
| M10-06 | Add Python examples | Add inspect and download example scripts. | Planned |

### Milestone 11 — Documentation and integration contract

| ID | Ticket | Short description | Status |
| --- | --- | --- | --- |
| M11-01 | Add API contract docs | Document public Python API and serializable outputs. | Planned |
| M11-02 | Add provider notes | Document Sentinel Hub/CDSE assumptions and credentials. | Planned |
| M11-03 | Add error handling docs | Document expected package exceptions and caller behavior. | Planned |
| M11-04 | Add GeoInsight adapter notes | Show how a consuming app should map package results externally. | Planned |
| M11-05 | Add README quickstart | Provide install, inspect, and download examples. | Planned |

### Milestone 12 — Hardening and portfolio polish

| ID | Ticket | Short description | Status |
| --- | --- | --- | --- |
| M12-01 | Add timeout/retry config | Handle transient provider failures safely. | Planned |
| M12-02 | Add max candidate limit | Prevent huge inspection result sets. | Planned |
| M12-03 | Add max AOI guard | Protect v1 from large-area requests. | Planned |
| M12-04 | Add integration tests | Env-gated Sentinel Hub tests only. | Planned |
| M12-05 | Add architecture notes | Document provider boundary and AOI quality decisions. | Planned |
| M12-06 | Add portfolio summary | Write case-study style README/notes. | Planned |

### Milestone 13 — Later extensions

These are not v1 work.

| ID | Ticket | Short description | Status |
| --- | --- | --- | --- |
| M13-01 | Add STAC provider spike | Evaluate CDSE STAC or Planetary Computer fallback. | Later |
| M13-02 | Add COG output | Write Cloud Optimized GeoTIFFs. | Later |
| M13-03 | Add derived indices | NDVI/NDWI/NBR after raw download is stable. | Later |
| M13-04 | Add MultiPolygon support | Support more complex AOIs after v1 works. | Later |
| M13-05 | Add batch jobs | Multiple AOIs/date ranges. | Later |
| M13-06 | Add cloud storage output | S3/GCS/Azure output targets. | Later |

## Recommended implementation order

1. M4-01/M4-02 Add band constants and validation.
2. M5-01/M5-02 Add provider configuration.
3. M6-02 Implement Sentinel Hub candidate search.
4. M7 AOI-level quality via Statistical API.
5. M8 thumbnail generation.
6. M9 selected-scene download.
7. M10 storage helpers, examples, and CLI.
8. M11 integration documentation.
9. M12 hardening and portfolio polish.
10. M13 later extensions only after v1 is stable.

## Architecture guardrails

- Keep the package independent from GeoInsight and every other consuming app.
- Keep provider-specific code behind provider classes.
- Keep quality classification and ranking pure and testable.
- Do not treat scene-level cloud coverage as final quality.
- Do not add downloads before candidate inspection and AOI quality are reliable.
- Do not add database writes to this package.
- Do not add a web API to this repository.
- Do not support MultiPolygon until the single-Polygon path is stable.
- Do not add NDVI or derived indices before raw band download works.
- Keep tickets small enough for one focused branch/PR.
- If a feature does not improve package correctness, provider independence, testability, or portfolio value, defer it.

## First useful next step

Start with **M4-01/M4-02 Add Sentinel-2 L2A band constants and download band validation**.

Do not start Sentinel Hub candidate search until band validation and provider configuration are stable. External provider complexity should not drive the internal domain design.