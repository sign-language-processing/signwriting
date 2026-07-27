import pytest

from signwriting.mouthing.mouthing import mouth_ipa

# IPA transcriptions that used to return None because a single character had no mouthing entry.
# https://linear.app/rylo/issue/SIGN-752
CASES = [
    # ASR tokenization artifacts
    ("ɔl-dej", "all-day"),
    ("hæz—wʌt", "has—what"),
    ("bajɑləʤi,ɹajt", "biology,right"),
    ("ju.ɛs", "U.S"),
    ("sɪks-fɪɡjɚ", "six-figure"),
    # Symbols missing from the mouthing table
    ("kɾeo", "es: creo"),
    ("desaroʝaɾ", "es: desarrollar"),
    ("plɛʀ", "fr: plaire"),
    ("sɥis", "fr: suis"),
    ("kɔ̃tɑ̃t", "fr: contente"),
    ("kɔstbaːrstən", "de: kostbarsten"),
    ("aʊ̯s", "de: aus"),
    ("ʨʲto", "ru: что"),
    ("utiliʦiamo", "it: Utilizziamo"),
    ("prodotːo", "it: prodotto"),
    ("paxɔvɨx", "pl: Pachowych"),
    ("faktɨt͡ʂɲɛ", "pl: faktycznie"),
    ("kõ", "pt: com"),
    ("ʈ͡ʂʊŋ˥kwo˧˥", "zh: 中国"),
    ("aɾiɡatoː", "ja: ありがとう"),
    ("han˧˩˧k͈ɯk̚", "ko: 한국"),
    ("ʔalʕarabijja", "ar: العربية"),
]


@pytest.mark.parametrize("ipa,word", CASES, ids=[word for _, word in CASES])
def test_mouths_without_returning_none(ipa: str, word: str):
    assert mouth_ipa(ipa) is not None, f"{word} ({ipa}) failed to mouth"


def test_digits_alone_have_no_mouthing():
    assert mouth_ipa("2014") is None


def test_long_vowel_still_distinct_from_short():
    assert mouth_ipa("iː") != mouth_ipa("ɪ")


def test_decomposition_does_not_collapse_cedilla_into_c():
    assert mouth_ipa("ç") != mouth_ipa("c")


def test_unknown_phoneme_still_fails_loudly():
    assert mouth_ipa("ʘ") is None
