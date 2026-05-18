from __future__ import annotations

from typing import Protocol

from sentinel2_ingest.models import CandidateScene, InspectionRequest


class SceneProvider(Protocol):
    """Provider interface for scene inspection.

    Implementations may call real APIs, local files, fixtures, or test doubles.
    The public client should not depend on provider-specific details.
    """

    def inspect(self, request: InspectionRequest) -> list[CandidateScene]:
        """Return candidate scenes for an inspection request."""
        ...