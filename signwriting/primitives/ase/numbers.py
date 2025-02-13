import locale
import math
import random
from decimal import Decimal
from functools import lru_cache
from typing import Union, Tuple

from signwriting.fingerspelling.fingerspelling import get_chars, spell
from signwriting.formats.fsw_to_sign import fsw_to_sign
from signwriting.formats.sign_to_fsw import sign_to_fsw
from signwriting.utils.join_signs import join_signs_horizontal, join_signs_vertical, sign_from_symbols

SPELLING_LANGUAGE_CODE = 'en-us-ase-asl'

locale.setlocale(locale.LC_ALL, 'en_US')


def _get_base_symbol(fsw: str) -> str:
    sign = fsw_to_sign(fsw)
    return sign['symbols'][0]['symbol']


@lru_cache(maxsize=1)
def _get_basic_integers():
    asl_spelling = get_chars(SPELLING_LANGUAGE_CODE)
    asl_digits = {int(k): v[0] for k, v in asl_spelling.items() if k.isdigit()}
    low_teens = {
        10: "M513x528S1f540486x504S2a508492x472",
        11: "M511x520S10000488x490S21d00493x480",
        12: "M509x521S10e00491x491S21d00491x480",
        13: "M516x517S13200492x492S22114484x482",
        14: "M513x515S14700493x493S22114487x486",
        15: "M513x517S22114487x482S15d00494x490",
    }
    # TODO: create a "replace symbol" method that replaces the symbol while re-centering it if it is bigger.
    high_teens = {(10 + k): f"M521x520{_get_base_symbol(asl_digits[k])[:4]}10480x491S2e008502x479"
                  for k in range(6, 10)}
    same_digit = {(10 * k + k): f"M518x524{_get_base_symbol(asl_digits[k])[:4]}50482x476S2890a489x509"
                  for k in range(2, 10)}
    hundreds = {
        (100 * k): join_signs_horizontal(asl_digits[k], "M520x512S16d20481x492S2f900509x488S26506504x496", spacing=8)
        for k in range(1, 10)}

    thousands_fsw = "M521x538{base}20500x461S20500478x523S15a38491x511S18051495x513S22a04502x493"
    thousands = {(1000 * k): thousands_fsw.format(base=_get_base_symbol(asl_digits[k])[:4])
                 for k in range(1, 10)}
    primitives = {
        **asl_digits,
        **low_teens,
        **high_teens,
        20: "M517x513S22114484x488S1f420488x498",
        21: "M516x515S1e020493x485S21802483x497",
        22: "M518x524S10e50482x476S2890a489x509",
        23: "M519x517S12420481x487S22114493x484",
        25: "M524x514S1c520494x486S22114477x487",
        **same_digit,
        **hundreds,
        **thousands,
    }
    # All other two digit number are spelled (38 => 3, 8)
    for i in range(20, 100):
        if i not in primitives:
            primitives[i] = spell(str(i), language=SPELLING_LANGUAGE_CODE, vertical=False)

    return primitives


