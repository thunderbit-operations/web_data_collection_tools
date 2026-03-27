"""Output formatters for email results."""

import csv
import io
import json
from typing import List

from email_extractor.utils import EmailResult


def format_plain(results: List[EmailResult], with_source: bool = False) -> str:
    """Format results as plain text, one email per line.

    Args:
        results: List of EmailResult objects.
        with_source: If True, append source after a tab character.

    Returns:
        Plain text string.
    """
    lines = []
    for r in results:
        if with_source:
            lines.append(f"{r.email}\t{r.source}")
        else:
            lines.append(r.email)
    return "\n".join(lines)


def format_csv(results: List[EmailResult], with_source: bool = False) -> str:
    """Format results as CSV.

    Args:
        results: List of EmailResult objects.
        with_source: If True, include source and source_type columns.

    Returns:
        CSV string with header row.
    """
    output = io.StringIO()
    if with_source:
        writer = csv.writer(output)
        writer.writerow(["email", "source", "source_type"])
        for r in results:
            writer.writerow([r.email, r.source, r.source_type])
    else:
        writer = csv.writer(output)
        writer.writerow(["email"])
        for r in results:
            writer.writerow([r.email])
    return output.getvalue().rstrip("\r\n")


def format_json(results: List[EmailResult], with_source: bool = False) -> str:
    """Format results as a JSON array.

    Args:
        results: List of EmailResult objects.
        with_source: If True, include source information in each object.

    Returns:
        JSON string.
    """
    if with_source:
        data = [
            {"email": r.email, "source": r.source, "source_type": r.source_type}
            for r in results
        ]
    else:
        data = [r.email for r in results]
    return json.dumps(data, indent=2, ensure_ascii=False)


def format_jsonl(results: List[EmailResult], with_source: bool = False) -> str:
    """Format results as JSON Lines (one JSON object per line).

    Args:
        results: List of EmailResult objects.
        with_source: If True, include source information.

    Returns:
        JSONL string.
    """
    lines = []
    for r in results:
        if with_source:
            obj = {"email": r.email, "source": r.source, "source_type": r.source_type}
        else:
            obj = {"email": r.email}
        lines.append(json.dumps(obj, ensure_ascii=False))
    return "\n".join(lines)


FORMATTERS = {
    "plain": format_plain,
    "csv": format_csv,
    "json": format_json,
    "jsonl": format_jsonl,
}


def format_results(
    results: List[EmailResult],
    fmt: str = "plain",
    with_source: bool = False,
) -> str:
    """Format results using the specified formatter.

    Args:
        results: List of EmailResult objects.
        fmt: Format name ("plain", "csv", "json", "jsonl").
        with_source: Whether to include source information.

    Returns:
        Formatted string.

    Raises:
        ValueError: If format name is not recognized.
    """
    formatter = FORMATTERS.get(fmt)
    if formatter is None:
        raise ValueError(
            f"Unknown format: {fmt!r}. Choose from: {', '.join(FORMATTERS)}"
        )
    return formatter(results, with_source=with_source)
