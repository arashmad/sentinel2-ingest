# Normalize WGS84 Bounding-Box AOIs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide `sentinel2_ingest.aoi.normalize_bbox` to validate WGS84
bounding boxes and return Shapely polygons.

**Architecture:** Put the single, stateless AOI conversion API in a focused
`aoi` module. The module owns numeric and geographic-bound validation before
constructing a Shapely rectangle. It uses the established `InvalidAOIError`
for all invalid caller inputs and remains module-scoped rather than being
re-exported by the package root.

**Tech Stack:** Python 3.11–3.13, Shapely 2, pytest, mypy, Ruff.

**Spec:** `docs/superpowers/specs/2026-09-12-normalize-wgs84-bbox-aoi-design.md`

## Global Constraints

- Public API: `sentinel2_ingest.aoi.normalize_bbox(west, south, east, north) -> Polygon`.
- Add Shapely as a runtime dependency; retain Python `>=3.11,<3.14` support.
- Inputs must be finite numeric WGS84 longitude/latitude bounds.
- Bounds must satisfy `-180 <= west < east <= 180` and `-90 <= south < north <= 90`.
- Reversed longitude bounds, including antimeridian-crossing boxes, are invalid.
- Invalid inputs raise `InvalidAOIError`; do not export `normalize_bbox` from `sentinel2_ingest.__init__`.
- The function docstring must specify inputs, return geometry, EPSG:4326 coordinate contract, and exceptions.
- Do not create commits; the user owns commits.

---

### Task 1: Add the geometry dependency and public-contract tests

**Files:**
- Modify: `pyproject.toml:10`
- Modify: `uv.lock`
- Create: `tests/test_aoi.py`

**Interfaces:**
- Consumes: `sentinel2_ingest.errors.InvalidAOIError`.
- Produces: test coverage for `sentinel2_ingest.aoi.normalize_bbox` and an
  installed `shapely` runtime dependency.

- [ ] **Step 1: Add Shapely to runtime dependencies and refresh the lockfile**

```toml
[project]
dependencies = [
    "shapely>=2.0",
]
```

Run: `uv lock`
Expected: `uv.lock` includes Shapely and its resolved distribution metadata.

- [ ] **Step 2: Write failing AOI tests**

Create `tests/test_aoi.py` with coverage for the module-scoped import, expected
geometry, WGS84 boundary values, and all invalid categories:

```python
import math

import pytest
from shapely.geometry import Polygon

from sentinel2_ingest.aoi import normalize_bbox
from sentinel2_ingest.errors import InvalidAOIError


def test_normalize_bbox_returns_a_valid_wgs84_rectangle() -> None:
    polygon = normalize_bbox(-3.2, 40.1, -3.0, 40.3)

    assert isinstance(polygon, Polygon)
    assert polygon.is_valid
    assert polygon.exterior.coords[:] == [
        (-3.2, 40.1),
        (-3.0, 40.1),
        (-3.0, 40.3),
        (-3.2, 40.3),
        (-3.2, 40.1),
    ]
    assert polygon.area == pytest.approx(0.04)


@pytest.mark.parametrize(
    ("bounds"),
    [
        ((-180, -90, 180, 90)),
        ((-180, 0, -179, 1)),
        ((179, -1, 180, 0)),
    ],
)
def test_normalize_bbox_accepts_wgs84_boundaries(
    bounds: tuple[float, float, float, float],
) -> None:
    assert normalize_bbox(*bounds).is_valid


@pytest.mark.parametrize(
    ("bounds"),
    [
        ((1, 0, 0, 1)),
        ((170, -1, -170, 1)),
        ((0, 1, 1, 0)),
        ((0, 0, 0, 1)),
        ((0, 0, 1, 0)),
        ((-181, 0, 0, 1)),
        ((0, -91, 1, 0)),
        ((0, 0, 181, 1)),
        ((0, 0, 1, 91)),
        ((math.nan, 0, 1, 1)),
        ((0, 0, math.inf, 1)),
        (("0", 0, 1, 1)),
    ],
)
def test_normalize_bbox_rejects_invalid_bounds(
    bounds: tuple[object, object, object, object],
) -> None:
    with pytest.raises(InvalidAOIError):
        normalize_bbox(*bounds)
```

