#!/usr/bin/env python3
"""CSV/TSV Data Validator - data-validation skill execution script.

Performs automated CSV/TSV data validation covering structure, data quality,
schema conformance, and custom rule checks. Outputs a JSON report compatible
with the data-validation skill's M-5 report format.

Usage:
    python validate_csv.py <file_path> [--schema schema.json] [--rules rules.json] [--output report.json]

Examples:
    # Basic validation (structure + data quality)
    python validate_csv.py data.csv

    # With schema validation
    python validate_csv.py data.csv --schema schema.json

    # With custom rules
    python validate_csv.py data.csv --rules rules.json --output report.json

    # TSV file with strict mode
    python validate_csv.py data.tsv --delimiter tab --severity strict
"""

from __future__ import annotations

import argparse
import codecs
import csv
import json
import re
import statistics
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEVERITY_LEVELS: list[str] = ["Critical", "Major", "Minor", "Info"]

# Common date patterns for auto-detection
DATE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("ISO-8601", re.compile(r"^\d{4}-\d{2}-\d{2}$")),
    ("JP-slash", re.compile(r"^\d{4}/\d{2}/\d{2}$")),
    ("JP-era", re.compile(r"^(令和|平成|昭和)\d{1,2}年\d{1,2}月\d{1,2}日$")),
    ("US-slash", re.compile(r"^\d{2}/\d{2}/\d{4}$")),
    ("EU-dot", re.compile(r"^\d{2}\.\d{2}\.\d{4}$")),
]

# Numeric pattern (supports Japanese comma-separated and decimal)
NUMERIC_PATTERN: re.Pattern[str] = re.compile(
    r"^[+-]?[\d,]+\.?\d*$|^[+-]?\d*\.?\d+$"
)

# Email pattern (simple)
EMAIL_PATTERN: re.Pattern[str] = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)

# IQR multiplier for outlier detection
IQR_MULTIPLIER: float = 1.5

# Maximum rows to show in detail for each issue
MAX_DETAIL_ROWS: int = 10


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Issue:
    """A single validation issue."""

    issue_id: int
    severity: str
    category: str
    message: str
    location: str
    impact: str
    suggestion: str
    detail_rows: list[int] = field(default_factory=list)


@dataclass
class ColumnProfile:
    """Profile of a single column."""

    name: str
    index: int
    inferred_type: str
    total_count: int
    non_null_count: int
    null_count: int
    null_rate: float
    unique_count: int
    cardinality: float
    top_values: list[tuple[str, int]]
    # Numeric stats (None if not numeric)
    min_value: float | None = None
    max_value: float | None = None
    mean_value: float | None = None
    median_value: float | None = None
    stddev_value: float | None = None


@dataclass
class ValidationReport:
    """Complete validation report."""

    meta: dict[str, Any]
    summary: dict[str, Any]
    column_profiles: list[dict[str, Any]]
    issues: list[dict[str, Any]]
    recommendations: list[str]


# ---------------------------------------------------------------------------
# BOM detection and file reading
# ---------------------------------------------------------------------------


def detect_encoding(file_path: Path) -> str:
    """Detect file encoding by checking for BOM markers.

    Args:
        file_path: Path to the file.

    Returns:
        Detected encoding string (e.g. 'utf-8-sig', 'utf-8').
    """
    with open(file_path, "rb") as f:
        raw = f.read(4)

    if raw.startswith(codecs.BOM_UTF8):
        return "utf-8-sig"
    if raw.startswith(codecs.BOM_UTF16_LE):
        return "utf-16-le"
    if raw.startswith(codecs.BOM_UTF16_BE):
        return "utf-16-be"

    # Try UTF-8, fall back to cp932 (Shift_JIS superset common in Japan)
    try:
        with open(file_path, encoding="utf-8") as f:
            f.read(4096)
        return "utf-8"
    except UnicodeDecodeError:
        return "cp932"


def detect_delimiter(file_path: Path, encoding: str) -> str:
    """Auto-detect the delimiter by inspecting the first few lines.

    Args:
        file_path: Path to the file.
        encoding: File encoding.

    Returns:
        Detected delimiter character.
    """
    with open(file_path, encoding=encoding, newline="") as f:
        sample = f.read(8192)

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
        return dialect.delimiter
    except csv.Error:
        # Default to comma
        return ","


