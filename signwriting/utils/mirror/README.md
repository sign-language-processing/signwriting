# mirror

Horizontal mirror for SignWriting symbols and signs.

```python
from signwriting.utils.mirror import mirror_sign, mirror_symbol

mirror_symbol("S10000")                          # "S10008"
mirror_sign("M507x507S1f720487x492")             # "M513x507S1f728493x492"
```

`mirror_sign` accepts ASCII **Formal SignWriting (FSW)**. For SWU input,
convert first via `signwriting.formats.swu_to_fsw.swu2fsw`.

## Algorithm

The Sutton SignWriting symbol set (ISWA) splits into ranges that mirror
differently. Each ISWA family (Hand, Contact, Movement Arrow, Face/Head,
Limb, Location, ...) has its own rotation and fill rules, encoded in
`mirror.py` as a handful of per-base sets/dicts (`_LIMB_BASES`,
`_FLOOR_HITS_BASES`, `_FACE_FILL_OVERRIDES`, etc.). The high-level shape:

| Section          | Base range  | Default rotation rule                          | Default fill rule                              |
| ---------------- | ----------- | ---------------------------------------------- | ---------------------------------------------- |
| Hand             | `S100-S204` | `rot -> (rot + 8) mod 16`                      | unchanged                                      |
| Contact          | `S205-S216` | `rot -> (n - rot) mod n` (n probed from font)  | unchanged                                      |
| Movement         | `S217-S2f6` | per-family (XOR-1, +8, face-style, custom)     | swap `0<->1` (handedness); fills 2-5 kept; some bases keep all |
| Face / dynamics  | `S2f7+`     | face-style: `0,4` fixed; `1<->7, 2<->6, 3<->5` | swap `1<->2` if the partner glyph exists       |
| Position         | -           | `x -> 1000 - x`, recompute box, `L <-> R`      | -                                              |

A fill swap is only applied when the partner glyph actually exists in
the font; otherwise the original fill is kept so the result is always a
renderable symbol.

Movement arrows encode handedness in fill `0` vs fill `1`, so mirroring
swaps that pair (fills `2-5` are arrow styles and are kept); a few
families that carry no handedness in the fill (e.g. the `Sequential`
bases `S21a`/`S21f`/`S223`/`S224`, and the contact-style `S22a`) keep it.
Within "Movement" and "Face/dynamics" a large number of per-base rules
override the rotation default; e.g. limbs (`S377-S37d`) keep rotation 0
and 8 as self-mirror and follow `+8` elsewhere; "Hits Floor" arrows
(`S2c8-S2d1`) swap fill `0<->1` plus a rotation fold of
`0<->1, 2<->7, 3<->6, 4<->5`. See `mirror.py` for the complete table.

This is an extension of signmaker's
[`ssw.mirror`](https://github.com/sutton-signwriting/signmaker/blob/1c3751049967819fd509c1ac290cd1bd1954be64/index.js#L467-L474)
calibrated against a corpus of user-confirmed pairs (see
`test_mirror.py` for the regression set).

## Symbol examples

Images are rendered live by
[signbank.org's glyphogram](https://www.signbank.org/signpuddle2.0/glyphogram.php).
Each example wraps the symbol in a minimum-sized sign centered on (500, 500).

| Section            | Original                                                                                                | Mirror                                                                                                  |
| ------------------ | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Hand, rot 0        | `S10000` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x515S10000493x485&pad=10&size=3) | `S10008` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x515S10008493x485&pad=10&size=3) |
| Hand, rot 5        | `S15050` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M513x516S15050487x484&pad=10&size=3) | `S15058` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M513x515S15058487x485&pad=10&size=3) |
| Movement 16-rot, fill 0→1 | `S2e700` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x512S2e700493x488&pad=10&size=3) | `S2e718` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x513S2e718493x487&pad=10&size=3) |
| Movement 8-rot, fill kept | `S22a02` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x507S22a02493x493&pad=10&size=3) | `S22a06` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x507S22a06493x493&pad=10&size=3) |
| Hits Chest, fill 0→1 + rot XOR-1 | `S2ae00` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x515S2ae00493x485&pad=10&size=3) | `S2ae11` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x515S2ae11493x485&pad=10&size=3) |
| Diagonal Between   | `S25d01` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x515S25d01493x485&pad=10&size=3) | `S25d17` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x515S25d17493x485&pad=10&size=3) |
| Hits Floor         | `S2c800` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x515S2c800493x485&pad=10&size=3) | `S2c811` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x515S2c811493x485&pad=10&size=3) |
| Single eyebrow     | `S30a10` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M518x518S30a10482x482&pad=10&size=3) | `S30a20` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M518x518S30a20482x482&pad=10&size=3) |
| Head, rot 1        | `S30001` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M518x517S30001482x483&pad=10&size=3) | `S30007` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M518x517S30007482x483&pad=10&size=3) |
| Dynamics (Fast)    | `S2f700` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M518x515S2f700482x485&pad=10&size=3) | `S2f710` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M518x515S2f710482x485&pad=10&size=3) |
| Limb, axis-aligned | `S37800` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x515S37800493x485&pad=10&size=3) | `S37800` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x515S37800493x485&pad=10&size=3) |
| Limb, rot 3        | `S37803` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x515S37803493x485&pad=10&size=3) | `S3780b` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x515S3780b493x485&pad=10&size=3) |
| Punctuation (sym.) | `S38800` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M536x504S38800464x496&pad=10&size=3) | `S38800` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M536x504S38800464x496&pad=10&size=3) |

