# Quality Policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add validated, serializable public configuration for Sentinel-2 SCL-based AOI quality rules.

**Architecture:** A dependency-free `quality` module owns immutable SCL class sets and the frozen `QualityPolicy` dataclass. Threshold validation is centralized, construction normalizes valid real numbers to floats, and invalid policies use a new package error. The package root re-exports the model and constants; `to_dict()` returns deterministic JSON-ready values.

**Tech Stack:** Python 3.11–3.13, standard-library `dataclasses`/`math`/`numbers`, pytest, mypy, Ruff.

**Spec:** `docs/superpowers/specs/2026-09-13-quality-policy-design.md`

## Global Constraints

- Do not add a serialization or model dependency.
- Defaults are `usable_threshold=80.0` and `risky_threshold=50.0`.
- Values must satisfy exactly `0 <= risky_threshold < usable_threshold <= 100`; reject booleans and non-finite values.
- Usable SCL classes are exactly `{2, 4, 5, 6, 7}`; unusable classes are exactly `{0, 1, 3, 8, 9, 10, 11}`.
- Serialization uses JSON-ready primitives and sorted SCL lists.
- Preserve public export conventions and strict mypy/Ruff conformance.

---

### Task 1: Add a public validation error

**Files:**
- Modify: `src/sentinel2_ingest/errors.py`
- Modify: `src/sentinel2_ingest/__init__.py`
- Modify: `tests/test_errors.py`

**Interfaces:**
- Consumes: `Sentinel2IngestError`.
- Produces: `InvalidQualityPolicyError(details: str)`, available from both `sentinel2_ingest.errors` and `sentinel2_ingest`.

- [ ] **Step 1: Write the failing error-contract test**

Add `"InvalidQualityPolicyError"` to `PUBLIC_ERROR_NAMES` and add this case to the message parametrization in `tests/test_errors.py`:

```python
(
    "InvalidQualityPolicyError",
    "thresholds must satisfy 0 <= risky < usable <= 100",
    "Invalid quality policy: thresholds must satisfy 0 <= risky < usable <= 100.",
),
```

- [ ] **Step 2: Run it to verify RED**

Run: `uv run pytest tests/test_errors.py -q`

Expected: FAIL because the new root export does not exist.

- [ ] **Step 3: Implement the minimum public error**

Add to `errors.py`:

```python
class InvalidQualityPolicyError(Sentinel2IngestError):
    """Raised when a scene-quality policy is invalid."""

    def __init__(self, details: str) -> None:
        super().__init__(f"Invalid quality policy: {details}.")
```

Import it in `__init__.py` and add `"InvalidQualityPolicyError"` to `__all__`.

- [ ] **Step 4: Run it to verify GREEN**

Run: `uv run pytest tests/test_errors.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/sentinel2_ingest/errors.py src/sentinel2_ingest/__init__.py tests/test_errors.py
git commit -m "feat: add quality policy validation error"
```

### Task 2: Add immutable SCL classifications and validated thresholds

**Files:**
- Create: `src/sentinel2_ingest/quality.py`
- Create: `tests/test_quality.py`

**Interfaces:**
- Consumes: `InvalidQualityPolicyError`.
- Produces: `USABLE_SCL_CLASSES: frozenset[int]`, `UNUSABLE_SCL_CLASSES: frozenset[int]`, and `QualityPolicy(usable_threshold: float = 80.0, risky_threshold: float = 50.0)`.

- [ ] **Step 1: Write failing defaults, classifications, and boundary tests**

Create `tests/test_quality.py`:

```python
from sentinel2_ingest.quality import (
    UNUSABLE_SCL_CLASSES,
    USABLE_SCL_CLASSES,
    QualityPolicy,
)


def test_quality_policy_defaults_to_documented_thresholds() -> None:
    policy = QualityPolicy()

    assert policy.usable_threshold == 80.0
    assert policy.risky_threshold == 50.0


def test_quality_policy_uses_the_documented_scl_classifications() -> None:
    assert USABLE_SCL_CLASSES == frozenset({2, 4, 5, 6, 7})
    assert UNUSABLE_SCL_CLASSES == frozenset({0, 1, 3, 8, 9, 10, 11})
    assert USABLE_SCL_CLASSES.isdisjoint(UNUSABLE_SCL_CLASSES)


def test_quality_policy_accepts_strictly_ordered_boundary_thresholds() -> None:
    policy = QualityPolicy(usable_threshold=100, risky_threshold=0)

    assert policy.usable_threshold == 100.0
    assert policy.risky_threshold == 0.0
```

- [ ] **Step 2: Run it to verify RED**

Run: `uv run pytest tests/test_quality.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'sentinel2_ingest.quality'`.

- [ ] **Step 3: Implement the minimum model**

Create `quality.py`:

```python
"""Validated public policy for Sentinel-2 scene-quality classification."""

from dataclasses import dataclass
from math import isfinite
from numbers import Real

from .errors import InvalidQualityPolicyError

USABLE_SCL_CLASSES = frozenset({2, 4, 5, 6, 7})
UNUSABLE_SCL_CLASSES = frozenset({0, 1, 3, 8, 9, 10, 11})


def _normalize_threshold(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise InvalidQualityPolicyError(f"{name} threshold must be a finite number")
    try:
        threshold = float(value)
    except OverflowError as error:
        raise InvalidQualityPolicyError(
            f"{name} threshold must be a finite number"
        ) from error
    if not isfinite(threshold):
        raise InvalidQualityPolicyError(f"{name} threshold must be a finite number")
    return threshold


@dataclass(frozen=True)
class QualityPolicy:
    usable_threshold: float = 80.0
    risky_threshold: float = 50.0

    def __post_init__(self) -> None:
        usable = _normalize_threshold("usable", self.usable_threshold)
        risky = _normalize_threshold("risky", self.risky_threshold)
        if not 0 <= risky < usable <= 100:
            raise InvalidQualityPolicyError(
                "thresholds must satisfy 0 <= risky < usable <= 100"
            )
        object.__setattr__(self, "usable_threshold", usable)
        object.__setattr__(self, "risky_threshold", risky)
```

