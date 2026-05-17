# Sentinel2 Ingest

Reusable Python package for inspecting and downloading Sentinel-2 imagery.

The package is designed as a standalone ingestion library. It is not tied to any specific API, database schema, or downstream application.

## Planned workflow

```txt
inspect Sentinel-2 candidate scenes
→ calculate AOI-level quality
→ generate thumbnails
→ select a scene
→ download selected raw bands as a multiband GeoTIFF
→ save metadata
```

## Project plan

See [docs/project-plan.md](docs/project-plan.md) for the full planning document, including scope, architecture, v1 boundaries, and implementation phases.
