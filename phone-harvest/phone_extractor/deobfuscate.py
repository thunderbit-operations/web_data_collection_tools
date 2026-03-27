"""Phone number deobfuscation engine.

Normalizes common obfuscation patterns found on web pages back into
parseable phone number formats.
"""

import html
import re
from urllib.parse import unquote


def _decode_html_entities(text: str) -> str:
    """Decode HTML entities: &#43; -> +, &#40; -> (, etc."""
    return html.unescape(text)


def _decode_url_encoding(text: str) -> str:
    """Decode URL-encoded characters: %2B -> +, %28 -> (, etc."""
    return unquote(text)


def _replace_unicode_chars(text: str) -> str:
    """Replace unicode dash/space variants with standard chars."""
    # EN DASH, EM DASH, FIGURE DASH, HORIZONTAL BAR -> hyphen
    for char in ("\u2013", "\u2014", "\u2012", "\u2015"):
        text = text.replace(char, "-")
    # NON-BREAKING SPACE, THIN SPACE, NARROW NO-BREAK SPACE -> space
    for char in ("\u00a0", "\u2009", "\u202f"):
        text = text.replace(char, " ")
    # FULLWIDTH digits -> ASCII
    for i, fw in enumerate("\uff10\uff11\uff12\uff13\uff14\uff15\uff16\uff17\uff18\uff19"):
        text = text.replace(fw, str(i))
    # FULLWIDTH + sign
    text = text.replace("\uff0b", "+")
    return text


def _normalize_dot_separators(text: str) -> str:
    """Convert dot-separated numbers to dash-separated.

    555.123.4567 -> 555-123-4567
    Only when dots appear between digit groups.
    """
    return re.sub(
        r"(\d)\s*\.\s*(\d)",
        r"\1-\2",
        text,
    )


def _normalize_word_separators(text: str) -> str:
    """Convert word-based obfuscation.

    'five five five one two three four five six seven' is too complex,
    but handle simple patterns like phone numbers with spelled-out separators.
    """
    # "555 dash 123 dash 4567" or "555 hyphen 123 hyphen 4567"
    text = re.sub(r"(\d)\s+(?:dash|hyphen)\s+(\d)", r"\1-\2", text, flags=re.IGNORECASE)
    return text


def _collapse_excessive_spaces(text: str) -> str:
    """Collapse spaces within digit sequences.

    '5 5 5 1 2 3 4 5 6 7' -> '5551234567'
    Only when there's a long sequence of single-spaced digits.
    """
    # Match 7+ digits separated by single spaces
    def _collapse(m: re.Match) -> str:
        return m.group(0).replace(" ", "")

    return re.sub(r"(?:\d ){6,}\d", _collapse, text)


_PIPELINE = [
    _decode_html_entities,
    _decode_url_encoding,
    _replace_unicode_chars,
    _normalize_dot_separators,
    _normalize_word_separators,
    _collapse_excessive_spaces,
]


def deobfuscate(text: str) -> str:
    """Apply all phone number deobfuscation transformations.

    Processes text through a pipeline that converts common phone number
    obfuscation patterns back to standard formats.

    Args:
        text: Input text potentially containing obfuscated phone numbers.

    Returns:
        Text with obfuscated numbers converted to standard format.
    """
    for transform in _PIPELINE:
        text = transform(text)
    return text