- [ ] **Step 4: Run it to verify GREEN**

Run: `uv run pytest tests/test_quality.py -q`

Expected: PASS with 3 tests.

- [ ] **Step 5: Commit**

```bash
git add src/sentinel2_ingest/quality.py tests/test_quality.py
git commit -m "feat: add quality policy model"
```

### Task 3: Test invalid configurations and serialization

**Files:**
- Modify: `src/sentinel2_ingest/quality.py`
- Modify: `tests/test_quality.py`

**Interfaces:**
- Consumes: `QualityPolicy` and `InvalidQualityPolicyError`.
- Produces: `QualityPolicy.to_dict() -> dict[str, float | list[int]]`.

- [ ] **Step 1: Write failing invalid-input and serialization tests**

Add imports for `math`, `pytest`, and `InvalidQualityPolicyError`, then append:

```python
@pytest.mark.parametrize(
    ("usable_threshold", "risky_threshold"),
    [
        (50, 50), (49, 50), (101, 50), (80, -1),
        (math.inf, 50), (80, math.nan), (True, 50), (80, "50"),
        (10**400, 50),
    ],
)
def test_quality_policy_rejects_invalid_thresholds(
    usable_threshold: object, risky_threshold: object
) -> None:
    with pytest.raises(InvalidQualityPolicyError):
        QualityPolicy(
            usable_threshold=usable_threshold,
            risky_threshold=risky_threshold,
        )


def test_quality_policy_serializes_thresholds_and_sorted_scl_classes() -> None:
    policy = QualityPolicy(usable_threshold=90, risky_threshold=20)

    assert policy.to_dict() == {
        "usable_threshold": 90.0,
        "risky_threshold": 20.0,
        "usable_scl_classes": [2, 4, 5, 6, 7],
        "unusable_scl_classes": [0, 1, 3, 8, 9, 10, 11],
    }
```

- [ ] **Step 2: Run it to verify RED**

Run: `uv run pytest tests/test_quality.py -q`

Expected: FAIL because `QualityPolicy` has no `to_dict()`; invalid cases already handled by Task 2 may pass as regression coverage.

- [ ] **Step 3: Implement deterministic serialization**

Add inside `QualityPolicy`:

```python
def to_dict(self) -> dict[str, float | list[int]]:
    """Return JSON-ready policy values with deterministic SCL ordering."""
    return {
        "usable_threshold": self.usable_threshold,
        "risky_threshold": self.risky_threshold,
        "usable_scl_classes": sorted(USABLE_SCL_CLASSES),
        "unusable_scl_classes": sorted(UNUSABLE_SCL_CLASSES),
    }
```

- [ ] **Step 4: Run it to verify GREEN**

Run: `uv run pytest tests/test_quality.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/sentinel2_ingest/quality.py tests/test_quality.py
git commit -m "feat: serialize quality policy"
```

### Task 4: Publish the quality-policy API and run full checks

**Files:**
- Modify: `src/sentinel2_ingest/__init__.py`
- Modify: `tests/test_quality.py`

**Interfaces:**
- Consumes: `QualityPolicy`, `USABLE_SCL_CLASSES`, and `UNUSABLE_SCL_CLASSES`.
- Produces: root imports `sentinel2_ingest.QualityPolicy`, `sentinel2_ingest.USABLE_SCL_CLASSES`, and `sentinel2_ingest.UNUSABLE_SCL_CLASSES`.

- [ ] **Step 1: Write the failing root-export test**

Append:

```python
def test_quality_policy_api_is_reexported_from_package_root() -> None:
    import sentinel2_ingest

    assert sentinel2_ingest.QualityPolicy is QualityPolicy
    assert sentinel2_ingest.USABLE_SCL_CLASSES == USABLE_SCL_CLASSES
    assert sentinel2_ingest.UNUSABLE_SCL_CLASSES == UNUSABLE_SCL_CLASSES
```

- [ ] **Step 2: Run it to verify RED**

Run: `uv run pytest tests/test_quality.py::test_quality_policy_api_is_reexported_from_package_root -q`

Expected: FAIL because the package root does not yet expose `QualityPolicy`.

- [ ] **Step 3: Re-export the public quality API**

Add to `__init__.py`:

```python
from .quality import (
    UNUSABLE_SCL_CLASSES,
    USABLE_SCL_CLASSES,
    QualityPolicy,
)
```

Add `"QualityPolicy"`, `"USABLE_SCL_CLASSES"`, and `"UNUSABLE_SCL_CLASSES"` to `__all__`.

- [ ] **Step 4: Run full verification**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`

Expected: tests pass at or above 90% coverage, Ruff has no violations, and mypy has no errors.

- [ ] **Step 5: Commit**

```bash
git add src/sentinel2_ingest/__init__.py tests/test_quality.py
git commit -m "feat: publish quality policy API"
```
