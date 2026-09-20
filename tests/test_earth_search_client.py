"""Offline request-construction tests for the Element 84 STAC client."""

from collections.abc import Mapping

import pytest

from sentinel2_ingest.providers import EarthSearchClient
from sentinel2_ingest.requests import InspectionRequest


class RecordingStacClient:
    """In-memory STAC client double that records the submitted search."""

    def __init__(self, response: object) -> None:
        self.response = response
        self.search_kwargs: Mapping[str, object] | None = None

    def search(self, **kwargs: object) -> object:
        self.search_kwargs = kwargs
        return self.response


def test_earth_search_client_submits_the_normalized_anonymous_stac_request() -> None:
    """A changed catalog filter, interval, or endpoint client request is a bug."""
    response = object()
    client = RecordingStacClient(response)
    earth_search = EarthSearchClient(client)
    request = InspectionRequest(
        {
            "type": "Polygon",
            "coordinates": [[[10, 45], [11, 45], [11, 46], [10, 46], [10, 45]]],
        },
        "2024-01-01",
        "2024-01-31",
        max_cloud_cover=20,
        candidate_limit=3,
    )

    assert earth_search.search(request) is response
    assert client.search_kwargs == {
        "method": "POST",
        "collections": ["sentinel-2-c1-l2a"],
        "intersects": {
            "type": "Polygon",
            "coordinates": [
                [[10.0, 45.0], [11.0, 45.0], [11.0, 46.0], [10.0, 46.0], [10.0, 45.0]]
            ],
        },
        "datetime": "2024-01-01T00:00:00Z/2024-01-31T23:59:59Z",
        "query": {"eo:cloud_cover": {"lte": 20.0}},
        "sortby": [
            {"field": "properties.datetime", "direction": "desc"},
            {"field": "id", "direction": "asc"},
        ],
        "limit": 3,
    }


def test_earth_search_client_opens_the_public_element84_catalog_anonymously(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Changing the endpoint or adding credentials would break public catalog use."""
    opened_urls: list[str] = []
    client = RecordingStacClient(object())

    def open_client(url: str) -> RecordingStacClient:
        opened_urls.append(url)
        return client

    monkeypatch.setattr("sentinel2_ingest.providers.Client.open", open_client)

    earth_search = EarthSearchClient.open_anonymous()

    assert earth_search.client is client
    assert opened_urls == ["https://earth-search.aws.element84.com/v1/"]
