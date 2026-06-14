from __future__ import annotations

from datetime import UTC, datetime

from sentinel2_ingest.inspection import select_best_candidate
from sentinel2_ingest.models import AoiQualityMetrics, CandidateScene, QualityStatus


def make_quality(
    *,
    usable_pixel_count: int = 80,
    cloud_pixel_count: int = 5,
    shadow_pixel_count: int = 2,
    valid_data_pixel_count: int = 100,
) -> AoiQualityMetrics:
    return AoiQualityMetrics(
        total_pixel_count=100,
        valid_data_pixel_count=valid_data_pixel_count,
        usable_pixel_count=usable_pixel_count,
        cloud_pixel_count=cloud_pixel_count,
        shadow_pixel_count=shadow_pixel_count,
        snow_pixel_count=0,
        no_data_pixel_count=0,
        defective_pixel_count=0,
        dark_area_pixel_count=0,
        unclassified_pixel_count=0,
    )


def make_candidate(
    *,
    scene_id: str,
    quality_status: QualityStatus | None = QualityStatus.USABLE,
    quality: AoiQualityMetrics | None = None,
    acquired_at: datetime | None = None,
) -> CandidateScene:
    return CandidateScene(
        scene_id=scene_id,
        datetime=acquired_at or datetime(2025, 6, 1, 10, 0, tzinfo=UTC),
        collection="sentinel-2-l2a",
        source="test",
        scene_cloud_coverage=10.0,
        quality=quality if quality is not None else make_quality(),
        quality_status=quality_status,
    )


def test_select_best_candidate_returns_best_usable_candidate() -> None:
    lower_quality_usable = make_candidate(
        scene_id="lower-quality-usable",
        quality=make_quality(usable_pixel_count=75),
        quality_status=QualityStatus.USABLE,
    )
    higher_quality_usable = make_candidate(
        scene_id="higher-quality-usable",
        quality=make_quality(usable_pixel_count=90),
        quality_status=QualityStatus.USABLE,
    )

    best = select_best_candidate([lower_quality_usable, higher_quality_usable])

    assert best is not None
    assert best.scene_id == "higher-quality-usable"


def test_select_best_candidate_ignores_risky_candidate_by_default() -> None:
    risky = make_candidate(
        scene_id="risky",
        quality=make_quality(usable_pixel_count=90),
        quality_status=QualityStatus.RISKY,
    )

    best = select_best_candidate([risky])

    assert best is None


def test_select_best_candidate_can_return_risky_candidate_explicitly() -> None:
    risky = make_candidate(
        scene_id="risky",
        quality=make_quality(usable_pixel_count=70),
        quality_status=QualityStatus.RISKY,
    )

    best = select_best_candidate([risky], allow_risky=True)

    assert best is not None
    assert best.scene_id == "risky"


def test_select_best_candidate_prefers_usable_over_risky_when_risky_is_allowed() -> None:
    risky = make_candidate(
        scene_id="risky",
        quality=make_quality(usable_pixel_count=95),
        quality_status=QualityStatus.RISKY,
    )
    usable = make_candidate(
        scene_id="usable",
        quality=make_quality(usable_pixel_count=80),
        quality_status=QualityStatus.USABLE,
    )

    best = select_best_candidate([risky, usable], allow_risky=True)

    assert best is not None
    assert best.scene_id == "usable"


def test_select_best_candidate_never_returns_rejected_candidate() -> None:
    rejected = make_candidate(
        scene_id="rejected",
        quality=make_quality(usable_pixel_count=95),
        quality_status=QualityStatus.REJECTED,
    )

    best = select_best_candidate([rejected], allow_risky=True)

    assert best is None


def test_select_best_candidate_returns_none_for_empty_list() -> None:
    best = select_best_candidate([])

    assert best is None


def test_select_best_candidate_ignores_candidate_without_quality_status() -> None:
    missing_status = make_candidate(
        scene_id="missing-status",
        quality_status=None,
    )

    best = select_best_candidate([missing_status], allow_risky=True)

    assert best is None
