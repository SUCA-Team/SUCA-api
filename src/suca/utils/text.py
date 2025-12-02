"""Text processing utilities."""

import re


def normalize_japanese_text(text: str) -> str:
    """Normalize Japanese text for better matching."""
    if not text:
        return text

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text.strip())

    return text


def extract_kanji(text: str) -> list[str]:
    """Extract kanji characters from text."""
    if not text:
        return []

    # Unicode ranges for kanji
    kanji_pattern = r"[\u4e00-\u9faf]+"
    return re.findall(kanji_pattern, text)


def extract_hiragana(text: str) -> list[str]:
    """Extract hiragana characters from text."""
    if not text:
        return []

    # Unicode range for hiragana
    hiragana_pattern = r"[\u3040-\u309f]+"
    return re.findall(hiragana_pattern, text)


def extract_katakana(text: str) -> list[str]:
    """Extract katakana characters from text."""
    if not text:
        return []

    # Unicode range for katakana
    katakana_pattern = r"[\u30a0-\u30ff]+"
    return re.findall(katakana_pattern, text)


def is_japanese_text(text: str) -> bool:
    """Check if text contains Japanese characters."""
    if not text:
        return False

    japanese_pattern = r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]"
    return bool(re.search(japanese_pattern, text))
