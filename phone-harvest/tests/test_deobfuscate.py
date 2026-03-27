"""Tests for the phone deobfuscation engine."""

from phone_extractor.deobfuscate import deobfuscate


class TestDotSeparators:
    def test_us_dots(self):
        result = deobfuscate("555.123.4567")
        assert "555-123-4567" in result

    def test_international_dots(self):
        result = deobfuscate("+1.555.123.4567")
        assert "555-123-4567" in result


class TestUnicodeChars:
    def test_fullwidth_digits(self):
        result = deobfuscate("\uff15\uff15\uff15\uff11\uff12\uff13\uff14\uff15\uff16\uff17")
        assert "5551234567" in result

    def test_fullwidth_plus(self):
        result = deobfuscate("\uff0b1 555 123 4567")
        assert "+1" in result

    def test_em_dash(self):
        result = deobfuscate("555\u20141234")
        assert "555-1234" in result

    def test_en_dash(self):
        result = deobfuscate("555\u20131234")
        assert "555-1234" in result

    def test_non_breaking_space(self):
        result = deobfuscate("555\u00a0123\u00a04567")
        assert "555 123 4567" in result


class TestHtmlEntities:
    def test_numeric_plus(self):
        result = deobfuscate("&#43;1 555 123 4567")
        assert "+1" in result

    def test_named_entity(self):
        result = deobfuscate("&plus;1 555 123 4567")
        assert "+1" in result


class TestUrlEncoding:
    def test_encoded_plus(self):
        result = deobfuscate("%2B1 555 123 4567")
        assert "+1" in result


class TestSpacedDigits:
    def test_spaced_out_number(self):
        result = deobfuscate("5 5 5 1 2 3 4 5 6 7")
        assert "5551234567" in result

    def test_short_spaced_not_collapsed(self):
        # Less than 7 spaced digits should not be collapsed
        result = deobfuscate("1 2 3 4 5")
        assert "1 2 3 4 5" in result


class TestWordSeparators:
    def test_dash_word(self):
        result = deobfuscate("555 dash 123 dash 4567")
        assert "555-123-4567" in result

    def test_hyphen_word(self):
        result = deobfuscate("555 hyphen 123 hyphen 4567")
        assert "555-123-4567" in result


class TestPassthrough:
    def test_normal_number(self):
        assert "+1 555-123-4567" == deobfuscate("+1 555-123-4567")

    def test_no_number_text(self):
        text = "No phone numbers in this text."
        assert text == deobfuscate(text)

    def test_empty_string(self):
        assert "" == deobfuscate("")
