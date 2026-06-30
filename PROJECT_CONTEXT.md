# Sentinel2 Ingest — Project Context

This document is the working product and engineering context for Sentinel2 Ingest. It keeps future tickets, implementation plans, and ownership-training exercises aligned with the actual roadmap instead of drifting into unrelated remote-sensing work.

## Product goal

Sentinel2 Ingest is a standalone Python package for inspecting and downloading Sentinel-2 L2A imagery.

The package should let a caller:

- inspect candidate scenes for one GeoJSON Polygon AOI and date range,
- estimate AOI-level usability from provider mask data,
- rank candidates using explicit local rules,
- generate thumbnails,
- select a scene,
- download selected raw bands as a multiband GeoTIFF,
- save provider-independent metadata.

The package must remain reusable from notebooks, scripts, CLIs, batch jobs, APIs, and other applications. It must not become coupled to GeoInsight or any other consuming application.

## Portfolio and training goal

The repository is not only a downloader implementation. It is also an ownership-training project.

Meaningful work should demonstrate:

- clarifying the real problem before coding,
- inspecting the current repository rather than assuming its structure,
- choosing the smallest useful implementation,
- making provider and domain boundaries explicit,
- identifying failure modes and regressions,
- testing behavior rather than implementation details,
- communicating decisions and trade-offs in the pull request,
- keeping scope controlled.

The implementer owns the solution. Guidance should normally challenge the plan, expose risks, and review the result rather than provide a complete implementation before the implementer has reasoned through the task.

## Target users

Primary users are technical callers that need a reusable Sentinel-2 ingestion component, including:

- Python scripts and notebooks,
- batch-processing jobs,
- geospatial APIs and services,
- future CLI consumers,
- downstream applications such as GeoInsight.

Public models and errors must remain understandable without requiring callers to know Sentinel Hub response structures.

## Current scope

The package currently includes:

- `src/` package layout and uv workflow,
- Pydantic request and result models,
- single-Polygon AOI validation,
- provider-independent scene models,
- `SceneProvider` protocol,
- deterministic fake provider,
- public inspection orchestration,
- local quality classification,
- candidate ranking and selection,
- Sentinel-2 L2A band constants and validation,
- band normalization,
- provider configuration and environment loading,
- a Sentinel Hub provider skeleton without real API calls,
- Ruff, pytest, and pull-request CI.

## Current milestone

Milestone 5 — Provider configuration.

Completed:

- M5-01: provider config model,
- M5-02: environment loading,
- M5-03: `.env.example`,
- M5-04: `SentinelHubProvider` skeleton.

Current:

- M5-05: package-specific provider error types.

The next milestone introduces the Sentinel Hub dependency and real candidate search. M5 must not pull that work forward.

## Near-term roadmap

1. Finish package-specific provider setup/configuration errors.
2. Add the Sentinel Hub runtime dependency deliberately.
3. Implement Sentinel-2 L2A Catalog candidate search.
4. Map provider results into provider-independent `CandidateScene` objects.
5. Add mocked provider tests before any credential-dependent integration path.
6. Add AOI-level quality through mask/statistical data in a later milestone.

## Non-goals for the current phase

Unless explicitly promoted into the roadmap, do not add:

- real Catalog search during M5,
- Statistical API calls,
- raster downloads or GeoTIFF writing,
- thumbnail generation,
- Rasterio or GeoPandas,
- STAC fallback providers,
- database writes,
- API server code,
- application-specific IDs or models,
- async job infrastructure,
- derived indices such as NDVI or NDWI,
- large-area tiling, mosaicking, or temporal compositing.

## Core boundaries

### Public package boundary

The public client and public models must expose provider-independent behavior. Provider SDK objects and raw response shapes must not leak into the public contract.

### Provider boundary

Provider-specific configuration, authentication, request construction, and response mapping belong under `providers/` or clearly provider-specific modules.

### Domain boundary

Models, ranking, selection, and quality decisions should remain pure where possible and must not import provider SDKs, Rasterio, databases, or application-specific code.

### Error boundary

