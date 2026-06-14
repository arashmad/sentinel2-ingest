from __future__ import annotations

from collections.abc import Sequence

from sentinel2_ingest.models import CandidateScene, QualityStatus

_STATUS_RANK = {
    QualityStatus.USABLE: 0,
    QualityStatus.RISKY: 1,
    QualityStatus.REJECTED: 2,
}


def rank_candidates(candidates: Sequence[CandidateScene]) -> list[CandidateScene]:
    """Return candidates ranked from best to worst.

    Ranking order:
    1. candidates with quality and known status first
    2. usable before risky before rejected
    3. higher usable pixel ratio
    4. lower cloud pixel ratio
    5. lower shadow pixel ratio
    6. newer acquisition datetime
    7. scene_id as deterministic final tie-breaker
    """
    return sorted(candidates, key=_candidate_sort_key)


def _candidate_sort_key(candidate: CandidateScene) -> tuple[object, ...]:
    quality_missing = candidate.quality is None or candidate.quality_status is None

    if candidate.quality is None:
        usable_pixel_ratio = 0.0
        cloud_pixel_ratio = 1.0
        shadow_pixel_ratio = 1.0
    else:
        usable_pixel_ratio = candidate.quality.usable_pixel_ratio
        cloud_pixel_ratio = candidate.quality.cloud_pixel_ratio
        shadow_pixel_ratio = candidate.quality.shadow_pixel_ratio

    return (
        quality_missing,
        _STATUS_RANK.get(candidate.quality_status, 3),
        -usable_pixel_ratio,
        cloud_pixel_ratio,
        shadow_pixel_ratio,
        -candidate.datetime.timestamp(),
        candidate.scene_id,
    )
