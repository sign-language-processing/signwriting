from signwriting.formats.fsw_to_sign import fsw_to_sign
from signwriting.formats.sign_to_fsw import sign_to_fsw
from signwriting.types import Sign


def all_ys(_sign):
    return [s["position"][1] for s in _sign["symbols"]]


def join_signs(*fsws: str, spacing: int = 0):
    signs = [fsw_to_sign(fsw) for fsw in fsws]
    new_sign: Sign = {"box": {"symbol": "M", "position": (500, 500)}, "symbols": []}

    accumulative_offset = 0

    for sign in signs:
        sign_min_y = min(all_ys(sign))
        sign_offset_y = accumulative_offset + spacing - sign_min_y
        accumulative_offset += (sign["box"]["position"][1] - sign_min_y) + spacing  # * 2

        new_sign["symbols"] += [{
            "symbol": s["symbol"],
            "position": (s["position"][0], s["position"][1] + sign_offset_y)
        } for s in sign["symbols"]]

    # Recenter around box center
    sign_middle = max(all_ys(new_sign)) // 2

    for symbol in new_sign["symbols"]:
        symbol["position"] = (symbol["position"][0],
                              new_sign["box"]["position"][1] - sign_middle + symbol["position"][1])

    return sign_to_fsw(new_sign)
