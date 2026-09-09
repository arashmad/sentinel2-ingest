import importlib


def test_installed_package_is_importable() -> None:
    package = importlib.import_module("sentinel2_ingest")

    assert package.__name__ == "sentinel2_ingest"
