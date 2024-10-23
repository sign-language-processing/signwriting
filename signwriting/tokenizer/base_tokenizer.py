from __future__ import annotations

from typing import List


class BaseTokenizer:

    # pylint: disable=too-many-arguments, too-many-instance-attributes
    def __init__(self,
                 tokens: List[str],
                 starting_index=None,
                 init_token="[CLS]",
                 eos_token="[SEP]",
                 pad_token="[PAD]",
                 unk_token="[UNK]"):
        if starting_index is None:
            starting_index = 4

        self.pad_token = pad_token
        self.bos_token = init_token
        self.eos_token = eos_token
        self.unk_token = unk_token

        self.i2s = {(i + starting_index): c for i, c in enumerate(tokens)}
        # Following the same ID scheme as JoeyNMT
        self.i2s[0] = self.unk_token
        self.i2s[1] = self.pad_token
        self.i2s[2] = self.bos_token
        self.i2s[3] = self.eos_token
        self.s2i = {c: i for i, c in self.i2s.items()}

        self.pad_token_id = self.s2i[self.pad_token]
        self.bos_token_id = self.s2i[self.bos_token]
        self.eos_token_id = self.s2i[self.eos_token]
        self.unk_token_id = self.s2i[self.unk_token]

    def __len__(self):
        return len(self.i2s)

    def vocab(self):
        return list(self.i2s.values())

    def text_to_tokens(self, text: str) -> List[str]:
        raise NotImplementedError()

    def tokens_to_text(self, tokens: List[str]) -> str:
        raise NotImplementedError()

    def tokenize(self, text: str, bos=False, eos=False):
        tokens = [self.s2i[c] for c in self.text_to_tokens(text)]
        if bos:
            tokens.insert(0, self.bos_token_id)
        if eos:
            tokens.append(self.eos_token_id)

        return tokens

    def detokenize(self, tokens: List[int]):
        if len(tokens) == 0:
            return ""
        if tokens[0] == self.bos_token_id:
            tokens = tokens[1:]
        if tokens[-1] == self.eos_token_id:
            tokens = tokens[:-1]

        try:
            padding_index = tokens.index(self.pad_token_id)
            tokens = tokens[:padding_index]
        except ValueError:
            pass

        return self.tokens_to_text([self.i2s[t] for t in tokens])
