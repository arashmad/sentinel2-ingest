from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

SENTINEL_HUB_BASE_URL = "https://services.sentinel-hub.com"
SENTINEL_HUB_TOKEN_URL = (
    "https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token"
)


class SentinelHubConfig(BaseModel):
    """Configuration required to construct a Sentinel Hub provider."""

    model_config = ConfigDict(frozen=True)

    client_id: str = Field(min_length=1)
    client_secret: str = Field(min_length=1)
    base_url: str = SENTINEL_HUB_BASE_URL
    token_url: str = SENTINEL_HUB_TOKEN_URL

    @field_validator("client_id", "client_secret", "base_url", "token_url")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        stripped_value = value.strip()

        if not stripped_value:
            raise ValueError("value must not be blank")

        return stripped_value
