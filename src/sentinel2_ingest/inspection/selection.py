from __future__ import annotations

from collections.abc import Sequence

from sentinel2_ingest.inspection.ranking import rank_candidates
from sentinel2_ingest.models import CandidateScene, QualityStatus


def select_best_candidate(
    candidates: Sequence[CandidateScene],
    *,
    allow_risky: bool = False,
) -> CandidateScene | None:
    """Return the best acceptable candidate, or None if no candidate is acceptable.

    By default, only usable candidates are acceptable.
    Risky candidates can be selected explicitly with allow_risky=True.
    Rejected candidates and candidates without a quality status are never selected.
    """
    acceptable_statuses = {QualityStatus.USABLE}

    if allow_risky:
        acceptable_statuses.add(QualityStatus.RISKY)

    for candidate in rank_candidates(candidates):
        if candidate.quality_status in acceptable_statuses:
            return candidate

    return None
