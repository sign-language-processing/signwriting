from signwriting.types import Sign


def sign_to_fsw(sign: Sign) -> str:
    symbols = [sign["box"]] + sign["symbols"]
    symbols_str = [s["symbol"] + str(s["position"][0]) + 'x' + str(s["position"][1]) for s in symbols]
    return "".join(symbols_str)
