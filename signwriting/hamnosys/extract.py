"""One-off extraction of HamNoSys data from official sources.

Regenerates symbols.json, handshapes/images/, handshapes/handshapes.json
and the chart tables in handshapes/README.md. Requires: pip install pymupdf fonttools

All geometry below is hardcoded to the 2010-06-10 revision of the
HamNoSys 4 handshapes chart (single page, 842x595pt).
"""
# pylint: disable=import-error,too-many-locals
# pymupdf and fonttools are only needed to regenerate the committed data, so they are not project dependencies.

import io
import json
import re
import urllib.request
from pathlib import Path

import fitz
from fontTools.ttLib import TTFont

HANDSHAPES_PDF = "https://www.sign-lang.uni-hamburg.de/dgs-korpus/files/inhalt_pdf/HamNoSys_Handshapes.pdf"
FONT_TTF = "https://mirrors.ibiblio.org/CTAN/fonts/hamnosys/HamNoSysUnicode.ttf"
INPUT_PAGE = "https://www.sign-lang.uni-hamburg.de/hamnosys/input/"

HERE = Path(__file__).parent


def fetch(url: str) -> bytes:
    cache = HERE / ".cache" / url.rstrip("/").split("/")[-1]
    cache.parent.mkdir(exist_ok=True)
    if not cache.is_file():
        with urllib.request.urlopen(url) as response:
            cache.write_bytes(response.read())
    return cache.read_bytes()


def extract_symbols() -> list[dict]:
    html = fetch(INPUT_PAGE).decode("utf-8")
    tabs = re.findall(r'<li><a href="#">([^<]+)</a></li>', html)
    panes = re.split(r'<div id="keyboard_[a-z0-9]+">', html)[1:]
    by_codepoint = {}
    for tab, pane in zip(tabs, panes):
        for name, value in re.findall(r'title="(ham[a-z0-9]+)" class="ham" value="([^"]*)"', pane):
            value = value.replace("&nbsp;", "").strip()
            if not value:  # hamspace's value is whitespace
                value = " "
            symbol = by_codepoint.setdefault(ord(value), {"name": name, "categories": []})
            if tab not in symbol["categories"]:
                symbol["categories"].append(tab)

    # The font knows a few glyphs the keyboard does not offer (e.g. hamversion40)
    font = TTFont(io.BytesIO(fetch(FONT_TTF)))
    for codepoint, glyph_name in font.getBestCmap().items():
        if codepoint >= 0xE000 and codepoint not in by_codepoint:
            by_codepoint[codepoint] = {"name": glyph_name, "categories": []}

    return [{"name": symbol["name"], "unicode": f"U+{codepoint:04X}", "char": chr(codepoint),
             "categories": symbol["categories"]}
            for codepoint, symbol in sorted(by_codepoint.items())]


# Chart geometry: (min_x, max_x) -> column label, per section
SECTION_1 = "Handshape Classes"
SECTION_2 = "Thumb Opposition"
COLUMNS = {
    SECTION_1: [
        (40, 60, "Selection"),
        (60, 160, "Selected Fingers Extended"),
        (160, 280, "Selected Fingers Flattened"),
        (280, 425, "Selected Fingers Bent"),
        (425, 540, "Selected Fingers Hooked"),
        (540, 700, "Derivation Examples"),
    ],
    SECTION_2: [
        (45, 165, "Fingertip-Thumbtip Opposition w/ fingers rounded"),
        (165, 285, "Fingertip-Thumbtip Opposition w/ fingers flattened"),
        (285, 330, "Fingertip-Thumbtip Opposition w/ fingers straight"),
        (330, 355, "Fingertip-Thumbtip Opposition w/ hitchhiker's fingers"),
        (355, 385, "Fingertip-Thumb's Interphalangeal Joint Opposition"),
        (385, 420, "Fingertip-Thumb's Metacarpophalangeal Joint Opposition"),
        (420, 700, "Derivation Examples"),
    ],
}
# (min_y, max_y) -> row label, keyed on image y0 for cells, on text y0 for "cf." references
IMAGE_ROWS = [
    (60, 100, SECTION_1, "Fist"),
    (100, 137, SECTION_1, "One Finger"),
    (137, 173, SECTION_1, "Two Fingers (nonspread)"),
    (173, 210, SECTION_1, "Two Fingers (spread)"),
    (210, 246, SECTION_1, "Flathand (Four Fingers nonspread)"),
    (246, 285, SECTION_1, "Four Fingers (spread)"),
    (310, 350, SECTION_2, "One Finger, others in fist position"),
    (350, 400, SECTION_2, "Two Fingers (nonspread), others in fist position"),
    (400, 460, SECTION_2, "Four Fingers (nonspread)"),
    (460, 500, SECTION_2, "One Finger, others extended (spread)"),
]
CF_ROWS = [
    (110, 125, SECTION_1, "One Finger"),
    (145, 160, SECTION_1, "Two Fingers (nonspread)"),
    (220, 235, SECTION_1, "Flathand (Four Fingers nonspread)"),
    (330, 355, SECTION_2, "One Finger, others in fist position"),
    (365, 395, SECTION_2, "Two Fingers (nonspread), others in fist position"),
    (395, 415, SECTION_2, "Two Fingers (spread), others in fist position"),
    (425, 455, SECTION_2, "Four Fingers (nonspread)"),
    (455, 475, SECTION_2, "Four Fingers (spread)"),
    (480, 500, SECTION_2, "One Finger, others extended (spread)"),
]
ROW_ORDER = [
    (SECTION_1, "Fist"),
    (SECTION_1, "One Finger"),
    (SECTION_1, "Two Fingers (nonspread)"),
    (SECTION_1, "Two Fingers (spread)"),
    (SECTION_1, "Flathand (Four Fingers nonspread)"),
    (SECTION_1, "Four Fingers (spread)"),
    (SECTION_2, "One Finger, others in fist position"),
    (SECTION_2, "Two Fingers (nonspread), others in fist position"),
    (SECTION_2, "Two Fingers (spread), others in fist position"),
    (SECTION_2, "Four Fingers (nonspread)"),
    (SECTION_2, "Four Fingers (spread)"),
    (SECTION_2, "One Finger, others extended (spread)"),
]


