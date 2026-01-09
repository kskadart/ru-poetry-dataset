from typing import Dict, Tuple

import pandas as pd

from src.consts import AUTHOR_MAPPING
from src.normalizers import (
    normalize_author,
    normalize_poem_name,
    normalize_poem_name_for_dedup,
    normalize_text_for_comparison,
)


def validate_no_empty_fields(df: pd.DataFrame) -> int:
    """
    Check for rows with empty required fields (author, poem_name, text).

    Returns count of rows with empty fields.
    """
    empty_author = df["author"].isna() | (df["author"].str.strip() == "")
    empty_name = df["poem_name"].isna() | (df["poem_name"].str.strip() == "")
    empty_text = df["text"].isna() | (df["text"].str.strip() == "")
    return int((empty_author | empty_name | empty_text).sum())


def validate_no_text_duplicates(df: pd.DataFrame) -> int:
    """
    Check for duplicate poems based on text content.

    Returns count of duplicate rows.
    """
    return int(df.duplicated(subset=["text"], keep=False).sum())


def validate_no_author_poem_duplicates(df: pd.DataFrame) -> int:
    """
    Check for duplicate author+poem_name combinations.

    Returns count of duplicate rows.
    """
    return int(df.duplicated(subset=["author", "poem_name"], keep=False).sum())


def validate_author_format(df: pd.DataFrame) -> int:
    """
    Check for authors not in canonical format (Фамилия Имя Отчество).

    Returns count of authors that might need normalization.
    """
    unmapped = 0
    for author in df["author"].unique():
        if author not in AUTHOR_MAPPING.values() and author not in AUTHOR_MAPPING:
            unmapped += 1
    return unmapped


def validate_poem_name_format(df: pd.DataFrame) -> Tuple[int, int]:
    """
    Check poem name formatting issues.

    Returns tuple of (trailing_dots_count, uppercase_count).
    """
    trailing = int(df["poem_name"].str.endswith("...", na=False).sum())
    uppercase = int(df["poem_name"].str.isupper().sum())
    return trailing, uppercase


def validate_and_fix_dataset(input_path: str, output_path: str) -> Dict[str, int]:
    """
    Validate and fix the merged poems dataset.

    Steps:
    1. Normalize author names to canonical format
    2. Normalize poem names (remove trailing dots, fix UPPERCASE)
    3. Remove duplicates by normalized text content
    4. Remove duplicates by author + normalized poem name
    5. Sort by author and poem name
    6. Save cleaned dataset

    Returns statistics dictionary.
    """
    df = pd.read_csv(input_path)

    stats = {
        "original_rows": len(df),
        "original_unique_authors": df["author"].nunique(),
    }

    df["author"] = df["author"].apply(normalize_author)
    stats["normalized_unique_authors"] = df["author"].nunique()

    df["poem_name"] = df["poem_name"].apply(normalize_poem_name)

    df["text_normalized"] = df["text"].apply(normalize_text_for_comparison)
    df["poem_name_normalized"] = df["poem_name"].apply(normalize_poem_name_for_dedup)

    duplicates_before = df[df.duplicated(subset=["text_normalized"], keep=False)]
    stats["duplicates_by_text_before"] = len(duplicates_before)

    df = df.drop_duplicates(subset=["text_normalized"], keep="first")
    df = df.drop_duplicates(subset=["author", "poem_name_normalized"], keep="first")
    df = df.drop(columns=["text_normalized", "poem_name_normalized"])

    stats["rows_after_dedup"] = len(df)
    stats["removed_duplicates"] = stats["original_rows"] - stats["rows_after_dedup"]

    duplicates_after = df[df.duplicated(subset=["text"], keep=False)]
    stats["duplicates_by_text_after"] = len(duplicates_after)

    df = df.sort_values(by=["author", "poem_name"]).reset_index(drop=True)
    df.to_csv(output_path, index=False)

    return stats


def print_validation_report(df: pd.DataFrame) -> None:
    """Print a validation report for the dataset."""
    print("=== DATASET VALIDATION REPORT ===")
    print(f"Total rows: {len(df)}")
    print(f"Unique authors: {df['author'].nunique()}")
    print()

    empty_count = validate_no_empty_fields(df)
    print(f"Empty fields: {empty_count}")

    text_dups = validate_no_text_duplicates(df)
    print(f"Text duplicates: {text_dups}")

    name_dups = validate_no_author_poem_duplicates(df)
    print(f"Author+poem_name duplicates: {name_dups}")

    trailing, uppercase = validate_poem_name_format(df)
    print(f"Trailing '...' in names: {trailing}")
    print(f"UPPERCASE names: {uppercase}")

    print()
    if empty_count == 0 and text_dups == 0 and name_dups == 0:
        print("VALIDATION PASSED: Dataset is clean!")
    else:
        print("VALIDATION FAILED: Issues found.")