- [ ] **Step 3: Run the AOI tests to verify they fail**

Run: `uv run pytest tests/test_aoi.py -v`
Expected: FAIL because `sentinel2_ingest.aoi` and `normalize_bbox` do not yet
exist.

### Task 2: Implement WGS84 AOI normalization

**Files:**
- Create: `src/sentinel2_ingest/aoi.py`
- Test: `tests/test_aoi.py`

**Interfaces:**
- Consumes: four positional `object` inputs and
  `sentinel2_ingest.errors.InvalidAOIError`.
- Produces: `normalize_bbox(west: object, south: object, east: object, north: object) -> Polygon`.

- [ ] **Step 1: Implement the documented module-scoped API**

```python
"""WGS84 area-of-interest normalization utilities."""

from math import isfinite
from numbers import Real

from shapely.geometry import Polygon

from .errors import InvalidAOIError


def normalize_bbox(
    west: object,
    south: object,
    east: object,
    north: object,
) -> Polygon:
    """Convert WGS84 bounds into a validated rectangular polygon.

    Args:
        west: Western longitude in degrees, in the inclusive range [-180, 180].
        south: Southern latitude in degrees, in the inclusive range [-90, 90].
        east: Eastern longitude in degrees, in the inclusive range [-180, 180].
        north: Northern latitude in degrees, in the inclusive range [-90, 90].

    Returns:
        A valid rectangular Shapely polygon with EPSG:4326 longitude/latitude
        coordinates. Shapely does not attach CRS metadata to the geometry.

    Raises:
        InvalidAOIError: If a bound is non-numeric or non-finite, outside WGS84
            limits, does not enclose area, or crosses the antimeridian.
    """
```

Use a private helper to reject anything that is not a finite `Real`, then
perform longitude range/order checks and latitude range/order checks before
passing these five coordinates to `Polygon`:

```python
return Polygon(
    [(west, south), (east, south), (east, north), (west, north), (west, south)]
)
```

Every rejection raises `InvalidAOIError` with a detail that identifies the
failed condition. Do not alter `src/sentinel2_ingest/__init__.py`.

- [ ] **Step 2: Run focused tests to verify the implementation passes**

Run: `uv run pytest tests/test_aoi.py -v`
Expected: PASS.

- [ ] **Step 3: Run static and formatting checks for the touched module**

Run: `uv run ruff check src/sentinel2_ingest/aoi.py tests/test_aoi.py && uv run ruff format --check src/sentinel2_ingest/aoi.py tests/test_aoi.py && uv run mypy src/sentinel2_ingest/aoi.py`
Expected: all commands pass.

### Task 3: Verify package-level regression safety

**Files:**
- Verify: `src/sentinel2_ingest/__init__.py`
- Verify: `tests/`

**Interfaces:**
- Consumes: completed AOI module and existing package contract.
- Produces: evidence that the addition preserves the public package API and
  repository quality gates.

- [ ] **Step 1: Confirm the root package does not export the new function**

```python
import sentinel2_ingest


def test_normalize_bbox_is_not_reexported_from_package_root() -> None:
    assert not hasattr(sentinel2_ingest, "normalize_bbox")
```

Add this test to `tests/test_aoi.py` and keep `__init__.py` unchanged.

- [ ] **Step 2: Run the full quality suite**

Run: `make check`
Expected: lint, format, typecheck, and tests pass, including the configured
coverage threshold.

- [ ] **Step 3: Inspect the final working-tree diff**

Run: `git diff --check && git status --short`
Expected: only `pyproject.toml`, `uv.lock`, `src/sentinel2_ingest/aoi.py`,
`tests/test_aoi.py`, and the design/plan documentation are modified or added;
there is no commit.
