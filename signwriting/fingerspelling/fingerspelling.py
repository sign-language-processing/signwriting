import functools
import random
import re
from pathlib import Path
from typing import Union

from signwriting.utils.join_signs import join_signs_vertical, join_signs_horizontal

FINGERSPELLING_DIR = Path(__file__).parent / "data"


@functools.lru_cache(maxsize=None)
def get_chars_by(value: str, category: str):
    categories = ["LANGUAGE", "COUNTRY", "SIGNED", "NAME"]
    if category not in categories:
        raise ValueError(f"Category must be one of {categories}")
    category_index = categories.index(category)

    # iterate over the directory
    for file in FINGERSPELLING_DIR.iterdir():
        file_category = file.stem.split("-")[category_index]
        if file_category == value:
            return get_chars(file.stem)

    raise ValueError(f"Could not find a file with {category} {value}")


@functools.lru_cache(maxsize=None)
def get_chars(language: str):
    with open(FINGERSPELLING_DIR / f"{language}.txt", "r", encoding="utf-8") as f:
        content = re.sub(r'#.*$', '', f.read(), flags=re.MULTILINE)  # Remove comments
        lines = [line.strip().split(",") for line in content.splitlines() if len(line.strip()) > 0]
    return {first.lower(): others for [first, *others] in lines}


def spell(word: str, language=None, chars=None, vertical=True) -> Union[str, None]:
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
                sl.append(random.choice(options))
                caret += len(c)
                found = True
                break
        if not found:
            return None
    if vertical:
        return join_signs_vertical(*sl, spacing=5)
    return join_signs_horizontal(*sl, spacing=5)


if __name__ == "__main__":
    words = ["custom", "prited", "circuit", "board"]
    spellings = [spell(word, language='en-us-ase-asl', vertical=True) for word in words]
    print(" ".join(spellings))
