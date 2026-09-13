"""Public quality-policy tests."""

import math
from fractions import Fraction

import pytest

from sentinel2_ingest.errors import InvalidQualityPolicyError
from sentinel2_ingest.quality import (
    UNUSABLE_SCL_CLASSES,
    USABLE_SCL_CLASSES,
    QualityPolicy,
)


def test_quality_policy_defaults_to_documented_thresholds() -> None:
    """A default policy must preserve the documented acceptance cutoffs."""
    policy = QualityPolicy()

    assert policy.usable_threshold == 80.0
    assert policy.risky_threshold == 50.0


def test_quality_policy_uses_the_documented_scl_classifications() -> None:
    """A wrong SCL grouping would accept unusable pixels or reject usable ones."""
    assert frozenset({2, 4, 5, 6, 7}) == USABLE_SCL_CLASSES
    assert frozenset({0, 1, 3, 8, 9, 10, 11}) == UNUSABLE_SCL_CLASSES
    assert USABLE_SCL_CLASSES.isdisjoint(UNUSABLE_SCL_CLASSES)


def test_quality_policy_accepts_strictly_ordered_boundary_thresholds() -> None:
    """Legal inclusive outer limits must remain configurable."""
    policy = QualityPolicy(usable_threshold=100, risky_threshold=0)

    assert policy.usable_threshold == 100.0
    assert policy.risky_threshold == 0.0


@pytest.mark.parametrize(
    ("usable_threshold", "risky_threshold"),
    [
        (50, 50),
        (49, 50),
        (101, 50),
        (80, -1),
        (math.inf, 50),
        (80, math.nan),
        (True, 50),
        (80, "50"),
        (10**400, 50),
    ],
)
def test_quality_policy_rejects_invalid_thresholds(
    usable_threshold: object,
    risky_threshold: object,
) -> None:
    """Invalid thresholds must not create policies that rank a candidate."""
    with pytest.raises(InvalidQualityPolicyError):
        QualityPolicy(
            usable_threshold=usable_threshold,
            risky_threshold=risky_threshold,
        )


@pytest.mark.parametrize(
    ("usable_threshold", "risky_threshold"),
    [
        (80, Fraction(-1, 10**400)),
        (Fraction(100, 1) + Fraction(1, 10**400), 50),
        (Fraction(80, 1) + Fraction(1, 10**400), 80),
    ],
)
def test_quality_policy_rejects_exact_values_that_float_rounding_would_accept(
    usable_threshold: object,
    risky_threshold: object,
) -> None:
    """Float conversion must not move an invalid threshold across a boundary."""
    with pytest.raises(InvalidQualityPolicyError):
        QualityPolicy(
            usable_threshold=usable_threshold,
            risky_threshold=risky_threshold,
        )


def test_quality_policy_serializes_thresholds_and_sorted_scl_classes() -> None:
    """Consumers need a deterministic JSON-ready representation of the policy."""
    policy = QualityPolicy(usable_threshold=90, risky_threshold=20)

    assert policy.to_dict() == {
        "usable_threshold": 90.0,
        "risky_threshold": 20.0,
        "usable_scl_classes": [2, 4, 5, 6, 7],
        "unusable_scl_classes": [0, 1, 3, 8, 9, 10, 11],
    }


def test_quality_policy_api_is_reexported_from_package_root() -> None:
    """Callers should use the documented package-level quality-policy API."""
    import sentinel2_ingest

    assert sentinel2_ingest.QualityPolicy is QualityPolicy
    assert sentinel2_ingest.USABLE_SCL_CLASSES == USABLE_SCL_CLASSES
    assert sentinel2_ingest.UNUSABLE_SCL_CLASSES == UNUSABLE_SCL_CLASSES
