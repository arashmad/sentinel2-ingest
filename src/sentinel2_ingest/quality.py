"""Validated public policy for Sentinel-2 scene-quality classification."""

from dataclasses import dataclass
from math import isfinite
from numbers import Real

from .errors import InvalidQualityPolicyError

USABLE_SCL_CLASSES = frozenset({2, 4, 5, 6, 7})
"""SCL classes that count as usable area."""

UNUSABLE_SCL_CLASSES = frozenset({0, 1, 3, 8, 9, 10, 11})
"""SCL classes that count as unusable area."""


def _validate_threshold(name: str, value: object) -> Real:
    """Return a finite real threshold or raise the public validation error."""
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

    return value


@dataclass(frozen=True)
class QualityPolicy:
    """Validated SCL quality thresholds used to classify a candidate AOI."""

    usable_threshold: float = 80.0
    risky_threshold: float = 50.0

    def __post_init__(self) -> None:
        """Normalize thresholds and enforce their strictly ordered range."""
        _validate_threshold("usable", self.usable_threshold)
        _validate_threshold("risky", self.risky_threshold)
        if not 0 <= self.risky_threshold < self.usable_threshold <= 100:
            raise InvalidQualityPolicyError(
                "thresholds must satisfy 0 <= risky < usable <= 100"
            )

        usable = float(self.usable_threshold)
        risky = float(self.risky_threshold)

        if not 0 <= risky < usable <= 100:
            raise InvalidQualityPolicyError(
                "thresholds must satisfy 0 <= risky < usable <= 100"
            )

        object.__setattr__(self, "usable_threshold", usable)
        object.__setattr__(self, "risky_threshold", risky)

    def to_dict(self) -> dict[str, float | list[int]]:
        """Return JSON-ready policy values with deterministic SCL ordering."""
        return {
            "usable_threshold": self.usable_threshold,
            "risky_threshold": self.risky_threshold,
            "usable_scl_classes": sorted(USABLE_SCL_CLASSES),
            "unusable_scl_classes": sorted(UNUSABLE_SCL_CLASSES),
        }
