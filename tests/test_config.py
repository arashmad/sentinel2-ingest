from __future__ import annotations

import pytest
from pydantic import ValidationError

from sentinel2_ingest import SentinelHubConfig
from sentinel2_ingest.config import SENTINEL_HUB_BASE_URL, SENTINEL_HUB_TOKEN_URL


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
