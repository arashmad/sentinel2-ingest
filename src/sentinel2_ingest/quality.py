"""Validated public policy for Sentinel-2 scene-quality classification."""

from dataclasses import dataclass
from math import isfinite
from numbers import Real

from .errors import InvalidQualityPolicyError

USABLE_SCL_CLASSES = frozenset({2, 4, 5, 6, 7})
"""SCL classes that count as usable area."""

UNUSABLE_SCL_CLASSES = frozenset({0, 1, 3, 8, 9, 10, 11})
"""SCL classes that count as unusable area."""


def _normalize_threshold(name: str, value: object) -> float:
    """Return a finite numeric threshold or raise the public validation error."""
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
    """Validated SCL quality thresholds used to classify a candidate AOI."""

    usable_threshold: float = 80.0
    risky_threshold: float = 50.0

    def __post_init__(self) -> None:
        """Normalize thresholds and enforce their strictly ordered range."""
        usable = _normalize_threshold("usable", self.usable_threshold)
        risky = _normalize_threshold("risky", self.risky_threshold)

        if not 0 <= risky < usable <= 100:
            raise InvalidQualityPolicyError(
                "thresholds must satisfy 0 <= risky < usable <= 100"
            )

        object.__setattr__(self, "usable_threshold", usable)
        object.__setattr__(self, "risky_threshold", risky)
