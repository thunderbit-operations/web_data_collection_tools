"""Web crawler for extracting emails from websites."""

import time
from typing import Callable, List, Optional, Set
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from email_extractor.extractor import EmailExtractor
from email_extractor.utils import EmailResult, ResultSet, normalize_url


class WebCrawler:
    """Crawl websites and extract email addresses.

    Supports rate limiting, robots.txt compliance, and proxy configuration.

    Usage::

        extractor = EmailExtractor()
        crawler = WebCrawler(extractor)

        # Single page
        results = crawler.extract_url("https://example.com/contact")

        # Recursive crawl
        results = crawler.crawl("https://example.com", max_depth=2)
    """

    def __init__(
        self,
        extractor: EmailExtractor,
        rate_limit: float = 1.0,
        respect_robots: bool = True,
        proxy: Optional[str] = None,
        timeout: int = 10,
        user_agent: str = "EmailHarvest/1.0",
        on_page_done: Optional[Callable[[str, int, int], None]] = None,
    ):
        """
        Args:
            extractor: EmailExtractor instance for email parsing.
            rate_limit: Seconds to wait between requests.
            respect_robots: Whether to check robots.txt before crawling.
            proxy: HTTP/HTTPS proxy URL.
            timeout: Request timeout in seconds.
            user_agent: User-Agent header string.
            on_page_done: Callback(url, pages_done, emails_found) after each page.
        """
        self.extractor = extractor
        self.rate_limit = rate_limit
        self.respect_robots = respect_robots
        self.proxy = proxy
        self.timeout = timeout
        self.user_agent = user_agent
        self.on_page_done = on_page_done
        self._robots_cache: dict = {}

    def _get_session(self) -> requests.Session:
        """Create a configured requests session."""
        session = requests.Session()
        session.headers["User-Agent"] = self.user_agent
        if self.proxy:
            session.proxies = {"http": self.proxy, "https": self.proxy}
        return session

    def _check_robots(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
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
                # If we can't fetch robots.txt, assume allowed
                self._robots_cache[robots_url] = None
                return True
            self._robots_cache[robots_url] = rp

        rp = self._robots_cache[robots_url]
        if rp is None:
            return True
        return rp.can_fetch(self.user_agent, url)

    def _fetch(self, session: requests.Session, url: str) -> str:
        """Fetch a URL and return HTML content."""
        resp = session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.text

    def _extract_from_html(self, html: str, url: str) -> List[EmailResult]:
        """Extract emails from HTML content with URL as source."""
        emails = self.extractor.from_html(html)
        return [
            EmailResult(email=e, source=url, source_type="url") for e in emails
        ]

    def _extract_links(self, html: str, base_url: str, base_domain: str) -> List[str]:
        """Extract same-domain links from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        links: List[str] = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.startswith("mailto:") or href.startswith("javascript:"):
                continue
            full_url = urljoin(base_url, href)
            if urlparse(full_url).netloc == base_domain:
                links.append(full_url)
        return links

    def extract_url(self, url: str) -> List[EmailResult]:
        """Extract emails from a single URL.

        Args:
            url: Web page URL.

        Returns:
            List of EmailResult objects.
        """
        if not self._check_robots(url):
            return []

        session = self._get_session()
        html = self._fetch(session, url)
        results = self._extract_from_html(html, url)

        if self.on_page_done:
            self.on_page_done(url, 1, len(results))

        return results

    def crawl(
        self,
        url: str,
        max_depth: int = 1,
        max_pages: int = 50,
    ) -> List[EmailResult]:
        """Crawl a website recursively and extract emails.

        Args:
            url: Starting URL.
            max_depth: How many levels of links to follow (0 = single page).
            max_pages: Maximum number of pages to visit.

        Returns:
            List of EmailResult objects from all crawled pages.
        """
        base_domain = urlparse(url).netloc
        visited: Set[str] = set()
        result_set = ResultSet()
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

            # Rate limiting (skip for first request)
            if pages_done > 0 and self.rate_limit > 0:
                time.sleep(self.rate_limit)

            visited.add(normalized)

            try:
                html = self._fetch(session, current_url)
            except Exception:
                continue

            # Extract emails
            page_results = self._extract_from_html(html, current_url)
            result_set.add_many(page_results)
            pages_done += 1

            if self.on_page_done:
                self.on_page_done(current_url, pages_done, len(result_set))

            # Follow links if within depth
            if depth < max_depth:
                for link in self._extract_links(html, current_url, base_domain):
                    norm_link = normalize_url(link)
                    if norm_link not in visited:
                        queue.append((link, depth + 1))

        return result_set.results_all_sources()
