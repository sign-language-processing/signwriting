from typing import TypedDict, Tuple, List


class SignSymbol(TypedDict):
    symbol: str
    position: Tuple[int, int]


class Sign(TypedDict):
    box: SignSymbol
    symbols: List[SignSymbol]
