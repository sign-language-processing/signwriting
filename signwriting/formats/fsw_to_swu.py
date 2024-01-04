def key2swu(key: str) -> str:
    return chr(key2id(key) + 0x40000)


def key2id(key: str) -> int:
    base = int(key[1:4], 16)
    fill = int(key[4], 16)
    rotation = int(key[5], 16)
    return ((base - 0x100) * 96) + (fill * 16) + rotation + 1


def symbol_line(id: int) -> str:
    return chr(id + 0xF0000)


def symbol_fill(id: int) -> str:
    return chr(id + 0x100000)
