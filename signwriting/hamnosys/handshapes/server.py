"""Annotation server for the SignWriting-to-HamNoSys handshape mapping.

Serves SignWriting->HamNoSys and HamNoSys->SignWriting views over
mappings.json; every save writes straight back to it.

External dictionary data is NOT distributed with this repository; the server
reads it from local files at runtime to enrich the handshape inventory:

- HAMNOSYS_INDEXES: comma-separated CSV files with a `hamnosys` (characters)
  or `hamnosys_names` (space-separated symbol names) column.
- PARALLEL_RECORDS: a jsonl(.gz) file of records whose turns carry
  `extra.hamnosys`.

Run:  pip install ".[server]" && python -m signwriting.hamnosys.handshapes.server
"""

import csv
import gzip
import io
import json
import os
from collections import Counter
from functools import cache
from pathlib import Path

# local-only tool: flask comes from the [server] extra, not the core dependencies
from flask import Flask, jsonify, request, send_file, send_from_directory  # pylint: disable=import-error

from signwriting.hamnosys.handshapes import map as hs_map
from signwriting.hamnosys.handshapes.map import (HAND_BASES, HERE, MAPPINGS_FILE, handshapes,
                                                 key_to_symid, parse_key, symbol_chars)
from signwriting.visualizer.visualize import visualize_sign

app = Flask(__name__)
HAMNOSYS_DIR = HERE.parent
PARALLEL_RECORDS = Path(os.environ.get("PARALLEL_RECORDS", "")).expanduser()

# The 3d-hands-benchmark photo set: indexed by fill (rotations share one
# canonical pose), except these heel-of-hand bases which only exist at fill 1
# and vary by rotation instead.
PHOTOS_BASE_URL = "https://rylo.com/sign/research/lessons-in-signwriting/hands"
WRIST_VIEW_BASES = {"14d", "14f", "151", "15c", "15e", "1f6", "204"}


def read_json(path: Path, default=None):
    if default is not None and not path.is_file():
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)
    hs_map.mappings.cache_clear()
    build_inventory.cache_clear()


def hand_photo_url(key: str) -> str | None:
    base, fill, rotation = parse_key(key)
    cc, gg, bbb, vv, _ff, _rr = key_to_symid(key).split("-")
    prefix = f"{cc}-{gg}-{bbb}"
    photo = rotation + 1 if base in WRIST_VIEW_BASES else fill + 1
    if photo > 6:
        return None
    return f"{PHOTOS_BASE_URL}/{cc}-{gg}/{prefix}/{prefix}-{vv}-{photo:02d}.png"


def parallel_records():
    if not PARALLEL_RECORDS.is_file():
        return
    opener = gzip.open if PARALLEL_RECORDS.suffix == ".gz" else open
    with opener(PARALLEL_RECORDS, "rt", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            turn = record["turns"][0]
            yield turn["extra"].get("gloss"), turn["extra"].get("hamnosys"), turn.get("signwriting")


@cache
def records_handshape_counts() -> Counter:
    counts = Counter()
    for _gloss, hamnosys, _swu in parallel_records():
        for shape in handshapes(hamnosys or ""):
            counts[shape] += 1
    return counts


def index_handshapes(path: Path) -> Counter:
    """Handshape counts from a local dictionary index CSV (not distributed here)."""
    counts = Counter()
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            text = row.get("hamnosys") or ""
            if not text and row.get("hamnosys_names"):
                try:
                    text = "".join(symbol_chars()[n] for n in row["hamnosys_names"].split())
                except KeyError:
                    continue
            for shape in handshapes(text):
                counts[shape] += 1
    return counts


@cache
def build_inventory() -> tuple:  # pylint: disable=too-many-branches
    chart_images = {}
    for cell in read_json(HERE / "handshapes.json"):
        if cell["image"]:
            chart_images.setdefault(cell["hamnosys"], cell["image"])

    sources: dict[str, set] = {}
    counts: Counter = Counter()

    def add(shape, source, count=0):
        sources.setdefault(shape, set()).add(source)
        counts.setdefault(shape, 0)
        counts[shape] += count

    for shape in chart_images:
        add(shape, "chart")
    for entry in read_json(HAMNOSYS_DIR / "parallel.json"):
        for hamnosys in entry.get("hamnosys") or []:
            for shape in handshapes(hamnosys):
                add(shape, "parallel", 1)
    for shape, count in records_handshape_counts().items():
        add(shape, "records", count)
    for path in os.environ.get("HAMNOSYS_INDEXES", "").split(","):
        if path.strip():
            path = Path(path.strip()).expanduser()
            if not path.is_file():
                print(f"warning: skipping missing index {path}")
                continue
            for shape, count in index_handshapes(path).items():
                add(shape, path.stem, count)
    for spellings in read_json(MAPPINGS_FILE).values():
        for shape in spellings:
            add(shape, "mappings")

    return tuple({"hamnosys": shape, "count": counts[shape], "sources": sorted(sources[shape]),
                  "image": chart_images.get(shape)}
                 for shape, _ in counts.most_common())


@cache
def render_symbol(key: str) -> bytes:
    base, fill, rotation = parse_key(key)
    if base in WRIST_VIEW_BASES and fill == 0:
        fill = 1  # wrist-view bases only exist at fill 1
    image = visualize_sign(f"M550x550S{base}{fill:x}{rotation:x}500x500", trust_box=False)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@app.get("/")
def index():
    return send_from_directory(HERE, "annotate.html")


@app.get("/fonts/hamnosys.ttf")
def font():
    return send_from_directory(HAMNOSYS_DIR, "HamNoSysUnicode.ttf")


@app.get("/chart/<path:filename>")
def chart_image(filename):
    return send_from_directory(HERE / "images", filename)


@app.get("/symbol/<key>.png")
def symbol_image(key):
    return send_file(io.BytesIO(render_symbol(key)), mimetype="image/png", max_age=86400)


@app.get("/data")
def data():
    symbols = read_json(HAMNOSYS_DIR / "symbols.json")
    names = read_json(HERE / "base_names.json")
    mappings = read_json(MAPPINGS_FILE)
    return jsonify({
        "bases": [{"key": key, "name": names[key], "hamnosys": mappings[key],
                   "symid": key_to_symid(key), "photo": hand_photo_url(key)}
                  for key in HAND_BASES],
        "inventory": build_inventory(),
        "symbols": [{"char": s["char"], "name": s["name"], "title": s["title"]}
                    for s in symbols if "Handshape" in s["categories"]],
    })


@app.post("/mappings")
def save_mapping():
    body = request.get_json()
    key, spellings = body.get("key"), body.get("hamnosys") or []
    if key not in HAND_BASES:
        return jsonify({"message": f"unknown base {key}"}), 400
    if not isinstance(spellings, list) or not all(isinstance(s, str) and s for s in spellings):
        return jsonify({"message": "hamnosys must be a list of non-empty strings"}), 400
    mappings = read_json(MAPPINGS_FILE)
    mappings[key] = spellings
    write_json(MAPPINGS_FILE, mappings)
    return jsonify({"key": key, "hamnosys": spellings})


if __name__ == "__main__":
    app.run(port=3030, debug=True)
