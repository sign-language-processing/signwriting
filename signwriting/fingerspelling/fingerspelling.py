import functools
import random
import re
from pathlib import Path
from typing import Union

from signwriting.utils.join_signs import join_signs

FINGERSPELLING_DIR = Path(__file__).parent / "data"


@functools.lru_cache(maxsize=None)
def get_chars(language: str):
    with open(FINGERSPELLING_DIR / f"{language}.txt", "r", encoding="utf-8") as f:
        content = re.sub(r'#.*$', '', f.read(), flags=re.MULTILINE)  # Remove comments
        lines = [line.strip().split(",") for line in content.splitlines() if len(line.strip()) > 0]
    return {first.lower(): others for [first, *others] in lines}


def spell(characters: str, language=None, chars=None) -> Union[str, None]:
    if chars is None:
        if language is None:
            raise ValueError("Either language or chars must be provided")
        chars = get_chars(language)

    sl = []
    caret = 0
    while caret < len(characters):
        found = False
        for c, options in chars.items():
            if characters[caret:caret + len(c)].lower() == c:
                sl.append(random.choice(options))
                caret += len(c)
                found = True
                break
        if not found:
            return None
    return join_signs(*sl, spacing=5)


if __name__ == "__main__":
    for word in ["12345", "hello", "Amit"]:
        print(word, spell(word, language='en-us-ase-asl'))
