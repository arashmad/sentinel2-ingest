"""Verify that a release tag matches the installed package version."""

import sys
from argparse import ArgumentParser

from sentinel2_ingest import __version__


def main() -> int:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("tag", help="release tag in vX.Y.Z form")
    tag = parser.parse_args().tag
    expected_tag = f"v{__version__}"

    if tag != expected_tag:
        print(
            f"tag {tag} does not match sentinel2-ingest {__version__}",
            file=sys.stderr,
        )
        return 1

    print(f"sentinel2-ingest {__version__} matches tag {tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