def read_csv_data(
    file_path: Path,
    encoding: str,
    delimiter: str,
) -> tuple[list[str], list[list[str]]]:
    """Read CSV/TSV file and return headers and rows.

    Args:
        file_path: Path to the file.
        encoding: File encoding.
        delimiter: Column delimiter.

    Returns:
        Tuple of (headers, rows) where rows is a list of string lists.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    rows: list[list[str]] = []
    with open(file_path, encoding=encoding, newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            rows.append(row)

    if not rows:
        raise ValueError(f"File is empty: {file_path}")

    headers = rows[0]
    data_rows = rows[1:]
    return headers, data_rows


# ---------------------------------------------------------------------------
# Structure validation
# ---------------------------------------------------------------------------


def validate_structure(
    headers: list[str],
    rows: list[list[str]],
    issues: list[Issue],
    issue_counter: list[int],
) -> None:
    """Validate structural integrity of the CSV data.

    Checks: header presence, column count consistency, empty headers.

    Args:
        headers: Column header names.
        rows: Data rows.
        issues: Mutable list to append issues to.
        issue_counter: Single-element list used as a mutable counter.
    """
    expected_cols = len(headers)

    # Check for empty headers
    empty_header_indices = [
        i for i, h in enumerate(headers) if not h.strip()
    ]
    if empty_header_indices:
        issue_counter[0] += 1
        issues.append(Issue(
            issue_id=issue_counter[0],
            severity="Major",
            category="structure",
            message=f"Empty header(s) found at column index: {empty_header_indices}",
            location="Header row",
            impact="Column identification may fail in downstream processing",
            suggestion="Assign meaningful names to all columns",
        ))

    # Check for duplicate headers
    header_counts = Counter(headers)
    duplicates = {h: c for h, c in header_counts.items() if c > 1 and h.strip()}
    if duplicates:
        issue_counter[0] += 1
        issues.append(Issue(
            issue_id=issue_counter[0],
            severity="Major",
            category="structure",
            message=f"Duplicate header names: {duplicates}",
            location="Header row",
            impact="Ambiguous column references in queries and processing",
            suggestion="Rename duplicate columns to unique names",
        ))

    # Check column count consistency
    inconsistent_rows: list[int] = []
    for i, row in enumerate(rows, start=2):  # 1-indexed, header is row 1
        if len(row) != expected_cols:
            inconsistent_rows.append(i)

    if inconsistent_rows:
        severity = "Critical" if len(inconsistent_rows) > len(rows) * 0.01 else "Major"
        issue_counter[0] += 1
        detail = inconsistent_rows[:MAX_DETAIL_ROWS]
        issues.append(Issue(
            issue_id=issue_counter[0],
            severity=severity,
            category="structure",
            message=(
                f"Column count mismatch: expected {expected_cols} columns, "
                f"found {len(inconsistent_rows)} rows with different counts"
            ),
            location=f"Rows: {detail}{'...' if len(inconsistent_rows) > MAX_DETAIL_ROWS else ''}",
            impact="Data alignment errors in downstream processing",
            suggestion="Check for unescaped delimiters or missing values",
            detail_rows=inconsistent_rows,
        ))


# ---------------------------------------------------------------------------
# Data quality validation
# ---------------------------------------------------------------------------


def infer_column_type(values: list[str]) -> str:
    """Infer the data type of a column from its non-empty values.

    Args:
        values: Non-empty string values from the column.

    Returns:
        Inferred type: 'integer', 'float', 'date', 'email', 'boolean', or 'string'.
    """
    if not values:
        return "string"

    sample = values[:1000]  # Sample for performance

    # Check boolean
    bool_values = {"true", "false", "yes", "no", "1", "0", "はい", "いいえ"}
    if all(v.strip().lower() in bool_values for v in sample):
        return "boolean"

    # Check integer
    int_pattern = re.compile(r"^[+-]?[\d,]+$")
    if all(int_pattern.match(v.strip().replace(",", "")) for v in sample):
        return "integer"

    # Check float
    float_pattern = re.compile(r"^[+-]?\d[\d,]*\.\d+$|^[+-]?\.\d+$")
    if all(float_pattern.match(v.strip().replace(",", "")) for v in sample):
        return "float"

    # Check date
    for _name, pattern in DATE_PATTERNS:
        if all(pattern.match(v.strip()) for v in sample):
            return "date"

    # Check email
    if all(EMAIL_PATTERN.match(v.strip()) for v in sample):
        return "email"

    return "string"


def parse_numeric(value: str) -> float | None:
    """Parse a string value as a number, handling comma separators.

    Args:
        value: String value to parse.

    Returns:
        Parsed float or None if not numeric.
    """
    cleaned = value.strip().replace(",", "")
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def profile_column(
    name: str,
    index: int,
    values: list[str],
) -> ColumnProfile:
    """Build a statistical profile of a single column.

    Args:
        name: Column header name.
        index: Column index (0-based).
        values: All values in the column (including empty strings).

    Returns:
        ColumnProfile with statistics.
    """
    total = len(values)
    non_null_values = [v for v in values if v.strip()]
    null_count = total - len(non_null_values)
    null_rate = null_count / total if total > 0 else 0.0
    unique_count = len(set(non_null_values))
    cardinality = unique_count / len(non_null_values) if non_null_values else 0.0

    # Top values
    counter = Counter(non_null_values)
    top_values = counter.most_common(5)

    # Infer type
    inferred_type = infer_column_type(non_null_values)

    # Numeric stats
    min_val = max_val = mean_val = median_val = stddev_val = None
    if inferred_type in ("integer", "float"):
        numeric_values = [
            n for v in non_null_values
            if (n := parse_numeric(v)) is not None
        ]
        if numeric_values:
            min_val = min(numeric_values)
            max_val = max(numeric_values)
            mean_val = statistics.mean(numeric_values)
            median_val = statistics.median(numeric_values)
            if len(numeric_values) >= 2:
                stddev_val = statistics.stdev(numeric_values)

    return ColumnProfile(
        name=name,
        index=index,
        inferred_type=inferred_type,
        total_count=total,
        non_null_count=len(non_null_values),
        null_count=null_count,
        null_rate=round(null_rate, 4),
        unique_count=unique_count,
        cardinality=round(cardinality, 4),
        top_values=top_values,
        min_value=min_val,
        max_value=max_val,
        mean_value=round(mean_val, 4) if mean_val is not None else None,
        median_value=median_val,
        stddev_value=round(stddev_val, 4) if stddev_val is not None else None,
    )


def validate_data_quality(
    headers: list[str],
    rows: list[list[str]],
    issues: list[Issue],
    issue_counter: list[int],
) -> list[ColumnProfile]:
    """Validate data quality: nulls, duplicates, outliers, type consistency.

    Args:
        headers: Column header names.
        rows: Data rows (each row is a list of strings).
        issues: Mutable list to append issues to.
        issue_counter: Single-element list used as a mutable counter.

    Returns:
        List of column profiles.
    """
    num_cols = len(headers)
    profiles: list[ColumnProfile] = []

    # Extract column-wise values
    for col_idx in range(num_cols):
        col_values = [
            row[col_idx] if col_idx < len(row) else ""
            for row in rows
        ]
        profile = profile_column(headers[col_idx], col_idx, col_values)
        profiles.append(profile)

        # Check high null rate
        if profile.null_rate > 0.5:
            issue_counter[0] += 1
            issues.append(Issue(
                issue_id=issue_counter[0],
                severity="Major",
                category="data_quality",
                message=f"Column '{profile.name}' has {profile.null_rate:.1%} null/empty values",
                location=f"Column {col_idx} ('{profile.name}')",
                impact="High missing data rate may compromise analysis accuracy",
                suggestion="Investigate data source or define imputation strategy",
            ))
        elif profile.null_rate > 0.05:
            issue_counter[0] += 1
            issues.append(Issue(
                issue_id=issue_counter[0],
                severity="Minor",
                category="data_quality",
                message=f"Column '{profile.name}' has {profile.null_rate:.1%} null/empty values",
                location=f"Column {col_idx} ('{profile.name}')",
                impact="Some missing data; may affect aggregations",
                suggestion="Review whether nulls are intentional or data collection gaps",
            ))

        # Check low cardinality on potential ID columns
        if "id" in profile.name.lower() and profile.cardinality < 1.0 and profile.non_null_count > 0:
            dup_count = profile.non_null_count - profile.unique_count
            if dup_count > 0:
                issue_counter[0] += 1
                issues.append(Issue(
                    issue_id=issue_counter[0],
                    severity="Critical",
                    category="data_quality",
                    message=f"Potential ID column '{profile.name}' has {dup_count} duplicate values",
                    location=f"Column {col_idx} ('{profile.name}')",
                    impact="Uniqueness violation; may cause data integrity issues",
                    suggestion="Deduplicate or verify that duplicates are intentional",
                ))

        # Outlier detection (IQR method) for numeric columns
        if profile.inferred_type in ("integer", "float") and profile.stddev_value is not None:
            non_null_vals = [v for v in col_values if v.strip()]
            numeric_vals = sorted([
                n for v in non_null_vals
                if (n := parse_numeric(v)) is not None
            ])
            if len(numeric_vals) >= 4:
                q1_idx = len(numeric_vals) // 4
                q3_idx = 3 * len(numeric_vals) // 4
                q1 = numeric_vals[q1_idx]
                q3 = numeric_vals[q3_idx]
                iqr = q3 - q1
                lower_bound = q1 - IQR_MULTIPLIER * iqr
                upper_bound = q3 + IQR_MULTIPLIER * iqr

                outlier_rows: list[int] = []
                for row_idx, v in enumerate(col_values, start=2):
                    n = parse_numeric(v)
                    if n is not None and (n < lower_bound or n > upper_bound):
                        outlier_rows.append(row_idx)

                if outlier_rows:
                    issue_counter[0] += 1
                    detail = outlier_rows[:MAX_DETAIL_ROWS]
                    issues.append(Issue(
                        issue_id=issue_counter[0],
                        severity="Minor",
                        category="data_quality",
                        message=(
                            f"Column '{profile.name}' has {len(outlier_rows)} outliers "
                            f"(IQR method, bounds: [{lower_bound:.2f}, {upper_bound:.2f}])"
                        ),
                        location=f"Rows: {detail}{'...' if len(outlier_rows) > MAX_DETAIL_ROWS else ''}",
                        impact="Outlier values may skew statistical analyses",
                        suggestion="Verify outlier values are correct; consider capping or removal",
                        detail_rows=outlier_rows,
                    ))

    # Check for complete duplicate rows
    row_tuples = [tuple(r) for r in rows]
    row_counts = Counter(row_tuples)
    dup_rows = {t: c for t, c in row_counts.items() if c > 1}
    if dup_rows:
        total_dups = sum(c - 1 for c in dup_rows.values())
        issue_counter[0] += 1
        issues.append(Issue(
            issue_id=issue_counter[0],
            severity="Major",
            category="data_quality",
            message=f"Found {total_dups} complete duplicate rows ({len(dup_rows)} unique patterns)",
            location="Multiple rows",
            impact="Duplicate records may inflate counts and distort analysis",
            suggestion="Deduplicate rows or verify that duplicates are intentional",
        ))

    return profiles


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


def load_schema(schema_path: Path) -> dict[str, Any]:
    """Load and parse a JSON schema file.

    Args:
        schema_path: Path to the schema JSON file.

    Returns:
        Parsed schema dictionary.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        json.JSONDecodeError: If the schema is not valid JSON.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)


