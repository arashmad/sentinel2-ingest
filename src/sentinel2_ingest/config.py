from __future__ import annotations

import os
from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator

SENTINEL_HUB_BASE_URL = "https://services.sentinel-hub.com"
SENTINEL_HUB_TOKEN_URL = (
    "https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token"
)

SENTINEL_HUB_CLIENT_ID_ENV = "SENTINEL2_INGEST_SENTINEL_HUB_CLIENT_ID"
SENTINEL_HUB_CLIENT_SECRET_ENV = "SENTINEL2_INGEST_SENTINEL_HUB_CLIENT_SECRET"
SENTINEL_HUB_BASE_URL_ENV = "SENTINEL2_INGEST_SENTINEL_HUB_BASE_URL"
SENTINEL_HUB_TOKEN_URL_ENV = "SENTINEL2_INGEST_SENTINEL_HUB_TOKEN_URL"


class SentinelHubConfig(BaseModel):
    """Configuration required to construct a Sentinel Hub provider."""

    model_config = ConfigDict(frozen=True)

    client_id: str = Field(min_length=1)
    client_secret: str = Field(min_length=1)
    base_url: str = SENTINEL_HUB_BASE_URL
    token_url: str = SENTINEL_HUB_TOKEN_URL

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> SentinelHubConfig:
        """Create config from environment variables."""

        values = os.environ if env is None else env

        return cls(
            client_id=values.get(SENTINEL_HUB_CLIENT_ID_ENV, ""),
            client_secret=values.get(SENTINEL_HUB_CLIENT_SECRET_ENV, ""),
            base_url=values.get(SENTINEL_HUB_BASE_URL_ENV, SENTINEL_HUB_BASE_URL),
            token_url=values.get(SENTINEL_HUB_TOKEN_URL_ENV, SENTINEL_HUB_TOKEN_URL),
        )

    @field_validator("client_id", "client_secret", "base_url", "token_url")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError("value must not be blank")

        return stripped_value
