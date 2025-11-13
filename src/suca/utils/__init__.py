"""Utility functions and helpers."""

from .logging import logger, setup_logging
from .text import (
    normalize_japanese_text,
    extract_kanji,
    extract_hiragana,
    extract_katakana,
    is_japanese_text
)

__all__ = [
    "logger",
    "setup_logging",
    "normalize_japanese_text",
    "extract_kanji",
    "extract_hiragana", 
    "extract_katakana",
    "is_japanese_text",
]