def construct_integer(number: int, recursive=False) -> Union[str, None]:
    if recursive and number == 0:
        return None

    basic_integers = _get_basic_integers()
    if number < 100:
        return basic_integers[number]
    if number < 1_000:
        if number % 100 == 0:
            return basic_integers[number]
        hundreds = construct_integer(number // 100)
        c_letter = spell("C", language=SPELLING_LANGUAGE_CODE)
        return join_signs_horizontal(hundreds, c_letter, construct_integer(number % 100), spacing=8)
    if number < 10_000:
        thousands = basic_integers[(number // 1000) * 1000]
        other_signs = construct_integer(number % 1000, recursive=True)
        return join_signs_horizontal(thousands, other_signs, spacing=8)
    if number < 1_000_000:
        thousand_sign = "M521x514S20500479x499S15a38492x487S18051496x489"
        thousands = construct_integer(number // 1000)
        other_signs = construct_integer(number % 1000, recursive=True)
        return join_signs_horizontal(thousands, thousand_sign, other_signs, spacing=8)
    if number < 1_000_000_000:
        million_sign = "M528x514S20500486x489S15a38499x487S20500486x503S18051503x489S26500471x493"
        millions = construct_integer(number // 1_000_000)
        other_signs = construct_integer(number % 1_000_000, recursive=True)
        return join_signs_horizontal(millions, million_sign, other_signs, spacing=8)
    if number < 1_000_000_000_000:
        billion_sign = "M529x519S20500485x495S15a38498x488S20500485x508S26500470x496S20500485x482S14b51504x495"
        billions = construct_integer(number // 1_000_000_000)
        other_signs = construct_integer(number % 1_000_000_000, recursive=True)
        return join_signs_horizontal(billions, billion_sign, other_signs, spacing=8)
    raise ValueError(f"Number too large {number}")


def construct_float(number: float) -> str:
    integer_part = int(number)
    integer_sign = construct_integer(integer_part)
    # get float part until the zeros
    float_part = 0
    number_remainder = number - integer_part
    if number_remainder == 0:
        return integer_sign

    text_number_remainder = str(Decimal(number_remainder).quantize(Decimal('1.0000000000'))).split(".")[1]
    shift = 0
    while (not math.isclose(number_remainder, 0, abs_tol=1e-4) and
           not math.isclose(number_remainder, 1, abs_tol=1e-4)):
        digit = int(number_remainder * 10)
        float_part = float_part * 10 + digit
        number_remainder = number_remainder * 10 - digit
        shift += 1

    # if the number is close to 1, round up
    if math.isclose(number_remainder, 1, abs_tol=1e-4):
        float_part += 1

    point = spell(".", language=SPELLING_LANGUAGE_CODE)

    if text_number_remainder[0] == "0":  # if leading zero such as 0.033
        float_sign = spell(text_number_remainder[:shift], language=SPELLING_LANGUAGE_CODE, vertical=False)
    else:
        float_sign = construct_integer(float_part)

    return " ".join([integer_sign, point, float_sign])


def construct_ordinals(number: int) -> str:
    if number < 1 or number > 9:
        raise ValueError("Ordinal out of range")
    base_symbol = _get_base_symbol(construct_integer(number))
    return f"M513x527{base_symbol[:4]}11487x497S2c300487x473"


def construct_faction(numerator: int, denominator: int) -> str:
    numerator_fsw = construct_integer(numerator)
    denominator_fsw = construct_integer(denominator)
    fraction_fsw = sign_to_fsw(sign_from_symbols([{"symbol": "S22a04", "position": (0, 0)}]))
    return join_signs_vertical(numerator_fsw, fraction_fsw, denominator_fsw, spacing=8)


def _generate_integer(number: int) -> Tuple[str, str]:
    fsw = construct_integer(number)
    yield str(number), fsw
    yield locale.format_string("%d", number, grouping=True)
    # TODO verbalize the number


def generate_integers():
    for i in range(100):
        yield from _generate_integer(i)
    for i in range(10):
        yield from _generate_integer((i + 1) * 100)
        yield from _generate_integer((i + 1) * 1_000)
        yield from _generate_integer((i + 1) * 10_000)
        yield from _generate_integer((i + 1) * 100_000)
        yield from _generate_integer((i + 1) * 1_000_000)
        yield from _generate_integer((i + 1) * 1_000_000_000)

    random.seed(42)
    for _ in range(10_000):  # Generate random numbers
        exponent = random.uniform(3, 12)  # between 10^3 and 10^12
        number = int(math.pow(10, exponent))
        yield from _generate_integer(number)


def _generate_float(number: float) -> Tuple[str, str]:
    fsw = construct_float(number)
    yield str(number), fsw
    yield locale.format_string("%f", number, grouping=True)
    # TODO verbalize the number


def generate_floats():
    random.seed(42)
    for _ in range(1_000):  # Generate random numbers
        exponent = random.uniform(3, 12)  # between 10^4 and 10^12
        fp_exponent = random.randint(1, 6)
        shift = math.pow(10, fp_exponent)
        number = float(int(math.pow(10, exponent))) / float(shift)
        yield from _generate_float(number)


def small_numbers(quantity=100, seed=None):
    random.seed(seed)
    for _ in range(quantity // 2):
        yield int(math.pow(10, random.uniform(0, 3)))
    for _ in range(quantity // 2):
        number = int(math.pow(10, random.uniform(1, 4)))
        shift = math.pow(10, random.randint(1, 3))
        yield float(number / shift)


def generate_fractions():
    for i in range(1, 11):
        for j in range(i, 21):
            yield f"{i}/{j}", construct_faction(i, j)
            yield f"{i}/{j * 100}", construct_faction(i, j * 10)


if __name__ == "__main__":
    # print(construct_integer(5))
    # print(construct_integer(25))
    # print(construct_integer(133))
    # print(construct_integer(2024))
    # print(construct_faction(3, 8))
    # print(construct_ordinals(8))
    # print(construct_float(56864494.9))
    print(construct_float(0.033))
    print(construct_float(16.32))
    print(construct_float(16.33))
    print(construct_float(16.34))
    # floats = generate_floats()
    # for i in range(10):
    #     print(next(floats))
