"""Shared utility functions and data structures."""

import glob as _glob
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional
from urllib.parse import urlparse


@dataclass
class PhoneResult:
    """An extracted phone number with metadata and source tracking."""

    number: str  # E.164 format: +15551234567
    national: str  # National format: (555) 123-4567
    international: str  # International format: +1 555-123-4567
    country_code: str  # ISO 3166-1 alpha-2: US, GB, CN
    country_name: str  # Full name: United States, United Kingdom
    carrier_name: str  # Carrier: AT&T, Vodafone, or empty
    number_type: str  # MOBILE, FIXED_LINE, VOIP, TOLL_FREE, etc.
    source: str  # file path, URL, or "stdin"
    source_type: str  # "file", "url", "stdin", "text"
    raw_match: str  # Original text that was matched


class ResultSet:
    """Deduplicated collection of phone results, keyed by E.164 number."""

    def __init__(self) -> None:
        self._numbers: Dict[str, PhoneResult] = {}
        self._order: List[str] = []

    def add(self, result: PhoneResult) -> None:
        if result.number not in self._numbers:
            self._numbers[result.number] = result
            self._order.append(result.number)

    def add_many(self, results: List[PhoneResult]) -> None:
        for r in results:
            self.add(r)

    def results(self) -> List[PhoneResult]:
        return [self._numbers[n] for n in self._order]

    def __len__(self) -> int:
        return len(self._order)


def is_url(source: str) -> bool:
    return source.startswith("http://") or source.startswith("https://")


def is_glob(source: str) -> bool:
    return any(c in source for c in ("*", "?", "["))


def expand_glob(pattern: str) -> List[str]:
    return sorted(_glob.glob(pattern, recursive=True))


def normalize_url(url: str) -> str:
    return url.split("#")[0].rstrip("/")


def detect_stdin() -> bool:
    return not sys.stdin.isatty()


def get_domain(url: str) -> str:
    return urlparse(url).netloc


def progress(msg: str, verbose: bool = True) -> None:
    if verbose and sys.stderr.isatty():
        print(f"\033[90m{msg}\033[0m", file=sys.stderr, flush=True)
    elif verbose:
        print(msg, file=sys.stderr, flush=True)
