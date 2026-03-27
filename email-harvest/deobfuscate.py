"""Email deobfuscation engine.

Transforms common obfuscation patterns back into standard email format
before regex extraction. This is the primary differentiator of email-harvest.
"""

import html
import re
from urllib.parse import unquote


def _replace_bracket_at(text: str) -> str:
    """Replace [at] [AT] [At] variations."""
    return re.sub(
        r"\s*\[\s*[aA][tT]\s*\]\s*",
        "@",
        text,
    )


def _replace_bracket_dot(text: str) -> str:
    """Replace [dot] [DOT] [Dot] variations."""
    return re.sub(
        r"\s*\[\s*[dD][oO][tT]\s*\]\s*",
        ".",
        text,
    )


def _replace_paren_at(text: str) -> str:
    """Replace (at) (AT) variations."""
    return re.sub(
        r"\s*\(\s*[aA][tT]\s*\)\s*",
        "@",
        text,
    )


def _replace_paren_dot(text: str) -> str:
    """Replace (dot) (DOT) variations."""
    return re.sub(
        r"\s*\(\s*[dD][oO][tT]\s*\)\s*",
        ".",
        text,
    )


def _replace_curly_at(text: str) -> str:
    """Replace {at} {AT} variations."""
    return re.sub(
        r"\s*\{\s*[aA][tT]\s*\}\s*",
        "@",
        text,
    )


def _replace_curly_dot(text: str) -> str:
    """Replace {dot} {DOT} variations."""
    return re.sub(
        r"\s*\{\s*[dD][oO][tT]\s*\}\s*",
        ".",
        text,
    )


def _replace_word_at(text: str) -> str:
    r"""Replace ' at ' ' AT ' as word boundaries: user at domain dot com.

    Only match when surrounded by non-space word chars to avoid false positives.
    """
    return re.sub(
        r"(\S)\s+[aA][tT]\s+(\S)",
        r"\1@\2",
        text,
    )


def _replace_word_dot(text: str) -> str:
    r"""Replace ' dot ' ' DOT ' as word boundaries."""
    return re.sub(
        r"(\S)\s+[dD][oO][tT]\s+(\S)",
        r"\1.\2",
        text,
    )


def _replace_spaced_at(text: str) -> str:
    """Replace spaced @ signs: 'user @ domain'."""
    return re.sub(
        r"(\S)\s+@\s+(\S)",
        r"\1@\2",
        text,
    )


def _replace_spaced_dot_in_email(text: str) -> str:
    """Replace spaced dots after @ sign: 'user@domain . com'."""
    return re.sub(
        r"(@\S+)\s+\.\s+(\S)",
        r"\1.\2",
        text,
    )


def _decode_html_entities(text: str) -> str:
    """Decode HTML entities: &#64; -> @, &#46; -> ., &commat; -> @."""
    return html.unescape(text)


def _decode_url_encoding(text: str) -> str:
    """Decode URL-encoded characters: %40 -> @."""
    return unquote(text)


def _replace_unicode_at(text: str) -> str:
    """Replace unicode @ alternatives."""
    # ＠ (fullwidth @), ⓐ (circled a used sometimes)
    return text.replace("\uff20", "@").replace("\u24d0", "@")


# Ordered pipeline of transformations
_PIPELINE = [
    _decode_html_entities,
    _decode_url_encoding,
    _replace_unicode_at,
    _replace_bracket_at,
    _replace_bracket_dot,
    _replace_paren_at,
    _replace_paren_dot,
    _replace_curly_at,
    _replace_curly_dot,
    _replace_word_at,
    _replace_word_dot,
    _replace_spaced_at,
    _replace_spaced_dot_in_email,
]


def deobfuscate(text: str) -> str:
    """Apply all deobfuscation transformations to text.

    Processes the text through a pipeline of transformations that convert
    common email obfuscation patterns back to standard email format.

    Args:
        text: Input text potentially containing obfuscated email addresses.

    Returns:
        Text with obfuscated emails converted to standard format.
    """
    for transform in _PIPELINE:
        text = transform(text)
    return text
