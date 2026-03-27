"""Core image discovery and extraction logic."""

from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from image_extractor.utils import (
    IMAGE_EXTENSIONS,
    ImageInfo,
    get_extension,
    is_image_url,
    normalize_url,
    url_to_filename,
)


class ImageExtractor:
    """Discover and collect image URLs from web pages.

    Usage::

        extractor = ImageExtractor()
        images = extractor.from_url("https://example.com")
        for img in images:
            print(img.url, img.filename)
    """

    def __init__(
        self,
        min_width: int = 0,
        min_height: int = 0,
        include_types: Optional[List[str]] = None,
        exclude_types: Optional[List[str]] = None,
        include_svg: bool = False,
        timeout: int = 10,
        user_agent: str = "ImageHarvest/1.0",
    ):
        """
        Args:
            min_width: Minimum image width (from HTML attributes, 0 = no filter).
            min_height: Minimum image height (from HTML attributes, 0 = no filter).
            include_types: Only keep these extensions (e.g., ["jpg", "png"]).
            exclude_types: Exclude these extensions.
            include_svg: Include SVG images (excluded by default as often icons).
            timeout: Request timeout in seconds.
            user_agent: User-Agent header.
        """
        self.min_width = min_width
        self.min_height = min_height
        self.include_types = (
            set(t.lower().lstrip(".") for t in include_types) if include_types else None
        )
        self.exclude_types = (
            set(t.lower().lstrip(".") for t in exclude_types) if exclude_types else set()
        )
        if not include_svg and not self.include_types:
            self.exclude_types.add("svg")
        self.timeout = timeout
        self.user_agent = user_agent

    def _passes_filter(self, url: str, width: int, height: int) -> bool:
        """Check if an image passes all filters."""
        ext = get_extension(url)

        if self.include_types and ext not in self.include_types:
            return False
        if ext in self.exclude_types:
            return False
        if self.min_width > 0 and 0 < width < self.min_width:
            return False
        if self.min_height > 0 and 0 < height < self.min_height:
            return False
        # Skip tiny tracking pixels and spacer GIFs
        if width == 1 or height == 1:
            return False
        # Skip data: URIs
        if url.startswith("data:"):
            return False

        return True

    def _parse_dimension(self, value) -> int:
        """Parse a width/height attribute to int."""
        if not value:
            return 0
        try:
            return int(str(value).rstrip("px%"))
        except (ValueError, TypeError):
            return 0

    def from_html(self, html: str, base_url: str = "") -> List[ImageInfo]:
        """Extract image URLs from HTML content.

        Finds images in:
        - <img> tags (src, data-src, data-lazy-src, srcset)
        - <picture> <source> tags
        - <a> tags linking directly to images
        - CSS background-image (inline styles)
        - <meta property="og:image"> tags

        Args:
            html: HTML content.
            base_url: Base URL for resolving relative paths.

        Returns:
            List of ImageInfo objects.
        """
        soup = BeautifulSoup(html, "html.parser")
        seen: Set[str] = set()
        results: List[ImageInfo] = []

        def _add(url: str, alt: str = "") -> None:
            if not url or url.startswith("data:"):
                return
            full_url = urljoin(base_url, url) if base_url else url
            normalized = normalize_url(full_url)
            if normalized in seen:
                return
            ext = get_extension(full_url)
            if not ext:
                return
            if ext not in IMAGE_EXTENSIONS:
                return
            seen.add(normalized)

            width = 0
            height = 0
            if not self._passes_filter(full_url, width, height):
                return

            results.append(ImageInfo(
                url=full_url,
                alt=alt,
                source_page=base_url,
                filename=url_to_filename(full_url),
                extension=ext,
            ))

        # <img> tags
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or ""
            alt = img.get("alt", "")
            width = self._parse_dimension(img.get("width"))
            height = self._parse_dimension(img.get("height"))

            if src and not src.startswith("data:"):
                full_url = urljoin(base_url, src) if base_url else src
                normalized = normalize_url(full_url)
                ext = get_extension(full_url)
                if normalized not in seen and ext in IMAGE_EXTENSIONS and self._passes_filter(full_url, width, height):
                    seen.add(normalized)
                    results.append(ImageInfo(
                        url=full_url, alt=alt, source_page=base_url,
                        filename=url_to_filename(full_url), extension=ext,
                    ))

            # srcset
            srcset = img.get("srcset", "")
            if srcset:
                for entry in srcset.split(","):
                    parts = entry.strip().split()
                    if parts:
                        _add(parts[0], alt)

        # <picture> <source> tags
        for source in soup.find_all("source"):
            srcset = source.get("srcset", "")
            for entry in srcset.split(","):
                parts = entry.strip().split()
                if parts:
                    _add(parts[0])

        # <a> tags linking to images
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if is_image_url(href):
                _add(href)

        # <meta og:image>
        for meta in soup.find_all("meta", property="og:image"):
            content = meta.get("content", "")
            if content:
                _add(content)

        # CSS background-image in inline styles
        import re
        for tag in soup.find_all(style=True):
            style = tag["style"]
            urls = re.findall(r'url\(["\']?([^"\')\s]+)["\']?\)', style)
            for url in urls:
                if is_image_url(url):
                    _add(url)

        return results

    def from_url(self, url: str) -> List[ImageInfo]:
        """Extract image URLs from a web page.

        Args:
            url: Web page URL.

        Returns:
            List of ImageInfo objects.
        """
        headers = {"User-Agent": self.user_agent}
        resp = requests.get(url, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        return self.from_html(resp.text, base_url=url)
