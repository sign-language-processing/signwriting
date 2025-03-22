import re
from typing import List

# Define regex patterns
re_swu = {
    'symbol': r'[\U00040001-\U0004FFFF]',
    'coord': r'[\U0001D80C-\U0001DFFF]{2}',
    'sort': r'\U0001D800',
    'box': r'[\U0001D801-\U0001D804]'
}
re_swu['prefix'] = rf"(?:{re_swu['sort']}(?:{re_swu['symbol']})+)"
re_swu['spatial'] = rf"{re_swu['symbol']}{re_swu['coord']}"
re_swu['signbox'] = rf"{re_swu['box']}{re_swu['coord']}(?:{re_swu['spatial']})*"
re_swu['sign'] = rf"{re_swu['prefix']}?{re_swu['signbox']}"
re_swu['sortable'] = rf"{re_swu['prefix']}{re_swu['signbox']}"


def swu_add_prefix(swu_text: str) -> str:
    signs = re.findall(re_swu['sign'], swu_text)
    output_signs = []
    for sign in signs:
        if not sign.startswith('𝠀'):
            symbols = re.findall(re_swu['symbol'], sign)
            sign = '𝠀' + "".join(symbols) + sign
        output_signs.append(sign)
    return " ".join(output_signs)


def swu2fsw(swu_text: str) -> str:
    if not swu_text:
        return ''

    # Initial replacements
    fsw = swu_text.replace("𝠀", "A").replace("𝠁", "B").replace("𝠂", "L").replace("𝠃", "M").replace("𝠄", "R")

    # SWU symbols to FSW keys
    syms = re.findall(re_swu['symbol'], fsw)
    if syms:
        for sym in syms:
            fsw = fsw.replace(sym, swu2key(sym))

    # SWU coordinates to FSW coordinates
    coords = re.findall(re_swu['coord'], fsw)
    if coords:
        for coord in coords:
            fsw = fsw.replace(coord, 'x'.join(map(str, swu2coord(coord))))

    return fsw


def swu2key(swu_sym: str) -> str:
    symcode = ord(swu_sym) - 0x40001
    base = symcode // 96
    fill = (symcode - (base * 96)) // 16
    rotation = symcode - (base * 96) - (fill * 16)
    return f'S{hex(base + 0x100)[2:]}{hex(fill)[2:]}{hex(rotation)[2:]}'


def swu2num(swu_num: str) -> int:
    return ord(swu_num) - 0x1D80C + 250


def swu2coord(swu_coord: str) -> List[int]:
    return [swu2num(swu_coord[0]), swu2num(swu_coord[1])]
