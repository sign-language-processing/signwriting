import itertools

from signwriting.primitives.ase.numbers import construct_integer, _get_base_symbol, small_numbers, construct_float

UNITS = {
    "length/distance": {
        ("an inch", "inches", "in"): "M517x530S11911489x505S10018483x500S20e00485x490S26600497x470",
        ("a foot", "feet", "ft"): "",
        ("a yard", "yards",
         "yd"): "M537x519S15a56493x507S19a52517x485S20500504x495S20500475x495S37816462x510S2d600480x481",
        ("a mile", "miles", "mi"): "M529x538S37606471x463S23800479x482S20e00495x509S18d10509x513",
        ("a nautical mile", "nautical miles", "nm"): "",
        ("a nanometer", "nanometers", "nm"): "",
        ("a millimeter", "millimeters", "mm"): "",
        ("a centimeter", "centimeters", "cm"): "",
        ("a meter", "meters", "m"): "",
        ("a kilometer", "kilometers", "km"): "",
    },
    "areas": {
        ("a square inch", "square inches", "in²"): "",
        ("a square foot", "square feet", "ft²"): "",
        ("a square yard", "square yards", "yd²"): "",
        ("a square mile", "square miles", "mi²"): "",
        ("an acre", "acres", "ac"): "",
        ("a hectare", "hectares", "ha"): "",
    },
    "volume": {
        ("a teaspoon", "teaspoons", "tsp"): "",
        ("a fluid ounce", "fluid ounces", "fl oz"): "",
        ("a cup", "cups", "cup"): "M513x543S16d40492x457S22f04488x483S20500489x506S20500502x505S15d39487x520",
        ("a pint", "pints", "pt"): "",
        ("a quart", "quarts", "qt"): "",
        ("a gallon", "gallons", "gal"): "",
    },
    "weight": {
        ("a gram", "grams", "g"): "",
        ("a milligram", "milligrams", "mg"): "",
        ("a kilogram", "kilograms", "kg"): "",
        ("an ounce", "ounces", "oz"): "",
        ("a pound", "pounds", "lb"): "",
        ("a stone", "stones", "st"): "",
        ("a ton", "tons", "t"): "",
    },
    "temperature": {
        ("a degree Fahrenheit", "degrees Fahrenheit",
         "°F"): "M519x550S17620492x449S2e300487x467S10018498x518S10012489x514S20e00482x519S22a04481x535",
        ("a degree Celsius", "degrees Celsius", "°C"): "",
        ("a Kelvin", "Kelvins", "K"): "",
        ("a Centigrade", "Centigrades", "C"): "",
    },
    "energy": {
        ("a calorie", "calories", "cal"): "",
        ("a joule", "joules", "J"): "",
        ("a kilowatt-hour", "kilowatt-hours", "kWh"): "",
        ("an Ampere", "Amperes", "A"): "",
        ("a Volt", "Volts", "V"): "",
        ("an Ohm", "Ohms", "Ω"): "",
        ("a Watt", "Watts", "W"): "",
    },
}


def construct_height(feet: int, inches: int):
    if inches < 0 or inches >= 12:
        raise ValueError("Inches out of range")
    if feet < 0:
        raise ValueError("Feet out of range")

    feet_fsw = _get_base_symbol(construct_integer(feet))
    inches_fsw = _get_base_symbol(construct_integer(inches))

    return f"M526x529{feet_fsw[:4]}01475x499S22a07497x498{inches_fsw[:4]}01505x471"


def generate_heights():
    for i in range(1, 10):
        for j in range(12):
            height_fsw = construct_height(i, j)
            yield f"{i}'{j}\"", height_fsw
            yield f"{i}' {j}\"", height_fsw
            yield f"{i} feet {j} inches", height_fsw
            yield f"{i} feet {j}", height_fsw
            yield f"{i} ft. {j} in.", height_fsw


def generate_units():
    for units in UNITS.values():
        for (singular_name, plural_name, short_name), fsw in units.items():
            # Yield singular
            yield singular_name, fsw
            yield singular_name, construct_integer(1) + " " + fsw

            numbers = set(small_numbers(20))
            for number in numbers:
                yield f"{number} {plural_name}", construct_float(number) + " " + fsw
                yield f"{number} {short_name}", construct_float(number) + " " + fsw


def main():
    print(construct_height(5, 8))
    print(construct_height(6, 10))

    for text, fsw in itertools.islice(generate_units(), 100):
        print(text, fsw)


if __name__ == "__main__":
    main()
