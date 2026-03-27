"""Tests for the product extractor."""

import os
import pytest
from product_extractor.extractor import ProductExtractor

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _load(name):
    with open(os.path.join(FIXTURES, name)) as f:
        return f.read()


class TestJsonLd:
    def test_extracts_product(self):
        ex = ProductExtractor()
        products = ex.from_html(_load("jsonld_product.html"), "https://shop.example.com/headphones")
        assert len(products) == 1
        p = products[0]
        assert p.name == "ProMax Wireless Headphones"
        assert p.price == "149.99"
        assert p.currency == "USD"
        assert p.brand == "ProMax"
        assert p.sku == "WH-PM-2024"
        assert p.availability == "InStock"
        assert p.rating == "4.5"
        assert p.review_count == "328"
        assert p.extraction_method == "json-ld"

    def test_extracts_description(self):
        ex = ProductExtractor()
        products = ex.from_html(_load("jsonld_product.html"), "https://shop.example.com")
        assert "noise-cancelling" in products[0].description

    def test_extracts_image(self):
        ex = ProductExtractor()
        products = ex.from_html(_load("jsonld_product.html"), "https://shop.example.com")
        assert "headphones.jpg" in products[0].image

    def test_extracts_gtin(self):
        ex = ProductExtractor()
        products = ex.from_html(_load("jsonld_product.html"), "https://shop.example.com")
        assert products[0].gtin == "0123456789012"

    def test_extracts_category(self):
        ex = ProductExtractor()
        products = ex.from_html(_load("jsonld_product.html"), "https://shop.example.com")
        assert "Headphones" in products[0].category


class TestOpenGraph:
    def test_extracts_product(self):
        ex = ProductExtractor()
        products = ex.from_html(_load("opengraph_product.html"), "https://sport.example.com/shoes")
        assert len(products) == 1
        p = products[0]
        assert p.name == "UltraRun Pro Running Shoes"
        assert p.price == "129.00"
        assert p.currency == "USD"
        assert p.brand == "UltraRun"
        assert p.extraction_method == "opengraph"

    def test_extracts_description(self):
        ex = ProductExtractor()
        products = ex.from_html(_load("opengraph_product.html"), "https://sport.example.com")
        assert "marathon" in products[0].description

    def test_extracts_image(self):
        ex = ProductExtractor()
        products = ex.from_html(_load("opengraph_product.html"), "https://sport.example.com")
        assert "shoes.jpg" in products[0].image

    def test_extracts_availability(self):
        ex = ProductExtractor()
        products = ex.from_html(_load("opengraph_product.html"), "https://sport.example.com")
        assert products[0].availability == "in stock"


class TestMetaFallback:
    def test_extracts_from_title_and_price(self):
        ex = ProductExtractor()
        products = ex.from_html(_load("meta_only.html"), "https://example.com/watch")
        assert len(products) == 1
        p = products[0]
        assert "Classic Watch" in p.name
        assert p.price == "89.99"
        assert p.currency == "USD"
        assert p.extraction_method == "meta-tags"


class TestNoProduct:
    def test_returns_empty(self):
        ex = ProductExtractor()
        products = ex.from_html(_load("no_product.html"), "https://example.com/about")
        assert products == []


class TestProductData:
    def test_to_dict(self):
        ex = ProductExtractor()
        products = ex.from_html(_load("jsonld_product.html"), "https://shop.example.com")
        d = products[0].to_dict()
        assert "name" in d
        assert "price" in d
        assert isinstance(d, dict)

    def test_is_valid(self):
        ex = ProductExtractor()
        products = ex.from_html(_load("jsonld_product.html"), "https://shop.example.com")
        assert products[0].is_valid()

    def test_empty_is_invalid(self):
        from product_extractor.extractor import ProductData
        p = ProductData()
        assert not p.is_valid()
