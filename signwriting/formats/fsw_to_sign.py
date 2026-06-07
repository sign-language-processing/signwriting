import re

from signwriting.types import Sign


BOX_RE = re.compile(r"([BLMR])(\d{3})x(\d{3})")
SYMBOL_RE = re.compile(r"(S[123][0-9a-f]{2}[0-5][0-9a-f])(\d{3})x(\d{3})")


def fsw_to_sign(fsw: str) -> Sign:
    box = BOX_RE.search(fsw)
    if box is None:
        box_symbol = "M"
        box_position = (500, 500)
    else:
        box_symbol = box[1]
        box_position = (int(box[2]), int(box[3]))

    symbols = SYMBOL_RE.findall(fsw)

    return {
        "box": {
            "symbol": box_symbol,
            "position": box_position,
        },
        "symbols": [{
            "symbol": symbol,
            "position": (int(x), int(y)),
        } for symbol, x, y in symbols],
    }
