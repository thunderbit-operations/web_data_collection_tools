"""Core phone number extraction logic.

Uses Google's libphonenumber (via python-phonenumbers) for robust
international phone number detection, validation, and metadata extraction.
"""

import glob as _glob
from typing import List, Optional, Set

import phonenumbers
from phonenumbers import PhoneNumberMatcher, PhoneNumberFormat
from phonenumbers import carrier as pn_carrier
from phonenumbers import geocoder as pn_geocoder
from phonenumbers import number_type as pn_number_type_func
from phonenumbers import PhoneNumberType
from phonenumbers.phonenumbermatcher import Leniency

from phone_extractor.deobfuscate import deobfuscate
from phone_extractor.utils import PhoneResult

# Map PhoneNumberType enum to human-readable strings
_TYPE_NAMES = {
    PhoneNumberType.FIXED_LINE: "FIXED_LINE",
    PhoneNumberType.MOBILE: "MOBILE",
    PhoneNumberType.FIXED_LINE_OR_MOBILE: "FIXED_LINE_OR_MOBILE",
    PhoneNumberType.TOLL_FREE: "TOLL_FREE",
    PhoneNumberType.PREMIUM_RATE: "PREMIUM_RATE",
    PhoneNumberType.SHARED_COST: "SHARED_COST",
    PhoneNumberType.VOIP: "VOIP",
    PhoneNumberType.PERSONAL_NUMBER: "PERSONAL_NUMBER",
    PhoneNumberType.PAGER: "PAGER",
    PhoneNumberType.UAN: "UAN",
    PhoneNumberType.VOICEMAIL: "VOICEMAIL",
    PhoneNumberType.UNKNOWN: "UNKNOWN",
}


class PhoneExtractor:
    """Extract phone numbers from text, files, and HTML content.

    Uses Google's libphonenumber for robust international number detection
    with country identification, carrier lookup, and format normalization.

    Usage::

        extractor = PhoneExtractor()
        numbers = extractor.from_text("Call us at +1 (555) 123-4567")

        # With default country for local numbers
        extractor = PhoneExtractor(default_region="US")
        numbers = extractor.from_text("Call 555-123-4567")

        # Filter by country
        extractor = PhoneExtractor(include_countries=["US", "GB"])
    """

    def __init__(
        self,
        default_region: str = "US",
        include_countries: Optional[List[str]] = None,
        exclude_countries: Optional[List[str]] = None,
        include_types: Optional[List[str]] = None,
        use_deobfuscate: bool = True,
        leniency: str = "possible",
    ):
        """
        Args:
            default_region: ISO 3166-1 alpha-2 code for parsing local numbers.
            include_countries: Only keep numbers from these countries.
            exclude_countries: Exclude numbers from these countries.
            include_types: Only keep these types (MOBILE, FIXED_LINE, etc.).
            use_deobfuscate: Whether to apply deobfuscation before extraction.
            leniency: PhoneNumberMatcher leniency: "possible" or "valid".
        """
        self.default_region = default_region.upper()
        self.include_countries = (
            set(c.upper() for c in include_countries) if include_countries else None
        )
        self.exclude_countries = (
            set(c.upper() for c in exclude_countries) if exclude_countries else set()
        )
        self.include_types = (
            set(t.upper() for t in include_types) if include_types else None
        )
        self.use_deobfuscate = use_deobfuscate

        if leniency == "valid":
            self.leniency = Leniency.VALID
        else:
            self.leniency = Leniency.POSSIBLE

    def _get_metadata(self, number: phonenumbers.PhoneNumber, raw: str) -> Optional[dict]:
        """Extract metadata from a parsed phone number."""
        # Get country code
        region = phonenumbers.region_code_for_number(number)
        if not region:
            return None

        # Apply country filters
        if self.include_countries and region not in self.include_countries:
            return None
        if region in self.exclude_countries:
            return None

        # Get number type
        ntype = pn_number_type_func(number)
        type_name = _TYPE_NAMES.get(ntype, "UNKNOWN")

        # Apply type filter
        if self.include_types and type_name not in self.include_types:
            return None

        # Get carrier and location
        carrier_name = pn_carrier.name_for_number(number, "en")
        country_name = pn_geocoder.description_for_number(number, "en")
        if not country_name:
            country_name = pn_geocoder.country_name_for_number(number, "en")

        return {
            "e164": phonenumbers.format_number(number, PhoneNumberFormat.E164),
            "national": phonenumbers.format_number(number, PhoneNumberFormat.NATIONAL),
            "international": phonenumbers.format_number(number, PhoneNumberFormat.INTERNATIONAL),
            "region": region,
            "country_name": country_name or region,
            "carrier": carrier_name or "",
            "type": type_name,
            "raw": raw,
        }

    def from_text(
        self,
        text: str,
        source: str = "unknown",
        source_type: str = "text",
    ) -> List[PhoneResult]:
        """Extract phone numbers from text.

        Args:
            text: Any text that may contain phone numbers.
            source: Source identifier for tracking.
            source_type: Type of source.

        Returns:
            List of PhoneResult objects with full metadata.
        """
        if self.use_deobfuscate:
            text = deobfuscate(text)

        seen: Set[str] = set()
        results: List[PhoneResult] = []

        for match in PhoneNumberMatcher(text, self.default_region, self.leniency):
            number = match.number
            raw_text = match.raw_string

            meta = self._get_metadata(number, raw_text)
            if meta is None:
                continue

            e164 = meta["e164"]
            if e164 in seen:
                continue
            seen.add(e164)

            results.append(PhoneResult(
                number=e164,
                national=meta["national"],
                international=meta["international"],
                country_code=meta["region"],
                country_name=meta["country_name"],
                carrier_name=meta["carrier"],
                number_type=meta["type"],
                source=source,
                source_type=source_type,
                raw_match=raw_text,
            ))

        return results

    def from_file(self, filepath: str) -> List[PhoneResult]:
        """Extract phone numbers from a local file."""
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return self.from_text(f.read(), source=filepath, source_type="file")

    def from_glob(self, pattern: str) -> List[PhoneResult]:
        """Extract phone numbers from files matching a glob pattern."""
        seen: Set[str] = set()
        results: List[PhoneResult] = []
        for path in sorted(_glob.glob(pattern, recursive=True)):
            for r in self.from_file(path):
                if r.number not in seen:
                    seen.add(r.number)
                    results.append(r)
        return results

    def from_html(self, html_content: str, source: str = "unknown") -> List[PhoneResult]:
        """Extract phone numbers from HTML, including tel: links.

        Args:
            html_content: HTML string.
            source: Source URL or identifier.

        Returns:
            List of PhoneResult objects.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, "html.parser")
        all_text_parts: List[str] = []

        # Extract tel: links
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.startswith("tel:"):
                phone_str = href[4:].strip()
                all_text_parts.append(phone_str)

        # Get visible page text
        page_text = soup.get_text(separator=" ")
        all_text_parts.append(page_text)

        # Also scan raw HTML for numbers in attributes
        all_text_parts.append(html_content)

        combined = "\n".join(all_text_parts)
        return self.from_text(combined, source=source, source_type="url")

    def extract_simple(self, text: str) -> List[str]:
        """Convenience method: extract and return just E.164 numbers.

        Args:
            text: Input text.

        Returns:
            List of phone numbers in E.164 format.
        """
        return [r.number for r in self.from_text(text)]
