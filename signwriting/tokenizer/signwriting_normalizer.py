from functools import lru_cache

from signwriting.tokenizer.signwriting_tokenizer import SignWritingTokenizer


@lru_cache(maxsize=None)
def get_tokenizer():
    return SignWritingTokenizer()


def normalize_signwriting(fsw: str) -> str:
    tokenizer = get_tokenizer()
    tokens = list(tokenizer.text_to_tokens(fsw, box_position=True))
    return tokenizer.tokens_to_text(tokens)
