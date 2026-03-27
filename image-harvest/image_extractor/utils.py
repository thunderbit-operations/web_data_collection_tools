"""Shared utility functions."""

import hashlib
import os
import re
import sys
from dataclasses import dataclass
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse, unquote


@dataclass
class ImageInfo:
    """Metadata about a discovered image."""

    url: str
    alt: str
    source_page: str
    filename: str
    extension: str


def is_url(source: str) -> bool:
    return source.startswith("http://") or source.startswith("https://")


def normalize_url(url: str) -> str:
    return url.split("#")[0].rstrip("/")


def detect_stdin() -> bool:
    return not sys.stdin.isatty()


def get_domain(url: str) -> str:
    return urlparse(url).netloc


def url_to_filename(url: str) -> str:
    """Derive a filename from a URL."""
    parsed = urlparse(url)
    path = unquote(parsed.path)
    basename = os.path.basename(path)
    if basename and "." in basename:
        return basename
    # Fallback: hash the URL
    h = hashlib.md5(url.encode()).hexdigest()[:12]
    return f"image_{h}"


def get_extension(url: str) -> str:
    """Get file extension from URL."""
    filename = url_to_filename(url)
    if "." in filename:
        return filename.rsplit(".", 1)[1].lower()
    return ""


IMAGE_EXTENSIONS = {
    "jpg", "jpeg", "png", "gif", "webp", "svg", "bmp", "ico",
    "tiff", "tif", "avif", "heic", "heif",
}


def is_image_url(url: str) -> bool:
    """Check if a URL likely points to an image."""
    ext = get_extension(url)
    return ext in IMAGE_EXTENSIONS


def content_hash(data: bytes) -> str:
    """SHA-256 hash of binary content for deduplication."""
    return hashlib.sha256(data).hexdigest()


def progress(msg: str, verbose: bool = True) -> None:
    if verbose and sys.stderr.isatty():
        print(f"\033[90m{msg}\033[0m", file=sys.stderr, flush=True)
    elif verbose:
        print(msg, file=sys.stderr, flush=True)


def sanitize_filename(name: str) -> str:
    """Remove or replace characters not safe for filenames."""
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = name.strip(". ")
    if not name:
        name = "unnamed"
    return name[:200]
