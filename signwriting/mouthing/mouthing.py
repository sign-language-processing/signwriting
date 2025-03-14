import copy
import functools
import json
import re
from pathlib import Path
from typing import Union

from epitran import Epitran

from signwriting.formats.fsw_to_sign import fsw_to_sign
from signwriting.formats.sign_to_fsw import sign_to_fsw
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
    mouthings = copy.deepcopy(get_mouthings())

    for info in mouthings.values():
        if "S335" in info["writing"]:
            info["writing"] = re.sub(r"S335..\d{3}x\d{3}", "", info["writing"])
        sign = fsw_to_sign(info["writing"])
        sign = sign_from_symbols(sign["symbols"])
        info["writing"] = sign_to_fsw(sign) if len(sign["symbols"]) > 0 else ""

    return mouthings


def mouth_ipa_single(word: str, aspiration=False) -> Union[str, None]:
    mouthings = get_mouthings() if aspiration else get_mouthings_without_aspiration()

    # Make sure to look at long symbols first
    mouthings = sorted(list(mouthings.items()), key=lambda x: len(x[0]), reverse=True)

    # Remove syllabic consonant markers
    word = word.replace("̩", "")

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

    mouthing_fsw = mouth_ipa(ipa, aspiration=aspiration)
    if mouthing_fsw is None:
        print(f"Failed to mouth {word}, IPA: {ipa}")
    return mouthing_fsw


if __name__ == "__main__":
    for _word in ["hello", "Amit", "high", "sign writing", "SignWriting"]:
        print(_word, mouth(_word, language='eng-Latn'))

    # Make sure all of English is covered https://www.vocabulary.com/resources/ipa-pronunciation/
    english_words = [
        "pit", "lip", "bit", "tub", "tip", "sit", "dig", "sad", "cup", "sky", "click", "guy", "bag", "my", "jam", "not",
        "ran", "sing", "finger", "link", "check", "etch", "just", "giant", "judge", "age", "fish", "cuff", "vowel",
        "leave", "thigh", "breath", "thy", "father", "breathe", "sip", "mass", "zip", "jazz", "shop", "wish", "genre",
        "pleasure", "beige", "house", "ahead", "wit", "swap", "yes", "young", "rip", "water", "write", "lap", "pull",
        "feet", "seat", "me", "happy", "sit", "gym", "elate", "break", "say", "let", "best", "cat", "mad", "but",
        "trust", "under", "comma", "bazaar", "the", "goose", "rude", "cruel", "foot", "took", "boat", "owe", "no",
        "frog", "bought", "launch", "not", "father", "buy", "aisle", "isle", "cow", "mouth", "soil", "boy",
        "participate"
    ]
    from tqdm import tqdm

    for _word in tqdm(english_words):
        mouth(_word, language='eng-Latn')
