import sentinel2_ingest


def test_package_imports() -> None:
    assert sentinel2_ingest.hello() == "Hello from sentinel2-ingest!"