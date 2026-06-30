from __future__ import annotations

from datetime import date

import pytest

from sentinel2_ingest import InspectionRequest, SentinelHubConfig, SentinelHubProvider

VALID_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [13.0, 52.0],
            [13.1, 52.0],
            [13.1, 52.1],
            [13.0, 52.1],
            [13.0, 52.0],
        ]
    ],
}


def test_sentinel_hub_provider_accepts_config() -> None:
    config = SentinelHubConfig(
        client_id="test-client-id",
        client_secret="test-client-secret",
    )

    provider = SentinelHubProvider(config=config)

    assert provider.config == config


def test_sentinel_hub_provider_can_be_created_from_env_mapping() -> None:
    provider = SentinelHubProvider.from_env(
        {
            "SENTINEL2_INGEST_SENTINEL_HUB_CLIENT_ID": "test-client-id",
            "SENTINEL2_INGEST_SENTINEL_HUB_CLIENT_SECRET": "test-client-secret",
        }
    )

    assert provider.config.client_id == "test-client-id"
    assert provider.config.client_secret == "test-client-secret"


def test_sentinel_hub_provider_inspect_is_not_implemented_yet() -> None:
    provider = SentinelHubProvider(
        config=SentinelHubConfig(
            client_id="test-client-id",
            client_secret="test-client-secret",
        )
    )
    request = InspectionRequest(
        aoi=VALID_POLYGON,
        date_from=date(2025, 6, 1),
        date_to=date(2025, 6, 30),
    )

    with pytest.raises(
        NotImplementedError,
        match="Sentinel Hub candidate search is not implemented yet",
    ):
        provider.inspect(request)
