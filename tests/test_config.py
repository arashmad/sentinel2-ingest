from __future__ import annotations

import pytest
from pydantic import ValidationError

from sentinel2_ingest import SentinelHubConfig
from sentinel2_ingest.config import (
    SENTINEL_HUB_BASE_URL,
    SENTINEL_HUB_BASE_URL_ENV,
    SENTINEL_HUB_CLIENT_ID_ENV,
    SENTINEL_HUB_CLIENT_SECRET_ENV,
    SENTINEL_HUB_TOKEN_URL,
    SENTINEL_HUB_TOKEN_URL_ENV,
)


def test_sentinel_hub_config_accepts_required_values() -> None:
    config = SentinelHubConfig(
        client_id="test-client-id",
        client_secret="test-client-secret",
    )

    assert config.client_id == "test-client-id"
    assert config.client_secret == "test-client-secret"
    assert config.base_url == SENTINEL_HUB_BASE_URL
    assert config.token_url == SENTINEL_HUB_TOKEN_URL


def test_sentinel_hub_config_rejects_empty_client_id() -> None:
    with pytest.raises(ValidationError):
        SentinelHubConfig(
            client_id="",
            client_secret="test-client-secret",
        )


def test_sentinel_hub_config_rejects_empty_client_secret() -> None:
    with pytest.raises(ValidationError):
        SentinelHubConfig(
            client_id="test-client-id",
            client_secret="",
        )


def test_sentinel_hub_config_rejects_blank_required_values() -> None:
    with pytest.raises(ValidationError, match="value must not be blank"):
        SentinelHubConfig(
            client_id="   ",
            client_secret="test-client-secret",
        )


def test_sentinel_hub_config_strips_values() -> None:
    config = SentinelHubConfig(
        client_id="  test-client-id  ",
        client_secret="  test-client-secret  ",
        base_url="  https://example.test  ",
        token_url="  https://example.test/token  ",
    )

    assert config.client_id == "test-client-id"
    assert config.client_secret == "test-client-secret"
    assert config.base_url == "https://example.test"
    assert config.token_url == "https://example.test/token"


def test_sentinel_hub_config_loads_from_env_mapping() -> None:
    config = SentinelHubConfig.from_env(
        {
            SENTINEL_HUB_CLIENT_ID_ENV: "test-client-id",
            SENTINEL_HUB_CLIENT_SECRET_ENV: "test-client-secret",
        }
    )

    assert config.client_id == "test-client-id"
    assert config.client_secret == "test-client-secret"
    assert config.base_url == SENTINEL_HUB_BASE_URL
    assert config.token_url == SENTINEL_HUB_TOKEN_URL


def test_sentinel_hub_config_loads_optional_urls_from_env_mapping() -> None:
    config = SentinelHubConfig.from_env(
        {
            SENTINEL_HUB_CLIENT_ID_ENV: "test-client-id",
            SENTINEL_HUB_CLIENT_SECRET_ENV: "test-client-secret",
            SENTINEL_HUB_BASE_URL_ENV: "https://example.test",
            SENTINEL_HUB_TOKEN_URL_ENV: "https://example.test/token",
        }
    )

    assert config.base_url == "https://example.test"
    assert config.token_url == "https://example.test/token"


def test_sentinel_hub_config_from_env_rejects_missing_client_id() -> None:
    with pytest.raises(ValidationError):
        SentinelHubConfig.from_env(
            {
                SENTINEL_HUB_CLIENT_SECRET_ENV: "test-client-secret",
            }
        )


def test_sentinel_hub_config_from_env_rejects_missing_client_secret() -> None:
    with pytest.raises(ValidationError):
        SentinelHubConfig.from_env(
            {
                SENTINEL_HUB_CLIENT_ID_ENV: "test-client-id",
            }
        )


def test_sentinel_hub_config_from_real_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SENTINEL_HUB_CLIENT_ID_ENV, "test-client-id")
    monkeypatch.setenv(SENTINEL_HUB_CLIENT_SECRET_ENV, "test-client-secret")

    config = SentinelHubConfig.from_env()

    assert config.client_id == "test-client-id"
    assert config.client_secret == "test-client-secret"
