"""Offline transport-failure tests for Element 84 scene searches."""

from collections.abc import Iterator, Sequence
from datetime import UTC, datetime

import pytest
from pystac import Item
from pystac_client.exceptions import APIError

from sentinel2_ingest.errors import ProviderRequestError
from sentinel2_ingest.providers import (
    EARTH_SEARCH_CONNECT_TIMEOUT,
    EARTH_SEARCH_READ_TIMEOUT,
    EarthSearchClient,
)
from sentinel2_ingest.requests import InspectionRequest


class EmptyItemSearch:
    """A successful STAC response with no catalog items."""

    def items(self) -> Iterator[Item]:
        return iter(())


class MalformedItemSearch:
    """A response whose item stream cannot be decoded."""

    def items(self) -> Iterator[Item]:
        raise ValueError("malformed STAC item")


class FailingItemSearch:
    """A lazy STAC response that fails only when its items are requested."""

    def __init__(self, error: Exception) -> None:
        self.error = error

    def items(self) -> Iterator[Item]:
        raise self.error


class PagedItemSearch:
    """A local item stream that exposes each page consumed by iteration."""

    def __init__(self, pages: Sequence[Sequence[Item]]) -> None:
        self.pages = pages
        self.pages_consumed = 0

    def items(self) -> Iterator[Item]:
        for page in self.pages:
            self.pages_consumed += 1
            yield from page


class InterruptedItemSearch:
    """A stream that yields an item before a transient page-fetch failure."""

    def __init__(self, item: Item, error: APIError) -> None:
        self.item = item
        self.error = error

    def items(self) -> Iterator[Item]:
        yield self.item
        raise self.error


class ScriptedStacClient:
    """A local STAC client that returns or raises scripted search outcomes."""

    def __init__(self, outcomes: Sequence[object]) -> None:
        self.outcomes = iter(outcomes)
        self.calls = 0

    def search(self, **_: object) -> object:
        self.calls += 1
        outcome = next(self.outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _request(candidate_limit: int = 20) -> InspectionRequest:
    return InspectionRequest(
        {
            "type": "Polygon",
            "coordinates": [[[10, 45], [11, 45], [11, 46], [10, 46], [10, 45]]],
        },
        "2024-01-01",
        "2024-01-31",
        candidate_limit=candidate_limit,
    )


def _api_error(status_code: int) -> APIError:
    error = APIError(f"HTTP {status_code}")
    error.status_code = status_code
    return error


def _stream_item(scene_id: str) -> Item:
    return Item(
        id=scene_id,
        geometry=None,
        bbox=None,
        datetime=datetime(2024, 1, 1, tzinfo=UTC),
        properties={},
    )


def test_search_scenes_retries_a_transient_failure_without_real_sleep() -> None:
    """A retryable catalog failure must recover using the injected delay function."""
    client = ScriptedStacClient((_api_error(503), EmptyItemSearch()))
    delays: list[float] = []

    assert (
        EarthSearchClient(client, sleep=delays.append).search_scenes(_request()) == ()
    )
    assert client.calls == 2
    assert delays == [0.25]


def test_search_retries_a_deferred_transient_failure_at_its_public_boundary() -> None:
    """Lazy STAC iteration must receive the same bounded failure behavior."""
    response = EmptyItemSearch()
    client = ScriptedStacClient((FailingItemSearch(_api_error(503)), response))
    delays: list[float] = []

    assert (
        tuple(EarthSearchClient(client, sleep=delays.append).search(_request()).items())
        == ()
    )
    assert client.calls == 2
    assert delays == [0.25]


def test_search_yields_the_first_page_before_reading_later_pages() -> None:
    """A lazy public stream must not materialize every STAC page before yielding."""
    item_search = PagedItemSearch(((_stream_item("first"),), (_stream_item("second"),)))
    client = ScriptedStacClient((item_search,))

    item_stream = EarthSearchClient(client, sleep=lambda _: None).search(_request())
    first = next(item_stream.items())

    assert first.id == "first"
    assert item_search.pages_consumed == 1


def test_search_skips_replayed_items_after_a_transient_stream_failure() -> None:
    """Retrying a later page must not replay IDs already yielded to the caller."""
    first = _stream_item("first")
    second = _stream_item("second")
    client = ScriptedStacClient(
        (
            InterruptedItemSearch(first, _api_error(503)),
            PagedItemSearch(((first, second),)),
        )
    )
    delays: list[float] = []

    items = tuple(
        EarthSearchClient(client, sleep=delays.append).search(_request(2)).items()
    )

    assert [item.id for item in items] == ["first", "second"]
    assert client.calls == 2
    assert delays == [0.25]


def test_search_scenes_maps_exhausted_transient_failures_with_their_cause() -> None:
    """More than three retries must not occur after persistent catalog failure."""
    failures = tuple(_api_error(503) for _ in range(4))
    client = ScriptedStacClient(failures)
    delays: list[float] = []

    with pytest.raises(ProviderRequestError) as raised:
        EarthSearchClient(client, sleep=delays.append).search_scenes(_request())

    assert client.calls == 4
    assert delays == [0.25, 0.5, 1.0]
    assert raised.value.__cause__ is failures[-1]


def test_search_scenes_does_not_retry_permanent_client_failures() -> None:
    """A permanent 4xx response must map immediately without a retry delay."""
    failure = _api_error(400)
    client = ScriptedStacClient((failure,))
    delays: list[float] = []

    with pytest.raises(ProviderRequestError) as raised:
        EarthSearchClient(client, sleep=delays.append).search_scenes(_request())

    assert client.calls == 1
    assert delays == []
    assert raised.value.__cause__ is failure


def test_search_scenes_maps_malformed_item_streams_without_retrying() -> None:
    """Malformed catalog responses must become public provider failures directly."""
    client = ScriptedStacClient((MalformedItemSearch(),))

    with pytest.raises(ProviderRequestError, match="Unable to retrieve") as raised:
        EarthSearchClient(client, sleep=lambda _: None).search_scenes(_request())

    assert client.calls == 1
    assert isinstance(raised.value.__cause__, ValueError)


def test_open_anonymous_configures_separate_connection_and_read_timeouts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unbounded default transport timeouts would leave catalog calls hanging."""
    opened_stac_io: list[object] = []
    client = ScriptedStacClient((EmptyItemSearch(),))

    def open_client(*_: object, stac_io: object) -> ScriptedStacClient:
        opened_stac_io.append(stac_io)
        return client

    monkeypatch.setattr("sentinel2_ingest.providers.Client.open", open_client)

    assert EarthSearchClient.open_anonymous(sleep=lambda _: None).client is client
    assert len(opened_stac_io) == 1
    assert opened_stac_io[0].timeout == (
        EARTH_SEARCH_CONNECT_TIMEOUT,
        EARTH_SEARCH_READ_TIMEOUT,
    )
