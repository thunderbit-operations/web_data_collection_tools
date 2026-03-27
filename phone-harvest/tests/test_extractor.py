"""Tests for the core PhoneExtractor."""

import os

import pytest

from phone_extractor.extractor import PhoneExtractor

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestFromText:
    def test_us_number_with_country_code(self):
        ex = PhoneExtractor(default_region="US")
        results = ex.from_text("Call +1 (212) 555-1234")
        assert len(results) >= 1
        assert results[0].number == "+12125551234"
        assert results[0].country_code == "US"

    def test_us_local_number(self):
        ex = PhoneExtractor(default_region="US")
        results = ex.from_text("Call (650) 253-0000")
        assert len(results) >= 1
        assert results[0].country_code == "US"

    def test_uk_number(self):
        ex = PhoneExtractor(default_region="GB")
        results = ex.from_text("Call +44 20 7946 0958")
        assert len(results) >= 1
        assert results[0].country_code == "GB"
        assert results[0].number == "+442079460958"

    def test_multiple_countries(self):
        ex = PhoneExtractor(default_region="US")
        text = "US: +1 212-555-1234, UK: +44 20 7946 0958"
        results = ex.from_text(text)
        countries = {r.country_code for r in results}
        assert "US" in countries
        assert "GB" in countries

    def test_deduplication(self):
        ex = PhoneExtractor(default_region="US")
        text = "+1 (212) 555-1234 and 12125551234 and 212-555-1234"
        results = ex.from_text(text)
        e164_numbers = [r.number for r in results]
        assert e164_numbers.count("+12125551234") == 1

    def test_no_numbers(self):
        ex = PhoneExtractor(default_region="US")
        results = ex.from_text("No phone numbers here.")
        assert results == []

    def test_empty_string(self):
        ex = PhoneExtractor(default_region="US")
        results = ex.from_text("")
        assert results == []

    def test_e164_format(self):
        ex = PhoneExtractor(default_region="US")
        results = ex.from_text("+1 212-555-1234")
        assert len(results) >= 1
        assert results[0].number.startswith("+")

    def test_national_format(self):
        ex = PhoneExtractor(default_region="US")
        results = ex.from_text("+1 212-555-1234")
        assert len(results) >= 1
        assert results[0].national

    def test_international_format(self):
        ex = PhoneExtractor(default_region="US")
        results = ex.from_text("+1 212-555-1234")
        assert len(results) >= 1
        assert "+" in results[0].international

    def test_number_type(self):
        ex = PhoneExtractor(default_region="US")
        results = ex.from_text("+1 800-275-2273")
        assert len(results) >= 1
        assert results[0].number_type in (
            "TOLL_FREE", "FIXED_LINE_OR_MOBILE", "FIXED_LINE", "MOBILE", "UNKNOWN",
        )

    def test_raw_match_preserved(self):
        ex = PhoneExtractor(default_region="US")
        results = ex.from_text("Call +1 (212) 555-1234 now")
        assert len(results) >= 1
        assert "212" in results[0].raw_match


class TestCountryFiltering:
    def test_include_country(self):
        ex = PhoneExtractor(default_region="US", include_countries=["GB"])
        text = "US: +1 212-555-1234, UK: +44 20 7946 0958"
        results = ex.from_text(text)
        assert all(r.country_code == "GB" for r in results)

    def test_exclude_country(self):
        ex = PhoneExtractor(default_region="US", exclude_countries=["US"])
        text = "US: +1 212-555-1234, UK: +44 20 7946 0958"
        results = ex.from_text(text)
        assert all(r.country_code != "US" for r in results)


class TestTypeFiltering:
    def test_include_type(self):
        ex = PhoneExtractor(default_region="US", include_types=["TOLL_FREE"])
        text = "+1 800-275-2273 and +1 212-555-1234"
        results = ex.from_text(text)
        assert all(r.number_type == "TOLL_FREE" for r in results)


class TestDeobfuscation:
    def test_deobfuscation_dot_format(self):
        ex = PhoneExtractor(default_region="US", use_deobfuscate=True)
        results = ex.from_text("Call 650.253.0000")
        assert len(results) >= 1

    def test_deobfuscation_disabled(self):
        ex = PhoneExtractor(default_region="US", use_deobfuscate=False)
        results_off = ex.from_text("Call 650.253.0000")
        ex2 = PhoneExtractor(default_region="US", use_deobfuscate=True)
        results_on = ex2.from_text("Call 650.253.0000")
        assert len(results_on) >= len(results_off)


class TestFromFile:
    def test_sample_txt(self):
        ex = PhoneExtractor(default_region="US")
        results = ex.from_file(os.path.join(FIXTURES, "sample.txt"))
        assert len(results) > 0
        e164s = {r.number for r in results}
        assert "+12125551234" in e164s
        assert "+442079460958" in e164s


class TestFromHtml:
    def test_sample_html(self):
        ex = PhoneExtractor(default_region="US")
        with open(os.path.join(FIXTURES, "sample.html")) as f:
            html = f.read()
        results = ex.from_html(html, source="test.html")
        assert len(results) > 0
        e164s = {r.number for r in results}
        assert "+12125551234" in e164s
        assert "+442079460958" in e164s
        assert all(r.source == "test.html" for r in results)


class TestExtractSimple:
    def test_convenience_method(self):
        ex = PhoneExtractor(default_region="US")
        numbers = ex.extract_simple("Call +1 212-555-1234 or +44 20 7946 0958")
        assert "+12125551234" in numbers
        assert "+442079460958" in numbers
