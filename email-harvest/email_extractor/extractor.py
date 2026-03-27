"""Core email extraction logic."""

import glob as _glob
import re
from typing import List, Optional, Set

from email_extractor.deobfuscate import deobfuscate
from email_extractor.utils import EmailResult

# RFC 5322 inspired pattern — catches the vast majority of real-world addresses
EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
)

# Common false-positive domains and addresses
FALSE_POSITIVES = {
    "example.com",
    "example.org",
    "example.net",
    "test.com",
    "test.org",
    "domain.com",
    "email.com",
    "website.com",
    "placeholder.com",
    "sentry.io",
    "yourname@example.com",
    "user@example.com",
    "name@domain.com",
    "email@example.com",
    "info@example.com",
    "your-email@example.com",
    "someone@example.com",
    "john@example.com",
    "jane@example.com",
}

# File extensions that are clearly not email domains
FAKE_TLDS = {
    "png", "jpg", "jpeg", "gif", "svg", "webp", "bmp", "ico", "tiff",
    "css", "js", "ts", "jsx", "tsx", "map", "scss", "less",
    "woff", "woff2", "ttf", "eot", "otf",
    "zip", "gz", "tar", "rar", "7z", "bz2",
    "exe", "dll", "so", "dylib",
    "pdf", "doc", "docx", "xls", "xlsx",
    "mp3", "mp4", "avi", "mov", "mkv",
    "py", "rb", "go", "rs", "java", "class",
    "json", "xml", "yaml", "yml", "toml", "ini", "cfg",
    "log", "tmp", "bak", "swp",
    "lock", "min",
}


class EmailExtractor:
    """Extract email addresses from text, files, and HTML content.

    Usage::

        extractor = EmailExtractor()
        emails = extractor.from_text("Contact us at hello@company.org")
        emails = extractor.from_file("page.html")

        # With filtering
        extractor = EmailExtractor(
            include_domains=["company.org"],
            exclude_domains=["spam.org"],
        )

        # With source tracking
        results = extractor.extract("Contact hello@co.org", source="input.txt", source_type="file")
        for r in results:
            print(f"{r.email} from {r.source}")
    """

    def __init__(
        self,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        use_deobfuscate: bool = True,
    ):
        self.include_domains = (
            set(d.lower() for d in include_domains) if include_domains else None
        )
        self.exclude_domains = (
            set(d.lower() for d in exclude_domains) if exclude_domains else set()
        )
        self.use_deobfuscate = use_deobfuscate

    def _is_valid_email(self, email: str) -> bool:
        """Filter out obvious false positives."""
        email_lower = email.lower()

        if "@" not in email_lower:
            return False

        domain = email_lower.split("@", 1)[1]
        tld = domain.rsplit(".", 1)[-1]

        if tld in FAKE_TLDS:
            return False
        if domain in FALSE_POSITIVES:
            return False
        if email_lower in FALSE_POSITIVES:
            return False
        if self.include_domains and domain not in self.include_domains:
            return False
        if domain in self.exclude_domains:
            return False

        # Reject if local part or domain looks like a file path
        local = email_lower.split("@", 1)[0]
        if local.endswith(".") or domain.startswith("."):
            return False

        return True

    def _extract_raw(self, text: str) -> List[str]:
        """Extract raw email addresses from text, with optional deobfuscation."""
        if self.use_deobfuscate:
            text = deobfuscate(text)
        return EMAIL_PATTERN.findall(text)

    def _deduplicate_and_filter(self, raw_emails: List[str]) -> List[str]:
        """Deduplicate and filter a list of raw email strings."""
        seen: Set[str] = set()
        results: List[str] = []
        for email in raw_emails:
            lower = email.lower()
            if lower not in seen and self._is_valid_email(lower):
                seen.add(lower)
                results.append(lower)
        return results

    def from_text(self, text: str) -> List[str]:
        """Extract emails from a text string.

        Args:
            text: Any text that may contain email addresses.

        Returns:
            List of unique, validated email addresses.
        """
        raw = self._extract_raw(text)
        return self._deduplicate_and_filter(raw)

    def extract(
        self, text: str, source: str = "unknown", source_type: str = "text"
    ) -> List[EmailResult]:
        """Extract emails with source tracking.

        Args:
            text: Text to extract from.
            source: Source identifier (file path, URL, etc.).
            source_type: Type of source ("file", "url", "stdin", "text").

        Returns:
            List of EmailResult objects with source information.
        """
        emails = self.from_text(text)
        return [
            EmailResult(email=e, source=source, source_type=source_type)
            for e in emails
        ]

    def from_file(self, filepath: str) -> List[str]:
        """Extract emails from a local file.

        Args:
            filepath: Path to a text/HTML file.

        Returns:
            List of unique email addresses found in the file.
        """
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return self.from_text(f.read())

    def extract_from_file(self, filepath: str) -> List[EmailResult]:
        """Extract emails from a file with source tracking."""
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return self.extract(f.read(), source=filepath, source_type="file")

    def from_glob(self, pattern: str) -> List[str]:
        """Extract emails from files matching a glob pattern.

        Args:
            pattern: Glob pattern (e.g., "*.html", "**/*.txt").

        Returns:
            List of unique email addresses from all matching files.
        """
        seen: Set[str] = set()
        results: List[str] = []
        for path in sorted(_glob.glob(pattern, recursive=True)):
            for email in self.from_file(path):
                if email not in seen:
                    seen.add(email)
                    results.append(email)
        return results

    def extract_from_glob(self, pattern: str) -> List[EmailResult]:
        """Extract emails from glob pattern with source tracking."""
        results: List[EmailResult] = []
        for path in sorted(_glob.glob(pattern, recursive=True)):
            results.extend(self.extract_from_file(path))
        return results

    def from_html(self, html: str) -> List[str]:
        """Extract emails from HTML content, including mailto: links.

        Parses the HTML to find emails in:
        - mailto: link hrefs
        - Visible page text
        - Raw HTML source (catches emails in attributes, comments, etc.)

        Args:
            html: HTML content string.

        Returns:
            List of unique email addresses.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        all_raw: List[str] = []

        # Collect mailto: links
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.startswith("mailto:"):
                addr = href[7:].split("?")[0].strip()
                if EMAIL_PATTERN.fullmatch(addr):
                    all_raw.append(addr)

        # Extract from visible page text
        page_text = soup.get_text(separator=" ")
        all_raw.extend(self._extract_raw(page_text))

        # Also check raw HTML for emails in attributes/comments
        all_raw.extend(self._extract_raw(html))

        return self._deduplicate_and_filter(all_raw)
