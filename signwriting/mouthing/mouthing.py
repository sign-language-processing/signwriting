import functools
import json
import re
from pathlib import Path
from typing import Union

from epitran import Epitran
from signwriting.formats.sign_to_fsw import sign_to_fsw

from signwriting.formats.fsw_to_sign import fsw_to_sign

from signwriting.utils.join_signs import join_signs_horizontal, sign_from_symbols

MOUTHING_INDEX = Path(__file__).parent / "mouthing.json"


@functools.lru_cache()
def get_mouthings():
    with open(MOUTHING_INDEX, "r", encoding="utf-8") as f:
        mouthings = json.load(f)

    for info in list(mouthings.values()):
        if "alternatives" in info:
            for alternative in info["alternatives"]:
                mouthings[alternative] = info

    return mouthings


@functools.lru_cache()
def get_mouthings_without_aspiration():
    mouthings = get_mouthings()

    for info in mouthings.values():
        if "S335" in info["writing"]:
            info["writing"] = re.sub(r"S335..\d{3}x\d{3}", "", info["writing"])
        sign = fsw_to_sign(info["writing"])
        sign = sign_from_symbols(sign["symbols"])
        info["writing"] = sign_to_fsw(sign)

    return mouthings


def mouth_ipa_single(word: str, aspiration=False) -> Union[str, None]:
    mouthings = get_mouthings() if aspiration else get_mouthings_without_aspiration()

    # Make sure to look at long symbols first
    mouthings = sorted(list(mouthings.items()), key=lambda x: len(x[0]), reverse=True)

    sl = []
    caret = 0
    while caret < len(word):
        found = False
        for symbol, info in mouthings:
            if word[caret:caret + len(symbol)].lower() == symbol:
                sl.append(info["writing"])
                caret += len(symbol)
                found = True
                break
        if not found:
            print(f"Symbol not found: {word[caret:caret + 1]}")
            return None
    return join_signs_horizontal(*sl, spacing=-10)


def mouth_ipa(characters: str, aspiration=False) -> Union[str, None]:
    words = [mouth_ipa_single(word, aspiration=aspiration) for word in characters.split(" ")]
    if any(word is None for word in words):
        return None

    return join_signs_horizontal(*words, spacing=10)


def mouth(word: str, language: str, aspiration=False):
    epi = Epitran(language, ligatures=True)
    ipa = epi.transliterate(word)
    return mouth_ipa(ipa, aspiration=aspiration)


if __name__ == "__main__":
    for _word in ["hello", "Amit", "high", "sign writing", "SignWriting"]:
        print(_word, mouth(_word, language='eng-Latn'))
