import datetime
import locale

from signwriting.fingerspelling.fingerspelling import spell
from signwriting.primitives.ase.numbers import construct_integer, construct_ordinals
from signwriting.utils.join_signs import join_signs_horizontal

SPELLING_LANGUAGE_CODE = 'en-us-ase-asl'

locale.setlocale(locale.LC_ALL, "en_US")


def construct_month(month: int):
    if month < 1 or month > 12:
        raise ValueError("Month out of range")

    fs_map = {
        1: 'jan', 2: 'feb', 3: 'march', 4: 'april', 5: 'may', 6: 'june',
        7: 'july', 8: 'aug', 9: 'sept', 10: 'oct', 11: 'nov', 12: 'dec'
    }

    return spell(fs_map[month], language=SPELLING_LANGUAGE_CODE, vertical=False)


def construct_day_of_month(day: int):
    if day < 10:
        return construct_ordinals(day)
    return construct_integer(day)


def construct_year(year: int):
    # TODO: bc/ad
    if year > 10000:
        raise ValueError("Year too large")
    if year < 1000:
        return construct_integer(year)
    first_pair = construct_integer(year // 100)
    second_pair = construct_integer(year % 100)
    return join_signs_horizontal(first_pair, second_pair, spacing=8)


def generate_birthday():
    signs = ["M514x514S15a01491x487S20500487x503",
             "M532x566S20500496x555S20500495x519S22a04494x536S30004482x482S1c507507x517"]
    for month in range(1, 13):
        month_name = datetime.date(1900, month, 1).strftime("%B")
        month_sign = construct_month(month)
        for day in range(1, 32):
            day_sign = construct_day_of_month(day)
            day_suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
            yield f"My birthday is {month_name} {day}{day_suffix}.", " ".join(
                signs + [month_sign, day_sign, "S38800464x496"])


if __name__ == "__main__":
    print(construct_year(2024))
    for english, birthday in generate_birthday():
        print(english, birthday)
