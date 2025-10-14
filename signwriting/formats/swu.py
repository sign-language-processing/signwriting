import re

import regex

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
re_swu['sign_with_whitespace'] = rf"{re_swu['sign']}\s*"
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


def is_swu(text: str) -> bool:
    # Using the regex pattern instead of the compiled regex for performance (about 30% faster)
    return bool(re.fullmatch(re_swu['sign_with_whitespace'], text))

def is_sgnw(text: str) -> bool:
    return bool(regex.fullmatch("\p{Sutton_SignWriting}+", text))