def validate_schema(
    headers: list[str],
    rows: list[list[str]],
    schema: dict[str, Any],
    issues: list[Issue],
    issue_counter: list[int],
) -> None:
    """Validate data against a schema definition.

    Schema format: see sample-schema.json for the expected structure.

    Args:
        headers: Column header names.
        rows: Data rows.
        schema: Schema dictionary.
        issues: Mutable list to append issues to.
        issue_counter: Single-element list used as a mutable counter.
    """
    schema_columns: list[dict[str, Any]] = schema.get("columns", [])
    schema_col_names = {col["name"] for col in schema_columns}

    # Check missing columns
    missing_in_data = schema_col_names - set(headers)
    if missing_in_data:
        issue_counter[0] += 1
        issues.append(Issue(
            issue_id=issue_counter[0],
            severity="Critical",
            category="schema",
            message=f"Schema-defined columns missing from data: {sorted(missing_in_data)}",
            location="Header row",
            impact="Required data fields are absent; processing will fail",
            suggestion="Add missing columns or update the schema",
        ))

    # Check extra columns not in schema
    extra_in_data = set(headers) - schema_col_names
    if extra_in_data:
        issue_counter[0] += 1
        issues.append(Issue(
            issue_id=issue_counter[0],
            severity="Info",
            category="schema",
            message=f"Columns in data not defined in schema: {sorted(extra_in_data)}",
            location="Header row",
            impact="Extra columns will be ignored by schema-aware consumers",
            suggestion="Add column definitions to the schema if they are needed",
        ))

    # Validate each schema column
    header_to_idx = {h: i for i, h in enumerate(headers)}

    for col_def in schema_columns:
        col_name = col_def["name"]
        if col_name not in header_to_idx:
            continue  # Already reported as missing above

        col_idx = header_to_idx[col_name]
        col_values = [
            row[col_idx] if col_idx < len(row) else ""
            for row in rows
        ]

        # NOT NULL constraint
        if col_def.get("not_null", False):
            null_rows = [
                i + 2 for i, v in enumerate(col_values) if not v.strip()
            ]
            if null_rows:
                issue_counter[0] += 1
                detail = null_rows[:MAX_DETAIL_ROWS]
                issues.append(Issue(
                    issue_id=issue_counter[0],
                    severity="Critical",
                    category="schema",
                    message=f"NOT NULL constraint violated: column '{col_name}' has {len(null_rows)} null values",
                    location=f"Rows: {detail}{'...' if len(null_rows) > MAX_DETAIL_ROWS else ''}",
                    impact="Required field is empty; data integrity compromised",
                    suggestion="Fill in missing values or correct data source",
                    detail_rows=null_rows,
                ))

        # UNIQUE constraint
        if col_def.get("unique", False):
            non_null = [v for v in col_values if v.strip()]
            dup_count = len(non_null) - len(set(non_null))
            if dup_count > 0:
                issue_counter[0] += 1
                issues.append(Issue(
                    issue_id=issue_counter[0],
                    severity="Critical",
                    category="schema",
                    message=f"UNIQUE constraint violated: column '{col_name}' has {dup_count} duplicate values",
                    location=f"Column '{col_name}'",
                    impact="Uniqueness guarantee broken; may cause key conflicts",
                    suggestion="Remove duplicates or verify data correctness",
                ))

        # Type check
        expected_type = col_def.get("type", "").lower()
        if expected_type:
            non_null_values = [v for v in col_values if v.strip()]
            type_violations = _check_type(non_null_values, expected_type)
            if type_violations:
                issue_counter[0] += 1
                detail_rows = [t[0] for t in type_violations[:MAX_DETAIL_ROWS]]
                issues.append(Issue(
                    issue_id=issue_counter[0],
                    severity="Critical" if len(type_violations) > len(non_null_values) * 0.01 else "Major",
                    category="schema",
                    message=(
                        f"Type mismatch in column '{col_name}': "
                        f"expected '{expected_type}', {len(type_violations)} violations found"
                    ),
                    location=f"Rows: {detail_rows}{'...' if len(type_violations) > MAX_DETAIL_ROWS else ''}",
                    impact="Data type inconsistency may cause processing errors",
                    suggestion="Clean the data to match the expected type or update the schema",
                    detail_rows=[t[0] for t in type_violations],
                ))

        # Range constraints
        min_val = col_def.get("min")
        max_val = col_def.get("max")
        if min_val is not None or max_val is not None:
            range_violations: list[int] = []
            for row_idx, v in enumerate(col_values, start=2):
                n = parse_numeric(v)
                if n is None:
                    continue
                if min_val is not None and n < min_val:
                    range_violations.append(row_idx)
                elif max_val is not None and n > max_val:
                    range_violations.append(row_idx)

            if range_violations:
                issue_counter[0] += 1
                detail = range_violations[:MAX_DETAIL_ROWS]
                range_desc = f"[{min_val}, {max_val}]"
                issues.append(Issue(
                    issue_id=issue_counter[0],
                    severity="Major",
                    category="schema",
                    message=(
                        f"Range constraint violated in column '{col_name}': "
                        f"{len(range_violations)} values outside {range_desc}"
                    ),
                    location=f"Rows: {detail}{'...' if len(range_violations) > MAX_DETAIL_ROWS else ''}",
                    impact="Values outside expected range may indicate data errors",
                    suggestion=f"Verify values are within {range_desc} or adjust the constraint",
                    detail_rows=range_violations,
                ))

        # Pattern (regex) constraint
        pattern_str = col_def.get("pattern")
        if pattern_str:
            try:
                pattern = re.compile(pattern_str)
                pattern_violations: list[int] = []
                for row_idx, v in enumerate(col_values, start=2):
                    if v.strip() and not pattern.match(v.strip()):
                        pattern_violations.append(row_idx)

                if pattern_violations:
                    issue_counter[0] += 1
                    detail = pattern_violations[:MAX_DETAIL_ROWS]
                    issues.append(Issue(
                        issue_id=issue_counter[0],
                        severity="Major",
                        category="schema",
                        message=(
                            f"Pattern constraint violated in column '{col_name}': "
                            f"{len(pattern_violations)} values don't match '{pattern_str}'"
                        ),
                        location=f"Rows: {detail}{'...' if len(pattern_violations) > MAX_DETAIL_ROWS else ''}",
                        impact="Inconsistent format may cause parsing failures downstream",
                        suggestion=f"Ensure values match the pattern: {pattern_str}",
                        detail_rows=pattern_violations,
                    ))
            except re.error:
                issue_counter[0] += 1
                issues.append(Issue(
                    issue_id=issue_counter[0],
                    severity="Info",
                    category="schema",
                    message=f"Invalid regex pattern in schema for column '{col_name}': {pattern_str}",
                    location="Schema definition",
                    impact="Pattern validation was skipped",
                    suggestion="Fix the regex pattern in the schema file",
                ))

        # Enum (allowed values) constraint
        allowed_values = col_def.get("enum")
        if allowed_values is not None:
            allowed_set = set(str(v) for v in allowed_values)
            enum_violations: list[int] = []
            for row_idx, v in enumerate(col_values, start=2):
                if v.strip() and v.strip() not in allowed_set:
                    enum_violations.append(row_idx)

            if enum_violations:
                issue_counter[0] += 1
                detail = enum_violations[:MAX_DETAIL_ROWS]
                issues.append(Issue(
                    issue_id=issue_counter[0],
                    severity="Major",
                    category="schema",
                    message=(
                        f"Enum constraint violated in column '{col_name}': "
                        f"{len(enum_violations)} values not in allowed set"
                    ),
                    location=f"Rows: {detail}{'...' if len(enum_violations) > MAX_DETAIL_ROWS else ''}",
                    impact="Unexpected categorical values may cause downstream errors",
                    suggestion=f"Allowed values: {sorted(allowed_set)}",
                    detail_rows=enum_violations,
                ))


