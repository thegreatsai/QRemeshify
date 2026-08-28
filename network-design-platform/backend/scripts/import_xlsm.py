#!/usr/bin/env python3
"""CLI: import reference data (and optionally site identity) from a site .xlsm.

Usage:
    python scripts/import_xlsm.py path/to/site.xlsm --name "PS 273" --district 27
    python scripts/import_xlsm.py path/to/site.xlsm --reference-only
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal  # noqa: E402
from app.importer.xlsm_importer import import_reference_lists, import_site  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xlsm_path", type=Path)
    parser.add_argument("--name", help="Site name (required unless --reference-only)")
    parser.add_argument("--district", default=None)
    parser.add_argument(
        "--reference-only", action="store_true", help="Only import Data Lists, skip site identity"
    )
    args = parser.parse_args()

    if not args.reference_only and not args.name:
        parser.error("--name is required unless --reference-only is set")

    db = SessionLocal()
    try:
        counts = import_reference_lists(args.xlsm_path, db)
        print("Reference lists imported (new items per list):")
        for key, added in sorted(counts.items()):
            print(f"  {key}: +{added}")

        if not args.reference_only:
            site = import_site(args.xlsm_path, db, name=args.name, district=args.district)
            print(f"Site imported: {site.building_code} (rack {site.rack_id}) -> id={site.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
