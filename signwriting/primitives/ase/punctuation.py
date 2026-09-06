PUNCTUATION = {
    ",": "S38700463x496",
    ".": "S38800464x496",
    ";": "S38900464x496",
    ":": "S38a00464x496",
    "(": "S38b00464x496",
    ")": "S38b04464x496",
}


def construct_punctuation(character: str) -> str:
    try:
        return PUNCTUATION[character]
    except KeyError as error:
        raise ValueError(f"Unsupported punctuation: {character!r}") from error


def generate_punctuation():
    yield from PUNCTUATION.items()
