import importlib
from importlib.metadata import version


def test_installed_package_is_importable() -> None:
    package = importlib.import_module("sentinel2_ingest")

    assert package.__name__ == "sentinel2_ingest"


def test_exports_installed_distribution_version() -> None:
    package = importlib.import_module("sentinel2_ingest")

    assert package.__version__ == version("sentinel2-ingest")
