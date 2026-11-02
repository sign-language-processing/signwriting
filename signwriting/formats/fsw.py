"""Syntax validation for unstyled Formal SignWriting in ASCII (FSW)."""

import re

_SIGN = re.compile(
    r"(?:(?:A(?:S[123][0-9a-f]{2}[0-5][0-9a-f])+)?[BLMR]\d{3}x\d{3}"
    r"(?:S[123][0-9a-f]{2}[0-5][0-9a-f]\d{3}x\d{3})+|S38[7-9ab][0-5][0-9a-f]\d{3}x\d{3})",
    re.ASCII,
)


def is_fsw(text: str) -> bool:
    """Return whether text is a nonempty, whitespace-separated sequence of FSW signs.

    Accept optional sorting prefixes and standalone punctuation. Each signbox
    must contain at least one positioned symbol. Styling and partial signs are
    rejected. This checks syntax, not whether each symbol variant has a glyph.
    """
    signs = text.split()
    return bool(signs) and all(_SIGN.fullmatch(sign) for sign in signs)
