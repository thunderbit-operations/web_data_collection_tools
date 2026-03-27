"""Shared utility functions."""

import glob as _glob
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.parse import urlparse


@dataclass
class EmailResult:
    """An extracted email with source tracking."""

    email: str
    source: str  # file path, URL, or "stdin"
    source_type: str  # "file", "url", "stdin", "text"


class ResultSet:
    """Deduplicated collection of email results, preserving all sources."""

    def __init__(self) -> None:
        self._emails: Dict[str, List[str]] = {}  # email -> [sources]
        self._order: List[str] = []  # insertion order

    def add(self, email: str, source: str, source_type: str) -> None:
        lower = email.lower()
        if lower not in self._emails:
            self._emails[lower] = []
            self._order.append(lower)
        src_key = f"{source_type}:{source}"
        if src_key not in self._emails[lower]:
            self._emails[lower].append(src_key)

    def add_many(self, results: List[EmailResult]) -> None:
        for r in results:
            self.add(r.email, r.source, r.source_type)

    def emails(self) -> List[str]:
        """Return deduplicated emails in insertion order."""
        return list(self._order)

    def results(self) -> List[EmailResult]:
        """Return EmailResult objects (one per email, first source)."""
        out = []
        for email in self._order:
            sources = self._emails[email]
            src_type, src = sources[0].split(":", 1)
            out.append(EmailResult(email=email, source=src, source_type=src_type))
        return out

    def results_all_sources(self) -> List[EmailResult]:
        """Return EmailResult objects (one per email-source pair)."""
        out = []
        for email in self._order:
            for src_key in self._emails[email]:
                src_type, src = src_key.split(":", 1)
                out.append(EmailResult(email=email, source=src, source_type=src_type))
        return out

    def __len__(self) -> int:
        return len(self._order)


def is_url(source: str) -> bool:
    """Check if a source string looks like a URL."""
    return source.startswith("http://") or source.startswith("https://")


def is_glob(source: str) -> bool:
    """Check if a source string contains glob pattern characters."""
    return any(c in source for c in ("*", "?", "["))


def expand_glob(pattern: str) -> List[str]:
    """Expand a glob pattern to matching file paths."""
    return sorted(_glob.glob(pattern, recursive=True))


def normalize_url(url: str) -> str:
    """Normalize a URL by removing fragment and trailing slash."""
    return url.split("#")[0].rstrip("/")


def detect_stdin() -> bool:
    """Check if stdin has piped data."""
    return not sys.stdin.isatty()


def get_domain(url: str) -> str:
    """Extract domain from a URL."""
    return urlparse(url).netloc


def progress(msg: str, verbose: bool = True) -> None:
    """Print a progress message to stderr with dim color."""
    if verbose and sys.stderr.isatty():
        print(f"\033[90m{msg}\033[0m", file=sys.stderr, flush=True)
    elif verbose:
        print(msg, file=sys.stderr, flush=True)
