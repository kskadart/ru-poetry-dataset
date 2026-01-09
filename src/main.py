import argparse
import sys
from typing import Iterable, Optional

import pandas as pd

from src.consts import OUTPUT_CSV, POEMS_CSV, REPORT_EVERY, THEMED_CSV
from src.merge import merge_datasets
from src.validators import print_validation_report, validate_and_fix_dataset


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Merge and validate poem datasets into a single clean CSV."
    )
    parser.add_argument(
        "-v", "--validate-only",
        action="store_true",
        help="Only validate existing merged_poems.csv without re-merging",
    )
    ns = parser.parse_args(list(argv) if argv is not None else None)
    return ns


def main(argv: Optional[Iterable[str]] = None) -> None:
    """Main entry point for the merge/validation CLI."""
    ns = parse_args(argv)

    if ns.validate_only:
        if not OUTPUT_CSV.exists():
            raise FileNotFoundError(f"Cannot validate: {OUTPUT_CSV} does not exist")
        df = pd.read_csv(OUTPUT_CSV)
        print_validation_report(df)
        return

    if not POEMS_CSV.exists():
        raise FileNotFoundError(f"Missing poems CSV: {POEMS_CSV}")
    if not THEMED_CSV.exists():
        raise FileNotFoundError(f"Missing themed CSV: {THEMED_CSV}")

    merge_stats = merge_datasets(
        poems_csv=POEMS_CSV,
        themed_csv=THEMED_CSV,
        output_csv=OUTPUT_CSV,
        report_every=REPORT_EVERY,
    )
    print(
        f"Merged. written={merge_stats['written']} dup={merge_stats['skipped_duplicate']} "
        f"empty={merge_stats['skipped_empty']} read_total={merge_stats['read_total']}",
        file=sys.stderr,
    )

    fix_stats = validate_and_fix_dataset(str(OUTPUT_CSV), str(OUTPUT_CSV))
    print(
        f"Fixed. original={fix_stats['original_rows']} final={fix_stats['rows_after_dedup']} "
        f"removed={fix_stats['removed_duplicates']}",
        file=sys.stderr,
    )

    df = pd.read_csv(OUTPUT_CSV)
    print_validation_report(df)


if __name__ == "__main__":
    main()
