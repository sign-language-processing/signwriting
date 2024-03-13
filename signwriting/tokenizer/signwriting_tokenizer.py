import re
from itertools import chain
from typing import List

from signwriting.formats.fsw_to_sign import fsw_to_sign
from signwriting.tokenizer.base_tokenizer import BaseTokenizer
from signwriting.types import SignSymbol


class SignWritingTokenizer(BaseTokenizer):

    def __init__(self, starting_index=None, **kwargs):
        super().__init__(tokens=SignWritingTokenizer.tokens(), starting_index=starting_index, **kwargs)

    @staticmethod
    def tokens():
        box_symbols = ["B", "L", "M", "R"]

        base_symbols = ["S" + hex(i)[2:] + hex(j)[2:] for i in range(0x10, 0x38 + 1) for j in range(0x0, 0xf + 1)]
        base_symbols.remove("S38c")
        base_symbols.remove("S38d")
        base_symbols.remove("S38e")
        base_symbols.remove("S38f")

        rows = ["r" + hex(j)[2:] for j in range(0x0, 0xf + 1)]
        cols = ["c0", "c1", "c2", "c3", "c4", "c5"]

        positions = ["p" + str(p) for p in range(250, 750)]

        return list(chain.from_iterable([box_symbols, base_symbols, rows, cols, positions]))

    @staticmethod
    def tokenize_symbol(symbol: SignSymbol, box_position=False):
        if symbol["symbol"] in ["B", "L", "M", "R"]:
            yield symbol["symbol"]

            if box_position:
                yield "p" + str(symbol["position"][0])
                yield "p" + str(symbol["position"][1])
            else:
                # We position all boxes at 500x500, since the position can be inferred from the other symbols
                yield "p500"
                yield "p500"
        else:
            yield symbol["symbol"][:4]  # Break symbol down
            num = int(symbol["symbol"][4:], 16)
            yield "c" + hex(num // 0x10)[2:]
            yield "r" + hex(num % 0x10)[2:]

            yield "p" + str(symbol["position"][0])
            yield "p" + str(symbol["position"][1])

    def text_to_tokens(self, text: str, box_position=False) -> List[str]:
        text = re.sub(r'([MLBR])', r' \1', text).strip()  # add spaces
        text = re.sub(r'\bA\w*\b', '', text)  # remove sign prefix
        text = re.sub(r' +', r' ', text)  # remove consecutive spaces
        text = text.strip()
        signs = [fsw_to_sign(f) for f in text.split(" ")]
        for sign in signs:
            yield from SignWritingTokenizer.tokenize_symbol(sign["box"], box_position=box_position)
            for symbol in sign["symbols"]:
                yield from SignWritingTokenizer.tokenize_symbol(symbol)

    def tokens_to_text(self, tokens: List[str]) -> str:
        tokenized = " ".join(tokens)
        tokenized = re.sub(r' p(\d*) p(\d*)', r'\1x\2', tokenized)
        tokenized = re.sub(r' c(\d)\d? r(.)', r'\1\2', tokenized)
        tokenized = re.sub(r' c(\d)\d?', r'\1 0', tokenized)
        tokenized = re.sub(r' r(.)', r'0\1', tokenized)

        tokenized = tokenized.replace(' ', '')
        tokenized = re.sub(r'(\d)([MBLR])', r'\1 \2', tokenized)

        return tokenized
