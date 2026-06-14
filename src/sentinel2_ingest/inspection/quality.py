from __future__ import annotations

from dataclasses import dataclass

from sentinel2_ingest.models import AoiQualityMetrics, QualityStatus


@dataclass(frozen=True)
class QualityAssessment:
    """Quality decision for one AOI-level candidate scene assessment."""

    status: QualityStatus
    reasons: list[str]


def classify_quality(
    *,
    metrics: AoiQualityMetrics,
    min_usable_pixel_ratio: float = 0.80,
    max_cloud_pixel_ratio: float = 0.10,
    max_shadow_pixel_ratio: float = 0.10,
    max_no_data_ratio: float = 0.05,
    risky_min_usable_pixel_ratio: float = 0.60,
) -> QualityAssessment:
    """Classify AOI-level quality metrics into a reusable quality status.

    A scene is usable only when all configured thresholds pass.
    A scene is risky when thresholds fail but the usable-pixel ratio is still moderate.
    A scene is rejected when the usable-pixel ratio is too low.
    """
    reasons = _build_quality_reasons(
        metrics=metrics,
        min_usable_pixel_ratio=min_usable_pixel_ratio,
        max_cloud_pixel_ratio=max_cloud_pixel_ratio,
        max_shadow_pixel_ratio=max_shadow_pixel_ratio,
        max_no_data_ratio=max_no_data_ratio,
    )

    if not reasons:
        return QualityAssessment(status=QualityStatus.USABLE, reasons=[])

    if metrics.usable_pixel_ratio >= risky_min_usable_pixel_ratio:
        return QualityAssessment(status=QualityStatus.RISKY, reasons=reasons)

    return QualityAssessment(status=QualityStatus.REJECTED, reasons=reasons)


def _build_quality_reasons(
    *,
    metrics: AoiQualityMetrics,
    min_usable_pixel_ratio: float,
    max_cloud_pixel_ratio: float,
    max_shadow_pixel_ratio: float,
    max_no_data_ratio: float,
) -> list[str]:
    reasons: list[str] = []

    if metrics.usable_pixel_ratio < min_usable_pixel_ratio:
        reasons.append(
            "AOI usable pixel ratio "
            f"{metrics.usable_pixel_ratio:.3f} is below threshold "
            f"{min_usable_pixel_ratio:.3f}."
        )

    if metrics.cloud_pixel_ratio > max_cloud_pixel_ratio:
        reasons.append(
            "AOI cloud pixel ratio "
            f"{metrics.cloud_pixel_ratio:.3f} is above threshold "
            f"{max_cloud_pixel_ratio:.3f}."
        )

    if metrics.shadow_pixel_ratio > max_shadow_pixel_ratio:
        reasons.append(
            "AOI shadow pixel ratio "
            f"{metrics.shadow_pixel_ratio:.3f} is above threshold "
            f"{max_shadow_pixel_ratio:.3f}."
        )

    if metrics.no_data_ratio > max_no_data_ratio:
        reasons.append(
            "AOI no-data ratio "
            f"{metrics.no_data_ratio:.3f} is above threshold "
            f"{max_no_data_ratio:.3f}."
        )

    return reasons
