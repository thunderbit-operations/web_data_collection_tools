"""Tests for the image extractor."""

import os
import pytest
from image_extractor.extractor import ImageExtractor

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestFromHtml:
    def _load_gallery(self):
        with open(os.path.join(FIXTURES, "gallery.html")) as f:
            return f.read()

    def test_finds_img_tags(self):
        ex = ImageExtractor()
        images = ex.from_html(self._load_gallery(), base_url="https://example.com")
        urls = {img.url for img in images}
        assert "https://example.com/photos/sunset.jpg" in urls
        assert "https://example.com/photos/mountain.png" in urls

    def test_finds_lazy_loaded(self):
        ex = ImageExtractor()
        images = ex.from_html(self._load_gallery(), base_url="https://example.com")
        urls = {img.url for img in images}
        assert "https://example.com/photos/lazy-loaded.jpg" in urls

    def test_finds_srcset(self):
        ex = ImageExtractor()
        images = ex.from_html(self._load_gallery(), base_url="https://example.com")
        urls = {img.url for img in images}
        assert "https://example.com/photos/hero-2x.jpg" in urls

    def test_finds_link_to_image(self):
        ex = ImageExtractor()
        images = ex.from_html(self._load_gallery(), base_url="https://example.com")
        urls = {img.url for img in images}
        assert "https://example.com/photos/full-size.jpg" in urls

    def test_finds_og_image(self):
        ex = ImageExtractor()
        images = ex.from_html(self._load_gallery(), base_url="https://example.com")
        urls = {img.url for img in images}
        assert "https://example.com/og-banner.jpg" in urls

    def test_finds_css_background(self):
        ex = ImageExtractor()
        images = ex.from_html(self._load_gallery(), base_url="https://example.com")
        urls = {img.url for img in images}
        assert "https://example.com/photos/bg-pattern.png" in urls

    def test_excludes_svg_by_default(self):
        ex = ImageExtractor()
        images = ex.from_html(self._load_gallery(), base_url="https://example.com")
        urls = {img.url for img in images}
        assert not any(url.endswith(".svg") for url in urls)

    def test_includes_svg_when_enabled(self):
        ex = ImageExtractor(include_svg=True)
        images = ex.from_html(self._load_gallery(), base_url="https://example.com")
        urls = {img.url for img in images}
        assert any(url.endswith(".svg") for url in urls)

    def test_excludes_tracking_pixel(self):
        ex = ImageExtractor()
        images = ex.from_html(self._load_gallery(), base_url="https://example.com")
        urls = {img.url for img in images}
        assert "https://example.com/tracking.gif" not in urls

    def test_excludes_data_uri(self):
        ex = ImageExtractor()
        images = ex.from_html(self._load_gallery(), base_url="https://example.com")
        assert not any(img.url.startswith("data:") for img in images)

    def test_ignores_non_image_links(self):
        ex = ImageExtractor()
        images = ex.from_html(self._load_gallery(), base_url="https://example.com")
        urls = {img.url for img in images}
        assert not any(url.endswith(".pdf") for url in urls)

    def test_preserves_alt_text(self):
        ex = ImageExtractor()
        images = ex.from_html(self._load_gallery(), base_url="https://example.com")
        sunset = [img for img in images if "sunset" in img.url]
        assert len(sunset) >= 1
        assert sunset[0].alt == "Beautiful sunset"

    def test_deduplication(self):
        ex = ImageExtractor()
        images = ex.from_html(self._load_gallery(), base_url="https://example.com")
        urls = [img.url for img in images]
        assert len(urls) == len(set(urls))


class TestTypeFiltering:
    def test_include_types(self):
        ex = ImageExtractor(include_types=["jpg"])
        html = '<img src="/a.jpg"><img src="/b.png"><img src="/c.jpg">'
        images = ex.from_html(html, base_url="https://example.com")
        assert all(img.extension == "jpg" for img in images)

    def test_exclude_types(self):
        ex = ImageExtractor(exclude_types=["gif"])
        html = '<img src="/a.jpg"><img src="/b.gif">'
        images = ex.from_html(html, base_url="https://example.com")
        assert not any(img.extension == "gif" for img in images)


class TestImageInfo:
    def test_filename_extraction(self):
        ex = ImageExtractor()
        images = ex.from_html(
            '<img src="/photos/my-photo.jpg">',
            base_url="https://example.com",
        )
        assert images[0].filename == "my-photo.jpg"
        assert images[0].extension == "jpg"

    def test_source_page_tracking(self):
        ex = ImageExtractor()
        images = ex.from_html(
            '<img src="/photo.jpg">',
            base_url="https://example.com/gallery",
        )
        assert images[0].source_page == "https://example.com/gallery"
