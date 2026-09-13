"""Public quality-policy tests."""

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
