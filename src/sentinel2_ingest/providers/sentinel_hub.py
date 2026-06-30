from __future__ import annotations

from collections.abc import Mapping

from sentinel2_ingest.config import SentinelHubConfig
from sentinel2_ingest.models import CandidateScene, InspectionRequest


class SentinelHubProvider:
    """Sentinel Hub provider skeleton.

    Real candidate search is implemented in a later milestone.
    """

    def __init__(self, config: SentinelHubConfig) -> None:
        self.config = config

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> SentinelHubProvider:
        """Create a provider from environment-backed Sentinel Hub config."""

        return cls(config=SentinelHubConfig.from_env(env=env))

    def inspect(self, request: InspectionRequest) -> list[CandidateScene]:
        """Return Sentinel-2 candidate scenes for an inspection request."""

        raise NotImplementedError("Sentinel Hub candidate search is not implemented yet")