## Sign examples

| Original                                                                                                                                            | Mirror                                                                                                                                              |
| --------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `M531x518S35d00469x483S34500495x483` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M531x518S35d00469x483S34500495x483&pad=10&size=2) | `M531x518S35d00495x483S34500469x483` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M531x518S35d00495x483S34500469x483&pad=10&size=2) |
| `M507x507S1f720487x492` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x507S1f720487x492&pad=10&size=2) | `M513x507S1f728493x492` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M513x507S1f728493x492&pad=10&size=2) |
| `M521x547S33100482x483S20310506x500S26b02503x520` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M521x547S33100482x483S20310506x500S26b02503x520&pad=10&size=2) | `M518x547S33100482x483S20318479x500S26b16479x520` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M518x547S33100482x483S20318479x500S26b16479x520&pad=10&size=2) |
| `M525x535S2e748483x510S10011501x466S2e704510x500S10019476x475` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M525x535S2e748483x510S10011501x466S2e704510x500S10019476x475&pad=10&size=2) | `M524x535S2e740500x510S10019478x466S2e71c475x500S10011503x475` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M524x535S2e740500x510S10019478x466S2e71c475x500S10011503x475&pad=10&size=2) |
| `M534x521S22a14475x503S19a00506x479S19a08467x479S22a04514x504S2fb04493x515` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M534x521S22a14475x503S19a00506x479S19a08467x479S22a04514x504S2fb04493x515&pad=10&size=2) | `M533x521S22a04511x503S19a08465x479S19a00504x479S22a14472x504S2fb04492x515` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M533x521S22a04511x503S19a08465x479S19a00504x479S22a14472x504S2fb04492x515&pad=10&size=2) |

## Caveats

* Mirroring relies on the `SuttonSignWritingLine` font being available
  (loaded via `signwriting.visualizer.visualize.get_symbol_size`).
* `render(mirror(sign))` is not bit-exact equal to a horizontal flip of
  `render(sign)`. A handful of font glyphs differ from their mirror partner
  by ~1px (e.g. some S22a arrowheads). Tests allow a 20% pixel-diff
  tolerance for the render-equivalence assertion.

## Known font issues

In a few cases the ISWA codepoint we map to is the correct symbolic
mirror, but the glyph drawn by the SignWriting fonts (both
`SuttonSignWritingLine` and `SuttonSignWritingOneD`) doesn't reflect it
faithfully. The mirror function returns the right codepoint; the rendered
image will look "off". Known cases:

* `S22826 → S22822` (and the reverse) — Finger Contact Movement, Wall
  Plane. The codepoint pairing is correct but the font's drawing of the
  partner glyph is not the actual horizontal mirror.
* `S2311b → S23103` (and the reverse), `S23104 → S2311c` (and the reverse)
  — Double Alternating Movement, Wall Plane. Fill `1<->0` swap + rotation
  +8 produces the correct codepoint, but several font glyphs in S231 don't
  reflect a true horizontal mirror.
* `S22922 → S22926` (and the reverse) — Finger Contact Movement, Floor
  Plane. Codepoint mapping is correct (face-style rotation 2 <-> 6) but
  the font glyph isn't the visual mirror.
