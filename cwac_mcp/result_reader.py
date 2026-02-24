"""Reads and parses CWAC result CSV files.

Provides functions to:
* Read individual audit result CSVs with optional filtering.
* Generate a summary across all audit types in a results directory.
* List all available result directories.

Uses only the ``csv`` module from the standard library to avoid adding a
hard dependency on pandas.
"""

import csv
import os
from datetime import datetime
from typing import Optional

from cwac_mcp import CWAC_PATH

_RESULTS_ROOT = os.path.join(CWAC_PATH, "results")


def read_results(
    results_dir: str,
    audit_type: Optional[str] = None,
    impact: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[dict]:
    """Read rows from one or more CWAC result CSVs.

    Args:
        results_dir: Absolute path to the scan's results directory
            (e.g. ``/workspaces/cwac/results/2026-02-24_14-30-00_my_audit``).
        audit_type: If provided, read only the CSV for this audit type.
            For example, ``"axe_core_audit"`` reads ``axe_core_audit.csv``.
            When ``None``, all CSVs in the directory are read.
        impact: If provided and the CSV contains an ``impact`` column,
            only rows whose ``impact`` value matches (case-insensitive) are
            returned.
        limit: If provided, return at most this many rows.

    Returns:
        A list of dicts, one per CSV row.  Keys are the column headers.
        Returns an empty list when the directory or file does not exist.
    """
    if not os.path.isdir(results_dir):
        return []

    csv_files = _resolve_csv_files(results_dir, audit_type)
    rows: list[dict] = []

    for csv_path in csv_files:
        file_rows = _read_csv_file(csv_path)

        # Apply impact filter if requested and column exists.
        if impact and file_rows:
            if "impact" in file_rows[0]:
                impact_lower = impact.lower()
                file_rows = [
                    r for r in file_rows
                    if r.get("impact", "").lower() == impact_lower
                ]

        rows.extend(file_rows)

        # Short-circuit if we already have enough rows.
        if limit is not None and len(rows) >= limit:
            break

    if limit is not None:
        rows = rows[:limit]

    return rows


def get_summary(results_dir: str) -> dict:
    """Generate a summary of all audit results in a scan directory.

    The returned dict has the structure::

        {
            "total_issues": int,
            "by_audit_type": {
                "axe_core_audit": int,
                "language_audit": int,
                ...
            },
            "axe_impact_breakdown": {       # only if axe_core_audit.csv exists
                "critical": int,
                "serious": int,
                "moderate": int,
                "minor": int,
            },
            "top_violations": [             # only if axe_core_audit.csv exists
                {"id": "color-contrast", "count": 42},
                ...
            ]
        }

    Args:
        results_dir: Absolute path to the scan's results directory.

    Returns:
        A structured summary dict.  Returns a dict with zero counts if the
        directory does not exist or contains no CSVs.
    """
    summary: dict = {
        "total_issues": 0,
        "by_audit_type": {},
    }

    if not os.path.isdir(results_dir):
        return summary

    csv_files = _resolve_csv_files(results_dir, audit_type=None)

    for csv_path in csv_files:
        audit_key = os.path.splitext(os.path.basename(csv_path))[0]
        rows = _read_csv_file(csv_path)
        count = len(rows)
        summary["by_audit_type"][audit_key] = count
        summary["total_issues"] += count

        # Axe-specific breakdowns.
        if audit_key == "axe_core_audit" and rows:
            summary["axe_impact_breakdown"] = _count_by_field(rows, "impact")
            summary["top_violations"] = _top_n_by_field(rows, "id", n=10)

    return summary


def list_scan_results() -> list[dict]:
    """List all result directories under ``/workspaces/cwac/results/``.

    Returns:
        A list of dicts sorted by ``modified_time`` (most recent first),
        each containing:

        * ``name`` -- directory name
        * ``path`` -- absolute path
        * ``modified_time`` -- ISO-8601 formatted modification timestamp

        Returns an empty list if the results root does not exist.
    """
    if not os.path.isdir(_RESULTS_ROOT):
        return []

    entries: list[dict] = []
    try:
        for entry in os.scandir(_RESULTS_ROOT):
            if entry.is_dir():
                stat = entry.stat()
                entries.append({
                    "name": entry.name,
                    "path": entry.path,
                    "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
    except OSError:
        return []

    entries.sort(key=lambda e: e["modified_time"], reverse=True)
    return entries


# ---------------------------------------------------------------------- #
# Internal helpers
# ---------------------------------------------------------------------- #


def _resolve_csv_files(results_dir: str, audit_type: Optional[str]) -> list[str]:
    """Return a list of CSV file paths to read.

    Args:
        results_dir: The results directory to scan.
        audit_type: If given, restrict to that single CSV; otherwise return
            all ``.csv`` files in the directory.

    Returns:
        A list of absolute paths to CSV files.  May be empty.
    """
    if audit_type:
        target = os.path.join(results_dir, f"{audit_type}.csv")
        return [target] if os.path.isfile(target) else []

    try:
        return sorted(
            os.path.join(results_dir, f)
            for f in os.listdir(results_dir)
            if f.endswith(".csv")
        )
    except OSError:
        return []


def _read_csv_file(csv_path: str) -> list[dict]:
    """Read a single CSV file into a list of dicts.

    Uses ``csv.DictReader`` so that each row is keyed by the header.
    Handles missing files and encoding issues gracefully.

    Args:
        csv_path: Absolute path to the CSV file.

    Returns:
        A list of row dicts.  Empty list on any read error.
    """
    if not os.path.isfile(csv_path):
        return []

    try:
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            return list(reader)
    except (OSError, csv.Error, UnicodeDecodeError):
        return []


def _count_by_field(rows: list[dict], field: str) -> dict[str, int]:
    """Count occurrences of each unique value in *field*.

    Args:
        rows: List of row dicts.
        field: The column name to group by.

    Returns:
        A dict mapping field values to their counts.
    """
    counts: dict[str, int] = {}
    for row in rows:
        value = row.get(field, "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _top_n_by_field(rows: list[dict], field: str, n: int = 10) -> list[dict]:
    """Return the top *n* most frequent values for *field*.

    Args:
        rows: List of row dicts.
        field: The column name to count.
        n: Number of top entries to return.

    Returns:
        A list of ``{"id": value, "count": int}`` dicts sorted by count
        descending.
    """
    counts = _count_by_field(rows, field)
    sorted_counts = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return [{"id": value, "count": count} for value, count in sorted_counts[:n]]
