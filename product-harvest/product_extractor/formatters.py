"""Output formatters for product data."""

import csv
import io
import json
from typing import List

from product_extractor.extractor import ProductData

FIELDS = [
    "name", "price", "currency", "brand", "availability",
    "rating", "review_count", "sku", "category",
    "description", "image", "url", "source_url", "extraction_method",
]

COMPACT_FIELDS = ["name", "price", "currency", "brand", "availability", "url"]


def format_plain(products: List[ProductData], detail: bool = False) -> str:
    lines = []
    for p in products:
        if detail:
            parts = [p.name, f"{p.currency} {p.price}" if p.price else "N/A"]
            if p.brand:
                parts.append(p.brand)
            if p.availability:
                parts.append(p.availability)
            parts.append(p.url or p.source_url)
            lines.append("\t".join(parts))
        else:
            price_str = f"{p.currency} {p.price}" if p.price else "N/A"
            lines.append(f"{p.name}\t{price_str}")
    return "\n".join(lines)


def format_csv(products: List[ProductData], detail: bool = False) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    fields = FIELDS if detail else COMPACT_FIELDS
    writer.writerow(fields)
    for p in products:
        d = p.to_dict()
        writer.writerow([d.get(f, "") for f in fields])
    return output.getvalue().rstrip("\r\n")


def format_json(products: List[ProductData], detail: bool = False) -> str:
    fields = FIELDS if detail else COMPACT_FIELDS
    data = []
    for p in products:
        d = p.to_dict()
        data.append({f: d.get(f, "") for f in fields})
    return json.dumps(data, indent=2, ensure_ascii=False)


def format_jsonl(products: List[ProductData], detail: bool = False) -> str:
    fields = FIELDS if detail else COMPACT_FIELDS
    lines = []
    for p in products:
        d = p.to_dict()
        lines.append(json.dumps({f: d.get(f, "") for f in fields}, ensure_ascii=False))
    return "\n".join(lines)


FORMATTERS = {
    "plain": format_plain,
    "csv": format_csv,
    "json": format_json,
    "jsonl": format_jsonl,
}


def format_results(products: List[ProductData], fmt: str = "plain", detail: bool = False) -> str:
    formatter = FORMATTERS.get(fmt)
    if formatter is None:
        raise ValueError(f"Unknown format: {fmt!r}. Choose from: {', '.join(FORMATTERS)}")
    return formatter(products, detail=detail)
