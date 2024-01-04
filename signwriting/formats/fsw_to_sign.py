import re

from signwriting.types import Sign


def fsw_to_sign(fsw: str) -> Sign:
    boxes = re.finditer(r'([BLMR])(\d{3})x(\d{3})', fsw)
    box = next(boxes, None)
    # pylint: disable=invalid-name
    box_symbol, x, y = box.groups() if box is not None else ("M", 500, 500)

    symbols = re.findall(r'(S[123][0-9a-f]{2}[0-5][0-9a-f])(\d{3})x(\d{3})', fsw)

    return {
        "box": {
            "symbol": box_symbol,
            "position": (int(x), int(y))
        },
        "symbols": [{
            "symbol": s[0],
            "position": (int(s[1]), int(s[2]))
        } for s in symbols]
    }
