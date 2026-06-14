from __future__ import annotations

from datetime import UTC, datetime

from sentinel2_ingest.inspection import rank_candidates
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


def test_rank_candidates_orders_by_status() -> None:
    rejected = make_candidate(scene_id="rejected", quality_status=QualityStatus.REJECTED)
    risky = make_candidate(scene_id="risky", quality_status=QualityStatus.RISKY)
    usable = make_candidate(scene_id="usable", quality_status=QualityStatus.USABLE)

    ranked = rank_candidates([rejected, risky, usable])

    assert [candidate.scene_id for candidate in ranked] == ["usable", "risky", "rejected"]


def test_rank_candidates_prefers_higher_usable_ratio_within_same_status() -> None:
    lower_usable = make_candidate(
        scene_id="lower-usable",
        quality=make_quality(usable_pixel_count=70),
    )
    higher_usable = make_candidate(
        scene_id="higher-usable",
        quality=make_quality(usable_pixel_count=90),
    )

    ranked = rank_candidates([lower_usable, higher_usable])

    assert [candidate.scene_id for candidate in ranked] == ["higher-usable", "lower-usable"]


def test_rank_candidates_prefers_lower_cloud_ratio_when_usable_ratio_is_tied() -> None:
    higher_cloud = make_candidate(
        scene_id="higher-cloud",
        quality=make_quality(usable_pixel_count=80, cloud_pixel_count=15),
    )
    lower_cloud = make_candidate(
        scene_id="lower-cloud",
        quality=make_quality(usable_pixel_count=80, cloud_pixel_count=5),
    )

    ranked = rank_candidates([higher_cloud, lower_cloud])

    assert [candidate.scene_id for candidate in ranked] == ["lower-cloud", "higher-cloud"]


def test_rank_candidates_prefers_lower_shadow_ratio_when_cloud_ratio_is_tied() -> None:
    higher_shadow = make_candidate(
        scene_id="higher-shadow",
        quality=make_quality(
            usable_pixel_count=80,
            cloud_pixel_count=5,
            shadow_pixel_count=10,
        ),
    )
    lower_shadow = make_candidate(
        scene_id="lower-shadow",
        quality=make_quality(
            usable_pixel_count=80,
            cloud_pixel_count=5,
            shadow_pixel_count=2,
        ),
    )

    ranked = rank_candidates([higher_shadow, lower_shadow])

    assert [candidate.scene_id for candidate in ranked] == ["lower-shadow", "higher-shadow"]


def test_rank_candidates_prefers_newer_date_as_final_tie_breaker() -> None:
    older = make_candidate(
        scene_id="older",
        acquired_at=datetime(2025, 6, 1, 10, 0, tzinfo=UTC),
    )
    newer = make_candidate(
        scene_id="newer",
        acquired_at=datetime(2025, 6, 2, 10, 0, tzinfo=UTC),
    )

    ranked = rank_candidates([older, newer])

    assert [candidate.scene_id for candidate in ranked] == ["newer", "older"]


def test_rank_candidates_places_missing_quality_last() -> None:
    missing_quality = make_candidate(
        scene_id="missing-quality",
        quality=None,
        quality_status=None,
    )
    rejected = make_candidate(
        scene_id="rejected",
        quality_status=QualityStatus.REJECTED,
    )

    ranked = rank_candidates([missing_quality, rejected])

    assert [candidate.scene_id for candidate in ranked] == ["rejected", "missing-quality"]


def test_rank_candidates_uses_scene_id_as_deterministic_final_tie_breaker() -> None:
    scene_b = make_candidate(scene_id="scene-b")
    scene_a = make_candidate(scene_id="scene-a")

    ranked = rank_candidates([scene_b, scene_a])

    assert [candidate.scene_id for candidate in ranked] == ["scene-a", "scene-b"]
