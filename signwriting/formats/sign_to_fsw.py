from itertools import chain

from signwriting.types import Sign


def _fit_positions(symbols: list) -> list:
    # One uniform scale (shrink only) and shift for the whole sign, centered on 500x500
    xs, ys = [s["position"][0] for s in symbols], [s["position"][1] for s in symbols]
    scale = min(1, 500 / max(max(xs) - min(xs), max(ys) - min(ys), 1))
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    return [{**s, "position": (round(500 + (s["position"][0] - cx) * scale),
                               round(500 + (s["position"][1] - cy) * scale))} for s in symbols]


def sign_to_fsw(sign: Sign, fix_out_of_range: bool = True) -> str:
    symbols = [sign["box"]] + sign["symbols"]
    all_positions = list(chain.from_iterable([s["position"] for s in symbols]))
    if min(all_positions) < 250 or max(all_positions) > 750:
        if not fix_out_of_range:
            raise ValueError("Positions must be between 250 and 750")
        symbols = _fit_positions(symbols)
    symbols_str = [s["symbol"] + str(s["position"][0]) + 'x' + str(s["position"][1]) for s in symbols]
    return "".join(symbols_str)
