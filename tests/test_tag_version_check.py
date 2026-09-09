import subprocess
import sys
from pathlib import Path


CHECK_SCRIPT = Path(__file__).parents[1] / "scripts" / "check_tag_version.py"


def run_version_check(tag: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK_SCRIPT), tag],
        capture_output=True,
        check=False,
        text=True,
    )


def test_version_check_accepts_matching_release_tag() -> None:
    result = run_version_check("v0.1.0")

    assert result.returncode == 0, result.stderr
    assert result.stdout == "sentinel2-ingest 0.1.0 matches tag v0.1.0\n"


def test_version_check_rejects_mismatched_release_tag() -> None:
    result = run_version_check("v9.9.9")

    assert result.returncode == 1
    assert result.stderr == (
        "tag v9.9.9 does not match sentinel2-ingest 0.1.0\n"
    )
