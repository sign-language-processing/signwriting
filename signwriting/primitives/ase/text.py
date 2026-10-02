"""Conservative text adapters for ASL primitives; None means use another fallback."""

import datetime
import re

from signwriting.fingerspelling.fingerspelling import spell
from signwriting.primitives.ase.dates import construct_day_of_month, construct_month, construct_year
from signwriting.primitives.ase.numbers import construct_integer

MONTHS = (
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
)


def construct_number(text: str):
    """Nonnegative integer/decimal quantities, without float rounding or lost zeros.

    Reject signs, exponents, identifiers and ambiguous separators. Leading-zero
    integers stay digit strings for fingerspelling rather than becoming quantities.
    """
    match = re.fullmatch(r"(0|[1-9][0-9]*|[1-9][0-9]{0,2}(?:,[0-9]{3})+)(?:\.([0-9]+))?", text.strip())
    if match is None:
        return None
    whole, fraction = match.groups()
    digits = whole.replace(",", "")
    if len(digits) > 12:  # construct_integer supports values below one trillion.
        return None
    try:
        integer = construct_integer(int(digits))
        if fraction is None:
            return integer
        point = spell(".", language="ase", seed=0)
        decimal = spell(fraction, language="ase", vertical=False, seed=0)
        return " ".join([integer, point, decimal])
    except ValueError:  # Some large layouts exceed the FSW coordinate bounds.
        return None


def construct_date(text: str):
    """Full ISO or English month-name dates only; never infer a numeric date order."""
    text = text.strip()
    iso = re.fullmatch(r"([0-9]{4})\s*-\s*([0-9]{2})\s*-\s*([0-9]{2})", text)
    if iso:
        year, month, day = map(int, iso.groups())
    else:
        named = re.fullmatch(r"([A-Za-z]+)\s+([0-9]{1,2})\s*,?\s+([0-9]{4})", text)
        reversed_named = re.fullmatch(r"([0-9]{1,2})\s+([A-Za-z]+)\s+([0-9]{4})", text)
        if named:
            name, day, year = named.groups()
        elif reversed_named:
            day, name, year = reversed_named.groups()
        else:
            return None
        if name.lower() not in MONTHS:
            return None
        month = MONTHS.index(name.lower()) + 1
        year, day = int(year), int(day)
    try:
        datetime.date(year, month, day)
    except ValueError:
        return None
    return " ".join([construct_month(month), construct_day_of_month(day), construct_year(year)])
