import re


def key2swu(key: str) -> str:
    return chr(key2id(key) + 0x40000)


def key2id(key: str) -> int:
    base = int(key[1:4], 16)
    fill = int(key[4], 16)
    rotation = int(key[5], 16)
    return ((base - 0x100) * 96) + (fill * 16) + rotation + 1


def symbol_line(symbol_id: int) -> str:
    return chr(symbol_id + 0xF0000)


def symbol_fill(symbol_id: int) -> str:
    return chr(symbol_id + 0x100000)


def mark2swu(fsw_mark: str) -> str:
    return {'A': '𝠀', 'B': '𝠁', 'L': '𝠂', 'M': '𝠃', 'R': '𝠄'}[fsw_mark]


def num2swu(num: int) -> str:
    return chr(0x1D80C + (num - 250))


def position2swu(position: tuple) -> str:
    return num2swu(position[0]) + num2swu(position[1])


def fsw2swu(text: str) -> str:
    text = text.replace("A", "𝠀").replace("B", "𝠁").replace("L", "𝠂").replace("M", "𝠃").replace("R", "𝠄")

    # Convert positions
    positions = re.findall(r'\d{3}x\d{3}', text)
    for position in positions:
        text = text.replace(position, position2swu(tuple(map(int, position.split("x")))))

    # Convert symbols
    symbols = re.findall(r'S.{5}', text)
    for symbol in symbols:
        text = text.replace(symbol, key2swu(symbol))

    return text
