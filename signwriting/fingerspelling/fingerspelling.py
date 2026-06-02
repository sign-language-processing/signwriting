import functools
import json
import random
import re
from pathlib import Path
from typing import Dict, List, Union

from signwriting.utils.join_signs import join_signs_vertical, join_signs_horizontal

FINGERSPELLING_DIR = Path(__file__).parent / "data"

CharVariants = Union[List[str], Dict[str, Union[List[str], Dict[str, List[str]]]]]


@functools.lru_cache(maxsize=None)
def get_chars(language: str) -> Dict[str, CharVariants]:
    if "-" in language:
        language = language.split("-")[2]

    with open(FINGERSPELLING_DIR / f"{language}.json", "r", encoding="utf-8") as f:
        return {char.lower(): variants for char, variants in json.load(f).items()}


def variant_signs(char_variants: CharVariants, variants: List[str] = None) -> List[str]:
    if isinstance(char_variants, dict):
        for variation in variants or []:
            if variation in char_variants["variations"]:
                return char_variants["variations"][variation]
        return char_variants["default"]
    return char_variants


def spell(word: str, language=None, chars=None, vertical=True, variants=None) -> Union[str, None]:
    if chars is None:
        if language is None:
            raise ValueError("Either language or chars must be provided")
        chars = get_chars(language)

    sl = []
    caret = 0
    while caret < len(word):
        found = False
        for c, options in chars.items():
            if word[caret:caret + len(c)].lower() == c:
                sl.append(random.choice(variant_signs(options, variants)))
                caret += len(c)
                found = True
                break
        if not found:
            return None
    if vertical:
        return join_signs_vertical(*sl, spacing=5)
    return join_signs_horizontal(*sl, spacing=5)


def tokenize(text: str) -> List[str]:
    return re.findall(r'[^\W_]+|[^\w\s]|_', text)


def spell_text(text: str, language=None, vertical=True, variants=None) -> Union[str, None]:
    spellings = [spell(token, language=language, vertical=vertical, variants=variants)
                 for token in tokenize(text)]
    if any(spelling is None for spelling in spellings):
        return None
    return " ".join(spellings)


if __name__ == "__main__":
    print(spell_text("custom prited circuit board", language='en-us-ase-asl', vertical=True))
