# Quality Policy Design

## Purpose

Provide validated, serializable public configuration for classifying a
Sentinel-2 scene's area-of-interest quality from its Scene Classification Layer
(SCL) values. This establishes the domain contract consumed by later scene
inspection and ranking features.

## Public API

`sentinel2_ingest.quality` will define:

- `QualityPolicy`, a frozen dataclass with `usable_threshold` and
  `risky_threshold` float fields.
- `USABLE_SCL_CLASSES`, the immutable set `{2, 4, 5, 6, 7}`.
- `UNUSABLE_SCL_CLASSES`, the immutable set `{0, 1, 3, 8, 9, 10, 11}`.

`QualityPolicy()` defaults to `usable_threshold=80.0` and
`risky_threshold=50.0`. Its `to_dict()` method returns JSON-ready primitive
values under the keys `usable_threshold`, `risky_threshold`,
`usable_scl_classes`, and `unusable_scl_classes`. SCL classes are represented
as sorted lists in serialized output so it is deterministic and JSON-safe.

The package root will re-export `QualityPolicy`, the two SCL class constants,
and `InvalidQualityPolicyError` as public API.

## Validation and Errors

Both thresholds must be real, finite numbers (booleans are rejected) and must
satisfy `0 <= risky_threshold < usable_threshold <= 100`. Construction rejects
all invalid values with `InvalidQualityPolicyError`, a
`Sentinel2IngestError` subclass whose message identifies the invalid policy
detail.

The SCL class sets are fixed domain constants. They do not overlap; class `2`
is usable, while classes `0` and `11` are unusable as specified by issue #8.

## Implementation Boundaries

The new `quality.py` module is self-contained and has no provider, Shapely, or
serialization-library dependency. It uses only the Python standard library and
the existing public error hierarchy. No inspection/ranking behavior is added;
later features consume this policy.

## Tests

Tests will verify defaults, both valid threshold boundaries, representative
invalid type/range/order combinations, the exact SCL classifications, stable
`to_dict()` output, and root-level public exports. Existing error-contract
tests will include `InvalidQualityPolicyError`.