def _check_type(
    values: list[str],
    expected_type: str,
) -> list[tuple[int, str]]:
    """Check that values conform to the expected type.

    Args:
        values: Non-null string values.
        expected_type: Expected type string (integer, float, date, email, boolean).

    Returns:
        List of (row_number, value) tuples that violate the type.
    """
    violations: list[tuple[int, str]] = []
    int_pattern = re.compile(r"^[+-]?[\d,]+$")
    float_pattern = re.compile(r"^[+-]?[\d,]*\.?\d+$")
    bool_values = {"true", "false", "yes", "no", "1", "0", "はい", "いいえ"}

    for i, v in enumerate(values):
        stripped = v.strip()
        if not stripped:
            continue

        row_num = i + 2  # 1-indexed, header is row 1

        if expected_type == "integer":
            if not int_pattern.match(stripped.replace(",", "")):
                violations.append((row_num, stripped))
        elif expected_type == "float":
            if not float_pattern.match(stripped.replace(",", "")):
                violations.append((row_num, stripped))
        elif expected_type == "date":
            matched = any(p.match(stripped) for _, p in DATE_PATTERNS)
            if not matched:
                violations.append((row_num, stripped))
        elif expected_type == "email":
            if not EMAIL_PATTERN.match(stripped):
                violations.append((row_num, stripped))
        elif expected_type == "boolean":
            if stripped.lower() not in bool_values:
                violations.append((row_num, stripped))

    return violations


