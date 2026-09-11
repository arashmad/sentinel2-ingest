"""Public exception contract tests."""

import pytest

import sentinel2_ingest

PUBLIC_ERROR_NAMES = (
    "InvalidAOIError",
    "InvalidDateError",
    "InvalidBandError",
    "InvalidResolutionError",
    "ProviderRequestError",
    "NoCandidatesFoundError",
    "UnacceptableCandidateError",
    "OutputError",
)


@pytest.mark.parametrize(
    "error_name",
    PUBLIC_ERROR_NAMES,
)
def test_public_errors_inherit_from_package_base(
    error_name: str,
) -> None:
    error_type = getattr(sentinel2_ingest, error_name, None)
    base_error = getattr(sentinel2_ingest, "Sentinel2IngestError", None)

    assert error_type is not None
    assert base_error is not None
    assert issubclass(error_type, base_error)


@pytest.mark.parametrize(
    ("error_name", "details", "message"),
    [
        (
            "InvalidAOIError",
            "polygon is self-intersecting",
            "Invalid area of interest: polygon is self-intersecting.",
        ),
        (
            "InvalidDateError",
            "end precedes start",
            "Invalid dates: end precedes start.",
        ),
        (
            "InvalidBandError",
            "B13 is unavailable",
            "Invalid bands: B13 is unavailable.",
        ),
        (
            "InvalidResolutionError",
            "12 m is unsupported",
            "Invalid resolution: 12 m is unsupported.",
        ),
        (
            "ProviderRequestError",
            None,
            "Unable to retrieve Sentinel-2 candidates from the provider.",
        ),
        ("NoCandidatesFoundError", None, "No Sentinel-2 candidates were found."),
        (
            "UnacceptableCandidateError",
            "cloud cover exceeds 20%",
            "No acceptable Sentinel-2 candidates: cloud cover exceeds 20%.",
        ),
        ("OutputError", None, "Unable to produce the requested output."),
    ],
)
def test_public_errors_provide_actionable_messages(
    error_name: str,
    details: str | None,
    message: str,
) -> None:
    error_type = getattr(sentinel2_ingest, error_name)
    error = error_type() if details is None else error_type(details)

    assert str(error) == message


def test_provider_error_can_preserve_cause_without_exposing_its_details() -> None:
    provider_failure = RuntimeError("provider endpoint https://secret.example failed")
    provider_error = sentinel2_ingest.ProviderRequestError

    with pytest.raises(provider_error) as raised:
        try:
            raise provider_failure
        except RuntimeError as cause:
            raise provider_error() from cause

    assert str(raised.value) == (
        "Unable to retrieve Sentinel-2 candidates from the provider."
    )
    assert raised.value.__cause__ is provider_failure
