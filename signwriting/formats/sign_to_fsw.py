from itertools import chain

from signwriting.types import Sign


def sign_to_fsw(sign: Sign, fix_out_of_range: bool = True) -> str:
    symbols = [sign["box"]] + sign["symbols"]
    all_positions = list(chain.from_iterable([s["position"] for s in symbols]))
    if min(all_positions) < 250 or max(all_positions) > 750:
        if not fix_out_of_range:
            raise ValueError("Positions must be between 250 and 750")
        symbols = [{**s, "position": tuple(max(250, min(749, v)) for v in s["position"])} for s in symbols]
    symbols_str = [s["symbol"] + str(s["position"][0]) + 'x' + str(s["position"][1]) for s in symbols]
    return "".join(symbols_str)