def classify(bands, value):
    for band in bands:
        if band[0] <= value < band[1]:
            return band[2:]
    raise ValueError(f"unclassified position {value}")


def extract_handshapes(names: dict[str, str]) -> list[dict]:
    doc = fitz.open(stream=fetch(HANDSHAPES_PDF), filetype="pdf")
    page = doc[0]
    images = page.get_image_info(xrefs=True)
    spans = [span
             for block in page.get_text("dict")["blocks"] if block["type"] == 0
             for line in block["lines"] for span in line["spans"]
             if span["font"] == "HamnosysUnicode"]

    cells = []
    for span in spans:
        x0, y0, x1, _ = span["bbox"]
        center_x = (x0 + x1) / 2
        image = next((i for i in images
                      if i["bbox"][3] - 2 <= y0 <= i["bbox"][3] + 12
                      and abs((i["bbox"][0] + i["bbox"][2]) / 2 - center_x) < 15), None)
        if image is None:  # a "cf." cross-reference, no image of its own
            section, row = classify(CF_ROWS, y0)
        else:
            images.remove(image)
            section, row = classify(IMAGE_ROWS, image["bbox"][1])
        anchor_x = image["bbox"][0] if image else x0
        (column,) = classify(COLUMNS[section], anchor_x)
        codepoints = [f"{ord(c):04x}" for c in span["text"]]
        cell = {
            "section": section,
            "row": row,
            "column": column,
            "hamnosys": span["text"],
            "symbols": [names[c] for c in codepoints],
            "image": f"images/{'-'.join(codepoints)}.png" if image else None,
            "order": (ROW_ORDER.index((section, row)), anchor_x),
        }
        if image:
            (HERE / "handshapes" / cell["image"]).write_bytes(doc.extract_image(image["xref"])["image"])
        cells.append(cell)

    assert not images, f"{len(images)} images had no notation paired to them"
    cells.sort(key=lambda c: c.pop("order"))
    return cells


def chart_html(cells: list[dict], section: str) -> str:
    columns = [c[2] for c in COLUMNS[section]]
    rows = [r for s, r in ROW_ORDER if s == section]
    grid = {(c["row"], c["column"]): [] for c in cells}
    for cell in cells:
        if cell["section"] == section:
            grid.setdefault((cell["row"], cell["column"]), []).append(cell)

    lines = ["<table>", "<tr><th></th>" + "".join(f"<th>{c}</th>" for c in columns) + "</tr>"]
    for row in rows:
        tds = [f"<th>{row}</th>"]
        for column in columns:
            parts = []
            for cell in grid.get((row, column), []):
                title = " ".join(cell["symbols"])
                if cell["image"]:
                    parts.append(f'<img src="{cell["image"]}" width="42" title="{title}" alt="{title}">')
                else:
                    parts.append(f'<sub>cf. {title}</sub>')
            tds.append(f'<td>{" ".join(parts)}</td>')
        lines.append("<tr>" + "".join(tds) + "</tr>")
    lines.append("</table>")
    return "\n".join(lines)


def main():
    symbols = extract_symbols()
    with open(HERE / "symbols.json", "w", encoding="utf-8") as f:
        json.dump(symbols, f, indent=2, ensure_ascii=False)

    (HERE / "handshapes" / "images").mkdir(parents=True, exist_ok=True)
    names = {symbol["unicode"][2:].lower(): symbol["name"] for symbol in symbols}
    cells = extract_handshapes(names)
    with open(HERE / "handshapes" / "handshapes.json", "w", encoding="utf-8") as f:
        json.dump(cells, f, indent=2, ensure_ascii=False)

    readme = (HERE / "handshapes" / "README.md").read_text(encoding="utf-8")
    for section in (SECTION_1, SECTION_2):
        marker = f"<!-- chart:{section} -->"
        pattern = re.escape(marker) + r".*?" + re.escape(marker)
        replacement = f"{marker}\n{chart_html(cells, section)}\n{marker}"
        readme = re.sub(pattern, replacement, readme, flags=re.DOTALL)
    (HERE / "handshapes" / "README.md").write_text(readme, encoding="utf-8")
    print(f"{len(symbols)} symbols, {len(cells)} chart cells")


if __name__ == "__main__":
    main()
