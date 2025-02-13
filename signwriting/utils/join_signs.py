from collections import namedtuple
from typing import List

from signwriting.formats.fsw_to_sign import fsw_to_sign
from signwriting.formats.sign_to_fsw import sign_to_fsw
from signwriting.types import Sign, SignSymbol
from signwriting.visualizer.visualize import get_symbol_size


def all_axis(_sign, axis):
    axis_index = 0 if axis == "x" else 1
    return [s["position"][axis_index] for s in _sign["symbols"]]


def init_join(*fsws: str):
    signs = [fsw_to_sign(fsw) for fsw in fsws if fsw is not None]
    return [sign for sign in signs if len(sign["symbols"]) > 0]


def join_signs_vertical(*fsws: str, spacing: int = 0):
    signs = init_join(*fsws)
    symbols = []
    accumulative_offset = 0

    for sign in signs:
        sign_min_y = min(all_axis(sign, "y"))
        sign_offset_y = accumulative_offset + spacing - sign_min_y
        accumulative_offset += (sign["box"]["position"][1] - sign_min_y) + spacing  # * 2

        for symbol in sign["symbols"]:
            symbols.append({
                "symbol": symbol["symbol"],
                "position": (symbol["position"][0], symbol["position"][1] + sign_offset_y)
            })

    new_sign = sign_from_symbols(symbols, fix_x=False)
    return sign_to_fsw(new_sign)


def join_signs_horizontal(*fsws: str, spacing: int = 0):
    signs = init_join(*fsws)
    symbols = []
    accumulative_offset = 0

    for sign in signs:
        sign_min_x = min(all_axis(sign, "x"))
        sign_offset_x = accumulative_offset + spacing - sign_min_x
        accumulative_offset += (sign["box"]["position"][0] - sign_min_x) + spacing  # * 2

        for symbol in sign["symbols"]:
            symbols.append({
                "symbol": symbol["symbol"],
                "position": (symbol["position"][0] + sign_offset_x, symbol["position"][1])
            })

    new_sign = sign_from_symbols(symbols, fix_y=False)
    return sign_to_fsw(new_sign)


Point = namedtuple("Point", ["x", "y"])


def sign_from_symbols(symbols: List[SignSymbol], fix_x=True, fix_y=True) -> Sign:
    min_p = Point(x=999, y=999)
    max_p = Point(x=0, y=0)
    for symbol in symbols:
        min_p = Point(x=min(min_p.x, symbol["position"][0]),
                      y=min(min_p.y, symbol["position"][1]))

        symbol_width, symbol_height = get_symbol_size(symbol["symbol"])
        max_p = Point(x=max(max_p.x, symbol["position"][0] + symbol_width),
                      y=max(max_p.y, symbol["position"][1] + symbol_height))

    box_p = Point(x=500 + (max_p.x - min_p.x) // 2,
                  y=500 + (max_p.y - min_p.y) // 2)
    box = {"symbol": "M", "position": box_p}
    size = Point(x=max_p.x - min_p.x,
                 y=max_p.y - min_p.y)

    for symbol in symbols:
        symbol_x, symbol_y = symbol["position"]
        if fix_x:
            symbol_x += box_p.x - min_p.x - size.x
        if fix_y:
            symbol_y += box_p.y - min_p.y - size.y
        symbol["position"] = (symbol_x, symbol_y)

    return {"box": box, "symbols": symbols}
