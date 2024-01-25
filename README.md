# SignWriting

Python utilities for SignWriting.

## Installation

```bash
pip install git+https://github.com/sign-language-processing/signwriting
```

## Utilities

### `signwriting.formats`

This module provides utilities for converting between different formats of SignWriting.
We include a few examples:

1. To parse an FSW string into a [`Sign`](signwriting/types.py) object, representing the sign as a dictionary:

```python
from signwriting.formats.fsw_to_sign import fsw_to_sign

fsw_to_sign("M123x456S1f720487x492")
# {'box': {'symbol': 'M', 'position': (123, 456)}, 'symbols': [{'symbol': 'S1f720', 'position': (487, 492)}]}
```

2. To convert a SignWriting string in SWU format to FSW format:

```python
from signwriting.formats.swu_to_fsw import swu2fsw

swu2fsw('𝠃𝤟𝤩񋛩𝣵𝤐񀀒𝤇𝣤񋚥𝤐𝤆񀀚𝣮𝣭')
# M525x535S2e748483x510S10011501x466S2e704510x500S10019476x475
```

### `signwriting.tokenizer`

This module provides utilities for tokenizing SignWriting strings for use in NLP tasks[^1].
We include a few usage non-exhaustive examples:

1. To tokenize a SignWriting string into a list of tokens:

```python
from signwriting.tokenizer import SignWritingTokenizer

tokenizer = SignWritingTokenizer()

fsw = 'M123x456S1f720487x492S1f720487x492'
tokens = list(tokenizer.text_to_tokens(fsw, box_position=True))
# ['M', 'p123', 'p456', 'S1f7', 'c2', 'r0', 'p487', 'p492', 'S1f7', 'c2', 'r0', 'p487', 'p492'])
```

2. To convert a list of tokens back to a SignWriting string:

```python
tokenizer.tokens_to_text(tokens)
# M123x456S1f720487x492S1f720487x492
```

3. For machine learning purposes, we can convert the tokens to a list of integers:

```python
tokenizer.tokenize(fsw, bos=False, eos=False)
# [6, 932, 932, 255, 678, 660, 919, 924, 255, 678, 660, 919, 924]
```

4. Or to remove 'A' information, and separate signs by spaces, we can use:

```python
from signwriting.tokenizer import normalize_signwriting

normalize_signwriting(fsw)
```

### `signwriting.visualizer`

This module is used to visualize SignWriting strings as images.
Unlike [sutton-signwriting/font-db](https://github.com/sutton-signwriting/font-db/) which it is based on, this module
does not support custom styling. Benchmarks show that this module is ~5000x faster than the original implementation.

```python
from signwriting.visualizer.visualize import signwriting_to_image

fsw = "AS10011S10019S2e704S2e748M525x535S2e748483x510S10011501x466S20544510x500S10019476x475"
signwriting_to_image(fsw)
```

![AS10011S10019S2e704S2e748M525x535S2e748483x510S10011501x466S20544510x500S10019476x475](signwriting/visualizer/test_assets/AS10011S10019S2e704S2e748M525x535S2e748483x510S10011501x466S20544510x500S10019476x475.png)

### `signwriting.utils`

This module includes general utilities that were not covered in the other modules.

1. `join_signs` joins a list of signs into a single sign.
   This is useful for example for fingerspelling words out of individual character signs.

```python
from signwriting.utils.join_signs import join_signs

char_a = 'M507x507S1f720487x492'
char_b = 'M507x507S14720493x485'
result_sign = join_signs(char_a, char_b)
# M500x500S1f720487x493S14720493x508
```

## References

[^1]: Amit Moryossef, Zifan Jiang.

2023. [SignBank+: Preparing a Multilingual Sign Language Dataset for Machine Translation Using Large Language Models](https://arxiv.org/abs/2309.11566).
