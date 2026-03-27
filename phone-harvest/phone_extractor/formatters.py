"""Output formatters for phone number results."""

import csv
import io
import json
from typing import List

from phone_extractor.utils import PhoneResult


def _result_to_dict(r: PhoneResult, detail: bool = False) -> dict:
    """Convert a PhoneResult to a dictionary."""
    d = {"number": r.number}
    if detail:
        d.update({
            "national": r.national,
            "international": r.international,
            "country_code": r.country_code,
            "country_name": r.country_name,
            "carrier": r.carrier_name,
            "type": r.number_type,
            "source": r.source,
        })
    return d


def format_plain(results: List[PhoneResult], detail: bool = False) -> str:
    lines = []
    for r in results:
        if detail:
            parts = [r.international, r.country_code, r.number_type]
            if r.carrier_name:
                parts.append(r.carrier_name)
            parts.append(r.source)
            lines.append("\t".join(parts))
        else:
            lines.append(r.number)
    return "\n".join(lines)


def format_csv(results: List[PhoneResult], detail: bool = False) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    if detail:
        writer.writerow([
            "number", "national", "international",
            "country_code", "country_name", "carrier", "type", "source",
        ])
        for r in results:
            writer.writerow([
                r.number, r.national, r.international,
                r.country_code, r.country_name, r.carrier_name,
                r.number_type, r.source,
            ])
    else:
        writer.writerow(["number"])
        for r in results:
            writer.writerow([r.number])
    return output.getvalue().rstrip("\r\n")


def format_json(results: List[PhoneResult], detail: bool = False) -> str:
    data = [_result_to_dict(r, detail) for r in results]
    return json.dumps(data, indent=2, ensure_ascii=False)


def format_jsonl(results: List[PhoneResult], detail: bool = False) -> str:
    lines = []
    for r in results:
        lines.append(json.dumps(_result_to_dict(r, detail), ensure_ascii=False))
    return "\n".join(lines)


FORMATTERS = {
    "plain": format_plain,
    "csv": format_csv,
    "json": format_json,
    "jsonl": format_jsonl,
}


def format_results(
    results: List[PhoneResult],
    fmt: str = "plain",
    detail: bool = False,
) -> str:
    formatter = FORMATTERS.get(fmt)
    if formatter is None:
        raise ValueError(
            f"Unknown format: {fmt!r}. Choose from: {', '.join(FORMATTERS)}"
        )
    return formatter(results, detail=detail)