# ---------------------------------------------------------------------------
# Rule validation
# ---------------------------------------------------------------------------


def load_rules(rules_path: Path) -> dict[str, Any]:
    """Load custom validation rules from a JSON file.

    Args:
        rules_path: Path to the rules JSON file.

    Returns:
        Parsed rules dictionary.

    Raises:
        FileNotFoundError: If the rules file does not exist.
    """
    if not rules_path.exists():
        raise FileNotFoundError(f"Rules file not found: {rules_path}")

    with open(rules_path, encoding="utf-8") as f:
        return json.load(f)


def validate_rules(
    headers: list[str],
    rows: list[list[str]],
    rules: dict[str, Any],
    issues: list[Issue],
    issue_counter: list[int],
) -> None:
    """Validate data against custom rules.

    Rule format:
        {
            "rules": [
                {
                    "name": "rule_name",
                    "column": "column_name",
                    "check": "range|regex|not_null|unique|cross_column",
                    "params": { ... },
                    "severity": "Critical|Major|Minor|Info",
                    "message": "Description"
                }
            ]
        }

    Args:
        headers: Column header names.
        rows: Data rows.
        rules: Rules dictionary.
        issues: Mutable list to append issues to.
        issue_counter: Single-element list used as a mutable counter.
    """
    header_to_idx = {h: i for i, h in enumerate(headers)}

    for rule in rules.get("rules", []):
        rule_name = rule.get("name", "unnamed_rule")
        column = rule.get("column", "")
        check = rule.get("check", "")
        params = rule.get("params", {})
        severity = rule.get("severity", "Major")
        message = rule.get("message", f"Rule '{rule_name}' violated")

        if column and column not in header_to_idx:
            issue_counter[0] += 1
            issues.append(Issue(
                issue_id=issue_counter[0],
                severity="Info",
                category="rule",
                message=f"Rule '{rule_name}' references non-existent column '{column}'",
                location="Rule definition",
                impact="Rule was skipped",
                suggestion="Fix the column name in the rules file",
            ))
            continue

        col_idx = header_to_idx.get(column, -1)
        col_values = [
            row[col_idx] if col_idx >= 0 and col_idx < len(row) else ""
            for row in rows
        ]

        violation_rows: list[int] = []

        if check == "range":
            min_v = params.get("min")
            max_v = params.get("max")
            for row_idx, v in enumerate(col_values, start=2):
                n = parse_numeric(v)
                if n is None:
                    continue
                if min_v is not None and n < min_v:
                    violation_rows.append(row_idx)
                elif max_v is not None and n > max_v:
                    violation_rows.append(row_idx)

        elif check == "regex":
            pattern_str = params.get("pattern", "")
            try:
                pattern = re.compile(pattern_str)
                for row_idx, v in enumerate(col_values, start=2):
                    if v.strip() and not pattern.match(v.strip()):
                        violation_rows.append(row_idx)
            except re.error:
                issue_counter[0] += 1
                issues.append(Issue(
                    issue_id=issue_counter[0],
                    severity="Info",
                    category="rule",
                    message=f"Invalid regex in rule '{rule_name}': {pattern_str}",
                    location="Rule definition",
                    impact="Rule was skipped",
                    suggestion="Fix the regex pattern",
                ))
                continue

        elif check == "not_null":
            for row_idx, v in enumerate(col_values, start=2):
                if not v.strip():
                    violation_rows.append(row_idx)

        elif check == "unique":
            seen: dict[str, int] = {}
            for row_idx, v in enumerate(col_values, start=2):
                if v.strip():
                    if v.strip() in seen:
                        violation_rows.append(row_idx)
                    else:
                        seen[v.strip()] = row_idx

        elif check == "cross_column":
            # Cross-column comparison: params.other_column, params.operator
            other_col = params.get("other_column", "")
            operator = params.get("operator", "==")
            if other_col not in header_to_idx:
                issue_counter[0] += 1
                issues.append(Issue(
                    issue_id=issue_counter[0],
                    severity="Info",
                    category="rule",
                    message=f"Cross-column rule '{rule_name}' references non-existent column '{other_col}'",
                    location="Rule definition",
                    impact="Rule was skipped",
                    suggestion="Fix the other_column name",
                ))
                continue

            other_idx = header_to_idx[other_col]
            for row_idx, row in enumerate(rows, start=2):
                v1 = row[col_idx] if col_idx < len(row) else ""
                v2 = row[other_idx] if other_idx < len(row) else ""
                n1 = parse_numeric(v1)
                n2 = parse_numeric(v2)
                if n1 is not None and n2 is not None:
                    if operator == "<" and not (n1 < n2):
                        violation_rows.append(row_idx)
                    elif operator == "<=" and not (n1 <= n2):
                        violation_rows.append(row_idx)
                    elif operator == ">" and not (n1 > n2):
                        violation_rows.append(row_idx)
                    elif operator == ">=" and not (n1 >= n2):
                        violation_rows.append(row_idx)
                    elif operator == "==" and not (n1 == n2):
                        violation_rows.append(row_idx)
                    elif operator == "!=" and not (n1 != n2):
                        violation_rows.append(row_idx)

        if violation_rows:
            issue_counter[0] += 1
            detail = violation_rows[:MAX_DETAIL_ROWS]
            issues.append(Issue(
                issue_id=issue_counter[0],
                severity=severity,
                category="rule",
                message=f"{message} ({len(violation_rows)} violations)",
                location=f"Column '{column}', Rows: {detail}{'...' if len(violation_rows) > MAX_DETAIL_ROWS else ''}",
                impact=f"Custom rule '{rule_name}' not satisfied",
                suggestion=f"Review the {len(violation_rows)} violating rows",
                detail_rows=violation_rows,
            ))


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def determine_verdict(issues: list[Issue]) -> str:
    """Determine the overall validation verdict.

    Args:
        issues: List of all detected issues.

    Returns:
        'Valid', 'Conditional', or 'Invalid'.
    """
    severity_counts = Counter(i.severity for i in issues)
    if severity_counts.get("Critical", 0) > 0:
        return "Invalid"
    if severity_counts.get("Major", 0) > 0:
        return "Conditional"
    return "Valid"