Errors should communicate a meaningful caller action. Do not add an exception class only because a low-level failure exists. Add one when callers need to distinguish the failure or when it protects a package boundary.

### Testing boundary

Normal tests must not require credentials or network access. Real-provider behavior should be covered with mocked responses; optional integration checks must be explicitly gated.

## Core workflows

### 1. Candidate inspection

A caller supplies an AOI, date range, and thresholds. The package validates input, asks a provider for candidate scenes, applies local quality/ranking rules, and returns provider-independent results.

Ownership focus:

- distinguish validation from provider failure,
- distinguish no candidates from unusable candidates,
- avoid provider-specific leakage,
- test ordering and decision rules explicitly.

### 2. Provider configuration

A caller supplies or loads provider configuration and constructs a provider.

Ownership focus:

- keep secrets out of source control,
- distinguish invalid local configuration from remote provider rejection,
- keep configuration testable without mutating real environment state,
- avoid adding provider SDK dependencies before they are needed.

### 3. Future candidate search

The Sentinel Hub provider will query Sentinel-2 L2A candidate scenes and map responses into domain models.

Ownership focus:

- verify current official provider documentation,
- keep query assumptions explicit,
- map external data at the provider boundary,
- use scene cloud coverage only as a coarse pre-filter,
- test with mocked provider responses.

### 4. Future raster download

A selected scene and band request will produce raster files and metadata.

Ownership focus:

- make resolution and resampling behavior explicit,
- preserve band order and metadata,
- separate provider retrieval from raster writing,
- keep storage decisions outside consuming applications.

## Task acceptance rules

A task should be accepted only when it is traceable to at least one of:

- the product goal,
- the current milestone,
- a core workflow,
- a known architecture or correctness risk,
- an explicit scope-control exercise.

Every meaningful ticket should contain:

- goal,
- why the work matters now,
- problem to solve,
- scope,
- out-of-scope boundaries,
- ownership decisions to make before coding,
- affected areas,
- verification approach,
- definition of done,
- expected PR communication.

A ticket should describe the problem and constraints, not prescribe the full implementation unless a decision is already fixed by architecture or compatibility requirements.

## Ownership training rules

Before coding, answer:

1. What is the actual problem?
2. What is the smallest useful change?
3. Which layer owns the behavior?
4. What could break or become ambiguous?
5. How will the tests prove the intended behavior?
6. What remains deliberately out of scope?

Working discipline:

- inspect current files and tests before proposing changes,
- separate facts, assumptions, risks, and decisions,
- make low-risk reversible decisions without blocking,
- ask for alignment only for scope, architecture, public API, data correctness, provider behavior, security, release risk, or future roadmap impact,
- avoid dependency additions unless the task requires them,
- avoid abstractions that have only one speculative use,
- keep PRs small enough to review and explain.

## Quality bar

A change is not complete only because the code runs.

Expected quality:

- behavior and ownership boundaries are explicit,
- tests cover meaningful success and failure paths,
- public exports are deliberate,
- errors are useful to callers,
- no credentials or network access are required by normal tests,
- documentation changes match actual behavior,
- unnecessary dependencies and abstractions are avoided,
- the implementation can be explained clearly in an interview.

## Definition of done

A task is done when:

- the smallest useful behavior is implemented,
- relevant tests and Ruff checks pass,
- public contract changes are documented when relevant,
- edge cases are handled or recorded as limitations,
- no out-of-scope provider/raster work leaked into the change,
- the PR explains what was found, what was decided, what changed, and what remains next,
- follow-up work is separated into another ticket.

## Alignment triggers

Require explicit alignment before implementation when a change:

- changes a public model, export, or exception contract,
- changes provider protocol semantics,
- introduces a new external dependency,
- changes credential/configuration behavior,
- changes candidate ranking or quality meaning,
- affects raster resolution, resampling, or output semantics,
- expands beyond the current milestone,
- introduces network-dependent normal tests,
- couples the package to a consuming application.

## Operating principle

Keep Sentinel2 Ingest small, reusable, explicit, and testable.

Prefer one explainable task that strengthens the real ingestion workflow over a larger implementation that hides decisions or weakens package boundaries.
