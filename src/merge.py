import csv
import hashlib
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional, Tuple

from src.consts import Row


def configure_csv_field_size_limit() -> None:
    """Increase the CSV parser field size limit to support very large text fields."""
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit = int(limit // 10)


def collapse_ws(value: str) -> str:
    """Collapse multiple whitespace characters to single space."""
    return " ".join(value.split())


def normalize_key(author: str, poem_name: str, text: str) -> Tuple[str, str, str]:
    """Normalize key for deduplication hash."""
    return (
        collapse_ws(author).casefold(),
        collapse_ws(poem_name).casefold(),
        collapse_ws(text).casefold(),
    )


def row_hash(row: Row) -> str:
    """Generate SHA1 hash for a row based on normalized content."""
    a, p, t = normalize_key(row.author, row.poem_name, row.text)
    payload = "\n".join((a, p, t)).encode("utf-8")
    return hashlib.sha1(payload).hexdigest()


def is_empty(value: Optional[str]) -> bool:
    """Check if a value is empty or only whitespace."""
    if value is None:
        return True
    return collapse_ws(value) == ""


def iter_rows_poems_csv(csv_path: Path) -> Iterator[Row]:
    """
    Iterator for poems.csv format.

    Expected columns: writer, poem, text
    """
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            author = raw.get("writer") or ""
            poem_name = raw.get("poem") or ""
            text = raw.get("text") or ""
            yield Row(
                author=collapse_ws(author),
                poem_name=collapse_ws(poem_name),
                text=text.strip(),
            )


def iter_rows_russian_poetry_with_theme(csv_path: Path) -> Iterator[Row]:
    """
    Iterator for russianPoetryWithTheme.csv format.

    Expected columns: author, name, text
    """
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            author = raw.get("author") or ""
            poem_name = raw.get("name") or ""
            text = raw.get("text") or ""
            yield Row(
                author=collapse_ws(author),
                poem_name=collapse_ws(poem_name),
                text=text.strip(),
            )


def ensure_db(conn: sqlite3.Connection) -> None:
    """Initialize SQLite database for deduplication."""
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS seen (
            h TEXT PRIMARY KEY
        )
        """.strip()
    )
    conn.commit()


def merge_datasets(
    poems_csv: Path,
    themed_csv: Path,
    output_csv: Path,
    sqlite_path: Optional[Path] = None,
    report_every: int = 200_000,
) -> Dict[str, int]:
    """
    Merge two poem CSV files into a single deduplicated CSV.

    Args:
        poems_csv: Path to poems.csv
        themed_csv: Path to russianPoetryWithTheme.csv
        output_csv: Output path for merged CSV
        sqlite_path: Path for SQLite dedup database (optional)
        report_every: Print progress every N rows (0 disables)

    Returns:
        Dictionary with statistics (read_total, written, skipped_empty, skipped_duplicate)
    """
    configure_csv_field_size_limit()
    if sqlite_path is None:
        sqlite_path = output_csv.with_suffix(".dedup.sqlite3")

    output_csv.parent.mkdir(parents=True, exist_ok=True)

    counters = {
        "read_total": 0,
        "written": 0,
        "skipped_empty": 0,
        "skipped_duplicate": 0,
    }

    conn = sqlite3.connect(str(sqlite_path))
    try:
        ensure_db(conn)
        with output_csv.open("w", encoding="utf-8", newline="") as out_f:
            writer = csv.DictWriter(out_f, fieldnames=["author", "poem_name", "text"])
            writer.writeheader()

            def handle_source(source_name: str, it: Iterable[Row]) -> None:
                nonlocal counters
                batch = 0
                for row in it:
                    counters["read_total"] += 1
                    if is_empty(row.author) or is_empty(row.poem_name) or is_empty(row.text):
                        counters["skipped_empty"] += 1
                        continue
                    h = row_hash(row)
                    cur = conn.execute("INSERT OR IGNORE INTO seen(h) VALUES (?)", (h,))
                    if cur.rowcount == 0:
                        counters["skipped_duplicate"] += 1
                    else:
                        writer.writerow({
                            "author": row.author,
                            "poem_name": row.poem_name,
                            "text": row.text,
                        })
                        counters["written"] += 1
                    batch += 1
                    if batch >= 10_000:
                        conn.commit()
                        batch = 0
                    if report_every > 0 and counters["read_total"] % report_every == 0:
                        print(
                            f"[{source_name}] read={counters['read_total']} written={counters['written']} "
                            f"dup={counters['skipped_duplicate']} empty={counters['skipped_empty']}",
                            file=sys.stderr,
                        )
                if batch:
                    conn.commit()

            handle_source("poems.csv", iter_rows_poems_csv(poems_csv))
            handle_source("russianPoetryWithTheme.csv", iter_rows_russian_poetry_with_theme(themed_csv))
    finally:
        conn.close()

    return counters