def build_report(
    file_path: Path,
    issues: list[Issue],
    profiles: list[ColumnProfile],
    severity_mode: str,
) -> ValidationReport:
    """Build the complete validation report.

    Args:
        file_path: Path to the validated file.
        issues: List of all detected issues.
        profiles: List of column profiles.
        severity_mode: 'strict' or 'lenient'.

    Returns:
        ValidationReport dataclass.
    """
    severity_counts = Counter(i.severity for i in issues)
    verdict = determine_verdict(issues)

    # Build recommendations
    recommendations: list[str] = []
    critical_count = severity_counts.get("Critical", 0)
    major_count = severity_counts.get("Major", 0)
    minor_count = severity_counts.get("Minor", 0)

    if critical_count > 0:
        recommendations.append(
            f"URGENT: Fix {critical_count} Critical issue(s) immediately before using this data"
        )
    if major_count > 0:
        recommendations.append(
            f"Fix {major_count} Major issue(s) and re-validate before proceeding"
        )
    if minor_count > 0:
        recommendations.append(
            f"Address {minor_count} Minor issue(s) to improve data quality"
        )
    if verdict == "Valid":
        recommendations.append("Data is ready for downstream processing")

    return ValidationReport(
        meta={
            "file": str(file_path),
            "validation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "severity_mode": severity_mode,
            "total_rows": profiles[0].total_count if profiles else 0,
            "total_columns": len(profiles),
        },
        summary={
            "verdict": verdict,
            "Critical": critical_count,
            "Major": major_count,
            "Minor": minor_count,
            "Info": severity_counts.get("Info", 0),
            "total_issues": len(issues),
        },
        column_profiles=[
            {
                "name": p.name,
                "index": p.index,
                "inferred_type": p.inferred_type,
                "total_count": p.total_count,
                "non_null_count": p.non_null_count,
                "null_rate": p.null_rate,
                "unique_count": p.unique_count,
                "cardinality": p.cardinality,
                "min": p.min_value,
                "max": p.max_value,
                "mean": p.mean_value,
                "median": p.median_value,
                "stddev": p.stddev_value,
                "top_values": [{"value": v, "count": c} for v, c in p.top_values],
            }
            for p in profiles
        ],
        issues=[asdict(i) for i in issues],
        recommendations=recommendations,
    )


