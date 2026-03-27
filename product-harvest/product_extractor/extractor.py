"""Core product data extraction logic.

Extracts structured product information from web pages by parsing
JSON-LD, Microdata, and Open Graph metadata — no AI required.
"""

import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def _safe_get(d: Any, *keys: str, default: str = "") -> str:
    """Safely navigate nested dicts."""
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, default)
        elif isinstance(d, list) and d:
            d = d[0]
            if isinstance(d, dict):
                d = d.get(key, default)
            else:
                return str(d) if d else default
        else:
            return default
    return str(d) if d else default


class ProductData:
    """Structured product information."""

    def __init__(
        self,
        name: str = "",
        price: str = "",
        currency: str = "",
        description: str = "",
        brand: str = "",
        sku: str = "",
        gtin: str = "",
        image: str = "",
        url: str = "",
        availability: str = "",
        rating: str = "",
        review_count: str = "",
        category: str = "",
        source_url: str = "",
        extraction_method: str = "",
    ):
        self.name = name
        self.price = price
        self.currency = currency
        self.description = description
        self.brand = brand
        self.sku = sku
        self.gtin = gtin
        self.image = image
        self.url = url
        self.availability = availability
        self.rating = rating
        self.review_count = review_count
        self.category = category
        self.source_url = source_url
        self.extraction_method = extraction_method

    def to_dict(self) -> Dict[str, str]:
        return {k: v for k, v in self.__dict__.items() if v}

    def is_valid(self) -> bool:
        """A product must have at least a name."""
        return bool(self.name.strip())


