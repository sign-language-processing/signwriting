import copy
import functools
import json
import re
import unicodedata
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path
from typing import Union, Optional

from epitran import Epitran

from signwriting.formats.fsw_to_sign import fsw_to_sign
from signwriting.formats.sign_to_fsw import sign_to_fsw
from signwriting.formats.fsw_to_swu import fsw2swu
from signwriting.utils.join_signs import join_signs_horizontal, sign_from_symbols

MOUTHING_INDEX = Path(__file__).parent / "mouthing.json"

# Punctuation, separators and digits. ASR tokenizers emit hyphenated/em-dashed compounds and bare
# numerals ("all-day", "has—what", "7-year-old"); break on them instead of failing the whole word.
# Numerals have no mouthing at all, so a word made only of digits still yields None.
WORD_BREAK_CATEGORIES = "PZN"

# Diacritics and suprasegmentals that qualify a phoneme without giving it its own mouth picture:
# nasalization, non-syllabic, palatalization, tie bars (Mn); length and stress marks (Lm); tone
# letters (Sk). Only consulted after longest-match fails, so "iː" still beats "ɪ" + dropped "ː".
IGNORED_MARK_CATEGORIES = ("Mn", "Lm", "Sk")


@dataclass
class MouthingResult:
    ipa: str
    fsw: Optional[str]
    swu: Optional[str]


@functools.cache
def get_mouthings():
    with open(MOUTHING_INDEX, "r", encoding="utf-8") as f:
        mouthings = json.load(f)

    # Decompose keys so precomposed vowels ("ũ", "õ") reduce to a base letter plus a skippable mark.
    # "ç" decomposes too, but stays a 2-character key that longest-match still prefers over "c".
    mouthings = {unicodedata.normalize("NFD", symbol): info for symbol, info in mouthings.items()}

    for info in list(mouthings.values()):
        if "alternatives" in info:
            for alternative in info["alternatives"]:
                mouthings[unicodedata.normalize("NFD", alternative)] = info

    return mouthings


@functools.cache
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

    word = unicodedata.normalize("NFD", word)

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
            if unicodedata.category(word[caret]) in IGNORED_MARK_CATEGORIES:
                caret += 1
                continue
            print(f"Symbol not found: {word[caret]}")
            return None
    if not sl:
        return None
    return join_signs_horizontal(*sl, spacing=-10)


def split_ipa_words(characters: str) -> list[str]:
    is_break = lambda char: unicodedata.category(char)[0] in WORD_BREAK_CATEGORIES
    return ["".join(chars) for brk, chars in groupby(characters, is_break) if not brk]


def mouth_ipa(characters: str, aspiration=False) -> Union[str, None]:
    words = [mouth_ipa_single(word, aspiration=aspiration) for word in split_ipa_words(characters)]
    if not words or any(word is None for word in words):
        return None

    return join_signs_horizontal(*words, spacing=10)


@functools.cache
def get_epitran(language: str) -> Epitran:
    # Construction loads language data from disk (~0.7s), so reuse instances across calls
    return Epitran(language, ligatures=True)


def mouth(word: str, language: str, aspiration=False) -> MouthingResult:
    epi = get_epitran(language)
    ipa = epi.transliterate(word)

    mouthing_fsw = mouth_ipa(ipa, aspiration=aspiration)
    if mouthing_fsw is None:
        print(f"Failed to mouth {word}, IPA: {ipa}")

    mouthing_swu = fsw2swu(mouthing_fsw) if mouthing_fsw else None

    return MouthingResult(ipa=ipa, fsw=mouthing_fsw, swu=mouthing_swu)


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