def print_summary(report: ValidationReport) -> None:
    """Print a human-readable summary to stdout.

    Args:
        report: The validation report.
    """
    meta = report.meta
    summary = report.summary

    print("=" * 60)
    print("  DATA VALIDATION REPORT")
    print("=" * 60)
    print(f"  File:       {meta['file']}")
    print(f"  Date:       {meta['validation_date']}")
    print(f"  Mode:       {meta['severity_mode']}")
    print(f"  Rows:       {meta['total_rows']}")
    print(f"  Columns:    {meta['total_columns']}")
    print("-" * 60)
    print(f"  Verdict:    {summary['verdict']}")
    print(f"  Critical:   {summary['Critical']}")
    print(f"  Major:      {summary['Major']}")
    print(f"  Minor:      {summary['Minor']}")
    print(f"  Info:       {summary['Info']}")
    print("-" * 60)

    if report.issues:
        print("\n  ISSUES:")
        for issue_dict in report.issues:
            print(
                f"  [{issue_dict['severity']:>8}] #{issue_dict['issue_id']}: "
                f"{issue_dict['message']}"
            )
            print(f"            Location: {issue_dict['location']}")
            print(f"            Suggestion: {issue_dict['suggestion']}")
            print()

    print("  COLUMN PROFILES:")
    for col in report.column_profiles:
        type_info = col["inferred_type"]
        null_info = f"null={col['null_rate']:.1%}"
        extra = ""
        if col["min"] is not None:
            extra = f" range=[{col['min']}, {col['max']}]"
        print(f"    {col['index']:>3}. {col['name']:<30} {type_info:<10} {null_info}{extra}")

    print()
    print("  RECOMMENDATIONS:")
    for rec in report.recommendations:
        print(f"    - {rec}")

    print("=" * 60)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="CSV/TSV Data Validator - data-validation skill execution script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python validate_csv.py data.csv\n"
            "  python validate_csv.py data.csv --schema schema.json\n"
            "  python validate_csv.py data.tsv --delimiter tab --output report.json\n"
        ),
    )
    parser.add_argument("file_path", type=Path, help="Path to the CSV/TSV file to validate")
    parser.add_argument(
        "--schema", type=Path, default=None,
        help="Path to a JSON schema file for column validation",
    )
    parser.add_argument(
        "--rules", type=Path, default=None,
        help="Path to a JSON custom rules file",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Path to write the JSON report (default: <input_file>.validation.json)",
    )
    parser.add_argument(
        "--delimiter", type=str, default="auto",
        choices=["auto", "comma", "tab", "semicolon", "pipe"],
        help="Column delimiter (default: auto-detect)",
    )
    parser.add_argument(
        "--severity", type=str, default="strict",
        choices=["strict", "lenient"],
        help="Validation severity mode (default: strict)",
    )
    return parser.parse_args(argv)