class ProductExtractor:
    """Extract product data from web pages using structured data.

    Supports JSON-LD (Schema.org), Open Graph, and HTML meta tags.
    No AI or LLM required — reads the structured data that sites
    already embed for Google/Facebook.

    Usage::

        extractor = ProductExtractor()
        products = extractor.from_url("https://shop.example.com/product")
        for p in products:
            print(f"{p.name}: {p.currency} {p.price}")
    """

    def __init__(
        self,
        timeout: int = 10,
        user_agent: str = "ProductHarvest/1.0",
    ):
        self.timeout = timeout
        self.user_agent = user_agent

    def _extract_jsonld(self, soup: BeautifulSoup, source_url: str) -> List[ProductData]:
        """Extract product data from JSON-LD script tags."""
        products: List[ProductData] = []

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
            except (json.JSONDecodeError, TypeError):
                continue

            # Handle @graph arrays
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                if data.get("@graph"):
                    items = data["@graph"]
                else:
                    items = [data]

            for item in items:
                if not isinstance(item, dict):
                    continue

                item_type = item.get("@type", "")
                if isinstance(item_type, list):
                    item_type = item_type[0] if item_type else ""

                if "Product" not in str(item_type):
                    continue

                # Extract price from offers
                offers = item.get("offers", {})
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}

                price = _safe_get(offers, "price")
                if not price:
                    price = _safe_get(offers, "lowPrice")
                currency = _safe_get(offers, "priceCurrency")
                availability = _safe_get(offers, "availability")
                if availability:
                    availability = availability.replace("https://schema.org/", "").replace("http://schema.org/", "")

                # Brand
                brand_data = item.get("brand", {})
                brand = ""
                if isinstance(brand_data, dict):
                    brand = brand_data.get("name", "")
                elif isinstance(brand_data, str):
                    brand = brand_data

                # Rating
                rating_data = item.get("aggregateRating", {})
                rating = _safe_get(rating_data, "ratingValue")
                review_count = _safe_get(rating_data, "reviewCount")
                if not review_count:
                    review_count = _safe_get(rating_data, "ratingCount")

                # Image
                image = ""
                img_data = item.get("image", "")
                if isinstance(img_data, list):
                    image = img_data[0] if img_data else ""
                elif isinstance(img_data, dict):
                    image = img_data.get("url", "")
                else:
                    image = str(img_data)

                product = ProductData(
                    name=_safe_get(item, "name"),
                    price=price,
                    currency=currency,
                    description=_safe_get(item, "description"),
                    brand=brand,
                    sku=_safe_get(item, "sku"),
                    gtin=_safe_get(item, "gtin") or _safe_get(item, "gtin13") or _safe_get(item, "gtin14"),
                    image=image,
                    url=_safe_get(item, "url") or source_url,
                    availability=availability,
                    rating=rating,
                    review_count=review_count,
                    category=_safe_get(item, "category"),
                    source_url=source_url,
                    extraction_method="json-ld",
                )
                if product.is_valid():
                    products.append(product)

        return products

    def _extract_opengraph(self, soup: BeautifulSoup, source_url: str) -> List[ProductData]:
        """Extract product data from Open Graph meta tags."""
        og: Dict[str, str] = {}
        for meta in soup.find_all("meta"):
            prop = meta.get("property", "") or meta.get("name", "")
            content = meta.get("content", "")
            if prop.startswith("og:") or prop.startswith("product:"):
                og[prop] = content

        if not og.get("og:title"):
            return []

        # Only extract if it looks like a product page
        og_type = og.get("og:type", "")
        has_price = "product:price:amount" in og or "og:price:amount" in og
        if "product" not in og_type.lower() and not has_price:
            return []

        product = ProductData(
            name=og.get("og:title", ""),
            description=og.get("og:description", ""),
            image=og.get("og:image", ""),
            url=og.get("og:url", source_url),
            price=og.get("product:price:amount", og.get("og:price:amount", "")),
            currency=og.get("product:price:currency", og.get("og:price:currency", "")),
            brand=og.get("product:brand", ""),
            availability=og.get("product:availability", ""),
            category=og.get("product:category", ""),
            source_url=source_url,
            extraction_method="opengraph",
        )
        if product.is_valid():
            return [product]
        return []

    def _extract_meta_tags(self, soup: BeautifulSoup, source_url: str) -> List[ProductData]:
        """Fallback: extract from standard meta tags and page title."""
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        desc = ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            desc = meta_desc.get("content", "")

        if not title:
            return []

        # Look for price patterns in the page
        price = ""
        currency = ""
        page_text = soup.get_text()
        price_match = re.search(r'[\$\£\€]\s*(\d+[\.,]\d{2})', page_text)
        if price_match:
            price = price_match.group(1)
            symbol = price_match.group(0)[0]
            currency = {"$": "USD", "£": "GBP", "€": "EUR"}.get(symbol, "")

        product = ProductData(
            name=title,
            description=desc,
            price=price,
            currency=currency,
            url=source_url,
            source_url=source_url,
            extraction_method="meta-tags",
        )
        return [product] if product.is_valid() and price else []

    def from_html(self, html: str, source_url: str = "") -> List[ProductData]:
        """Extract product data from HTML content.

        Tries extraction methods in order of reliability:
        1. JSON-LD (most structured, preferred by Google)
        2. Open Graph meta tags
        3. HTML meta tags + price pattern matching (fallback)

        Args:
            html: HTML content.
            source_url: Source URL for reference.

        Returns:
            List of ProductData objects.
        """
        soup = BeautifulSoup(html, "html.parser")

        # Try JSON-LD first (most reliable)
        products = self._extract_jsonld(soup, source_url)
        if products:
            return products

        # Try Open Graph
        products = self._extract_opengraph(soup, source_url)
        if products:
            return products

        # Fallback to meta tags
        return self._extract_meta_tags(soup, source_url)

    def from_url(self, url: str) -> List[ProductData]:
        """Extract product data from a URL.

        Args:
            url: Product page URL.

        Returns:
            List of ProductData objects.
        """
        headers = {"User-Agent": self.user_agent}
        resp = requests.get(url, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        return self.from_html(resp.text, source_url=url)

    def from_urls(self, urls: List[str]) -> List[ProductData]:
        """Extract product data from multiple URLs.

        Args:
            urls: List of product page URLs.

        Returns:
            List of ProductData objects from all URLs.
        """
        all_products: List[ProductData] = []
        for url in urls:
            try:
                products = self.from_url(url)
                all_products.extend(products)
            except Exception:
                continue
        return all_products
