from __future__ import annotations

from sentinel2_ingest.inspection import classify_quality
from sentinel2_ingest.models import AoiQualityMetrics, QualityStatus


def make_metrics(
    *,
    total_pixel_count: int = 100,
    valid_data_pixel_count: int = 100,
    usable_pixel_count: int = 85,
    cloud_pixel_count: int = 5,
    shadow_pixel_count: int = 2,
    no_data_pixel_count: int = 0,
) -> AoiQualityMetrics:
    return AoiQualityMetrics(
        total_pixel_count=total_pixel_count,
        valid_data_pixel_count=valid_data_pixel_count,
        usable_pixel_count=usable_pixel_count,
        cloud_pixel_count=cloud_pixel_count,
        shadow_pixel_count=shadow_pixel_count,
        snow_pixel_count=0,
        no_data_pixel_count=no_data_pixel_count,
        defective_pixel_count=0,
        dark_area_pixel_count=0,
        unclassified_pixel_count=0,
    )


def test_classify_quality_returns_usable_when_all_thresholds_pass() -> None:
    assessment = classify_quality(metrics=make_metrics())

    assert assessment.status == QualityStatus.USABLE
    assert assessment.reasons == []


def test_classify_quality_returns_risky_when_thresholds_fail_but_usable_ratio_is_moderate() -> None:
    assessment = classify_quality(
        metrics=make_metrics(
            usable_pixel_count=70,
            cloud_pixel_count=20,
        )
    )

    assert assessment.status == QualityStatus.RISKY
    assert len(assessment.reasons) == 2
    assert "usable pixel ratio" in assessment.reasons[0]
    assert "cloud pixel ratio" in assessment.reasons[1]


def test_classify_quality_returns_rejected_when_usable_ratio_is_too_low() -> None:
    assessment = classify_quality(
        metrics=make_metrics(
            usable_pixel_count=40,
            cloud_pixel_count=45,
        )
    )

    assert assessment.status == QualityStatus.REJECTED
    assert assessment.reasons


def test_classify_quality_returns_multiple_reasons() -> None:
    assessment = classify_quality(
        metrics=make_metrics(
            total_pixel_count=100,
            valid_data_pixel_count=80,
            usable_pixel_count=50,
            cloud_pixel_count=20,
            shadow_pixel_count=12,
            no_data_pixel_count=20,
        )
    )

    assert assessment.status == QualityStatus.RISKY
    assert len(assessment.reasons) == 4
    assert any("usable pixel ratio" in reason for reason in assessment.reasons)
    assert any("cloud pixel ratio" in reason for reason in assessment.reasons)
    assert any("shadow pixel ratio" in reason for reason in assessment.reasons)
    assert any("no-data ratio" in reason for reason in assessment.reasons)


def test_classify_quality_respects_custom_thresholds() -> None:
    assessment = classify_quality(
        metrics=make_metrics(usable_pixel_count=75),
        min_usable_pixel_ratio=0.70,
    )

    assert assessment.status == QualityStatus.USABLE
    assert assessment.reasons == []
