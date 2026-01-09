import re

import pandas as pd

from src.consts import AUTHOR_MAPPING


def normalize_author(author: str) -> str:
    """
    Normalize author name to canonical format: Фамилия Имя Отчество.

    Handles:
    - Different name orders (First Last vs Last First Middle)
    - Missing middle names
    - Typos (e.g., Апполон -> Аполлон)
    - ё/е variations
    - Pseudonyms are kept in original form
    """
    if pd.isna(author):
        return ""
    author = str(author).strip()
    return AUTHOR_MAPPING.get(author, author)


def normalize_poem_name(name: str) -> str:
    """
    Normalize poem name for display.

    Handles:
    - Removes trailing ellipsis (...)
    - Normalizes multiple spaces to single space
    - Converts ALL-UPPERCASE titles to proper case (except Roman numerals)
    """
    if pd.isna(name):
        return ""
    s = str(name).strip()
    s = re.sub(r"\.{2,}$", "", s)
    s = re.sub(r"\s+", " ", s)

    roman_numerals = {
        "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
        "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX",
    }
    abbreviations = {"NN", "ТВС", "ТБЦ", "МЮД"}

    if s.isupper():
        if s in roman_numerals or s in abbreviations:
            return s
        words = s.split()
        normalized_words = []
        for i, word in enumerate(words):
            if word in roman_numerals or word in abbreviations:
                normalized_words.append(word)
            elif i == 0:
                normalized_words.append(word.capitalize())
            else:
                normalized_words.append(word.lower())
        s = " ".join(normalized_words)
    return s


def normalize_poem_name_for_dedup(name: str) -> str:
    """
    Normalize poem name for duplicate detection.

    Returns lowercase version without trailing dots for comparison.
    """
    if pd.isna(name):
        return ""
    s = str(name).strip().lower()
    s = re.sub(r"\.{2,}$", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def normalize_text_for_comparison(text: str) -> str:
    """
    Normalize text for duplicate detection.

    Handles:
    - Multiple whitespace characters collapsed to single space
    - Different quote styles (« » " " ' ')
    - Different dash styles (— – ―)
    - Ellipsis (…) to dots (...)
    - ё/Ё to е/Е
    - Punctuation removed for fuzzy matching
    """
    if pd.isna(text):
        return ""
    s = str(text)
    s = re.sub(r"\s+", " ", s)
    s = s.replace("«", '"').replace("»", '"').replace(""", '"').replace(""", '"')
    s = s.replace("'", "'").replace("'", "'")
    s = s.replace("—", "-").replace("–", "-").replace("―", "-")
    s = s.replace("…", "...")
    s = s.replace("ё", "е").replace("Ё", "Е")
    s = re.sub(r"[.,;:!?]", "", s)
    s = s.strip().lower()
    return s
