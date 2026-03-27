"""Web crawler for discovering images across multiple pages."""

import time
from typing import Callable, List, Optional, Set
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from image_extractor.extractor import ImageExtractor
from image_extractor.utils import ImageInfo, normalize_url


class ImageCrawler:
    """Crawl websites and discover images across multiple pages.

    Usage::

        extractor = ImageExtractor(min_width=100)
        crawler = ImageCrawler(extractor)
        images = crawler.crawl("https://example.com", max_depth=2)
    """

    def __init__(
        self,
        extractor: ImageExtractor,
        rate_limit: float = 1.0,
        respect_robots: bool = True,
        proxy: Optional[str] = None,
        timeout: int = 10,
        user_agent: str = "ImageHarvest/1.0",
        on_page_done: Optional[Callable[[str, int, int], None]] = None,
    ):
        self.extractor = extractor
        self.rate_limit = rate_limit
        self.respect_robots = respect_robots
        self.proxy = proxy
        self.timeout = timeout
        self.user_agent = user_agent
        self.on_page_done = on_page_done
        self._robots_cache: dict = {}

    def _get_session(self) -> requests.Session:
        session = requests.Session()
        session.headers["User-Agent"] = self.user_agent
        if self.proxy:
            session.proxies = {"http": self.proxy, "https": self.proxy}
        return session

    def _check_robots(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        if robots_url not in self._robots_cache:
            rp = RobotFileParser()
            rp.set_url(robots_url)
            try:
                rp.read()
            except Exception:
                self._robots_cache[robots_url] = None
                return True
            self._robots_cache[robots_url] = rp
        rp = self._robots_cache[robots_url]
        if rp is None:
            return True
        return rp.can_fetch(self.user_agent, url)

    def _fetch(self, session: requests.Session, url: str) -> str:
        resp = session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.text

    def _extract_links(self, html: str, base_url: str, base_domain: str) -> List[str]:
        soup = BeautifulSoup(html, "html.parser")
        links: List[str] = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.startswith(("mailto:", "javascript:", "tel:")):
                continue
            full_url = urljoin(base_url, href)
            if urlparse(full_url).netloc == base_domain:
                links.append(full_url)
        return links

    def crawl(
        self,
        url: str,
        max_depth: int = 1,
        max_pages: int = 50,
    ) -> List[ImageInfo]:
        """Crawl a website and discover images."""
        base_domain = urlparse(url).netloc
        visited: Set[str] = set()
        all_images: dict = {}  # url -> ImageInfo (dedup by image URL)
        queue: list = [(url, 0)]
        session = self._get_session()
        pages_done = 0

        while queue and len(visited) < max_pages:
            current_url, depth = queue.pop(0)
            normalized = normalize_url(current_url)
            if normalized in visited:
                continue
            if not self._check_robots(current_url):
                visited.add(normalized)
                continue
            if pages_done > 0 and self.rate_limit > 0:
                time.sleep(self.rate_limit)
            visited.add(normalized)

            try:
                html = self._fetch(session, current_url)
            except Exception:
                continue

            page_images = self.extractor.from_html(html, base_url=current_url)
            for img in page_images:
                if img.url not in all_images:
                    all_images[img.url] = img
            pages_done += 1

            if self.on_page_done:
                self.on_page_done(current_url, pages_done, len(all_images))

            if depth < max_depth:
                for link in self._extract_links(html, current_url, base_domain):
                    norm_link = normalize_url(link)
                    if norm_link not in visited:
                        queue.append((link, depth + 1))

        return list(all_images.values())