def resolve_delimiter(delimiter_arg: str) -> str | None:
    """Convert delimiter argument to actual character.

    Args:
        delimiter_arg: CLI argument value.

    Returns:
        Delimiter character or None for auto-detect.
    """
    mapping = {
        "auto": None,
        "comma": ",",
        "tab": "\t",
        "semicolon": ";",
        "pipe": "|",
    }
    return mapping.get(delimiter_arg)


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CSV/TSV validator.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Exit code: 0 for Valid, 1 for Conditional, 2 for Invalid, 3 for error.
    """
    args = parse_args(argv)
    file_path: Path = args.file_path.resolve()

    # Detect encoding
    try:
        encoding = detect_encoding(file_path)
    except FileNotFoundError:
        print(f"ERROR: File not found: {file_path}", file=sys.stderr)
        return 3

    # Detect or set delimiter
    delimiter_char = resolve_delimiter(args.delimiter)
    if delimiter_char is None:
        delimiter_char = detect_delimiter(file_path, encoding)

    # Read data
    try:
        headers, rows = read_csv_data(file_path, encoding, delimiter_char)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3

    print(f"Read {len(rows)} data rows, {len(headers)} columns (encoding: {encoding})")

    issues: list[Issue] = []
    issue_counter: list[int] = [0]  # Mutable counter

    # Step 1: Structure validation
    validate_structure(headers, rows, issues, issue_counter)

    # Step 2: Data quality validation
    profiles = validate_data_quality(headers, rows, issues, issue_counter)

    # Step 3: Schema validation (optional)
    if args.schema:
        try:
            schema = load_schema(args.schema.resolve())
            validate_schema(headers, rows, schema, issues, issue_counter)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"WARNING: Schema validation skipped: {e}", file=sys.stderr)

    # Step 4: Rule validation (optional)
    if args.rules:
        try:
            rules = load_rules(args.rules.resolve())
            validate_rules(headers, rows, rules, issues, issue_counter)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"WARNING: Rule validation skipped: {e}", file=sys.stderr)

    # Filter issues in lenient mode
    if args.severity == "lenient":
        issues = [i for i in issues if i.severity in ("Critical", "Major")]

    # Build report
    report = build_report(file_path, issues, profiles, args.severity)

    # Print human-readable summary
    print_summary(report)

    # Write JSON report
    output_path = args.output or file_path.with_suffix(
        file_path.suffix + ".validation.json"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(asdict(report) if hasattr(report, "__dataclass_fields__") else {
            "meta": report.meta,
            "summary": report.summary,
            "column_profiles": report.column_profiles,
            "issues": report.issues,
            "recommendations": report.recommendations,
        }, f, ensure_ascii=False, indent=2)

    print(f"\nJSON report written to: {output_path}")

    # Return exit code based on verdict
    verdict = report.summary["verdict"]
    if verdict == "Valid":
        return 0
    elif verdict == "Conditional":
        return 1
    else:
        return 2


if __name__ == "__main__":
    sys.exit(main())
