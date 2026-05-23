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
differently. The implementation has one section per range, plus the
sign-level position flip.

| Section          | Base range  | Rotation rule                              | Fill rule                              |
| ---------------- | ----------- | ------------------------------------------ | -------------------------------------- |
| Hand             | `S100-S204` | `rot -> (rot + 8) mod 16`                  | unchanged                              |
| Movement (16 rot)| `S205-S2f6` | `rot -> (rot + 8) mod 16`                  | swap `0<->1`, `3<->4`, `2<->5`         |
| Movement (8 rot) | subset above| reflect direction: `0,4` fixed, diagonals swap | swap `0<->1`, `3<->4`, `2<->5`     |
| Face / dynamics  | `S2f7+`     | reflect direction: `0,4` fixed, diagonals swap | swap `1<->2` (head bases that have an asymmetric partner) |
| Position         | -           | `x -> 1000 - x`, recompute box, `L <-> R`  | -                                      |

A fill swap is only applied when the partner glyph actually exists in the
font; otherwise we keep the original fill so the result is always a
renderable symbol.

This is a section-typed reformulation of signmaker's
[`ssw.mirror`](https://github.com/sutton-signwriting/signmaker/blob/1c3751049967819fd509c1ac290cd1bd1954be64/index.js#L467-L474),
extended with the fill swaps for movement and face sections.

## Symbol examples

Images are rendered live by
[signbank.org's glyphogram](https://www.signbank.org/signpuddle2.0/glyphogram.php).

Each example wraps the symbol in a minimum-sized sign centered on (500, 500)
so the glyphogram renders the full glyph without cropping.

| Section          | Original                                                                                                | Mirror                                                                                                  |
| ---------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Hand, rot 0      | `S10000` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x515S10000493x485&pad=10&size=3) | `S10008` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x515S10008493x485&pad=10&size=3) |
| Hand, rot 5      | `S15050` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M513x516S15050487x484&pad=10&size=3) | `S15058` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M513x515S15058487x485&pad=10&size=3) |
| Movement arrow   | `S2e700` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x512S2e700493x488&pad=10&size=3) | `S2e718` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x513S2e718493x487&pad=10&size=3) |
| Movement (8 rot) | `S22a02` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x507S22a02493x493&pad=10&size=3) | `S22a16` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x507S22a16493x493&pad=10&size=3) |
| Single eyebrow   | `S30a10` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M518x518S30a10482x482&pad=10&size=3) | `S30a20` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M518x518S30a20482x482&pad=10&size=3) |
| Punctuation (symmetric, no change) | `S38800` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M536x504S38800464x496&pad=10&size=3) | `S38800` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M536x504S38800464x496&pad=10&size=3) |
| Head, rot 1      | `S30001` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M518x517S30001482x483&pad=10&size=3) | `S30007` ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M518x517S30007482x483&pad=10&size=3) |

## Sign examples

| Original                                                                                                                                            | Mirror                                                                                                                                              |
| --------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `M531x518S35d00469x483S34500495x483` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M531x518S35d00469x483S34500495x483&pad=10&size=2) | `M531x518S35d00495x483S34500469x483` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M531x518S35d00495x483S34500469x483&pad=10&size=2) |
| `M507x507S1f720487x492` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M507x507S1f720487x492&pad=10&size=2) | `M513x507S1f728493x492` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M513x507S1f728493x492&pad=10&size=2) |
| `M521x547S33100482x483S20310506x500S26b02503x520` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M521x547S33100482x483S20310506x500S26b02503x520&pad=10&size=2) | `M518x547S33100482x483S20318479x500S26b16479x520` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M518x547S33100482x483S20318479x500S26b16479x520&pad=10&size=2) |
| `M525x535S2e748483x510S10011501x466S2e704510x500S10019476x475` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M525x535S2e748483x510S10011501x466S2e704510x500S10019476x475&pad=10&size=2) | `M524x535S2e730500x510S10019478x466S2e71c475x500S10011503x475` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M524x535S2e730500x510S10019478x466S2e71c475x500S10011503x475&pad=10&size=2) |
| `M534x521S22a14475x503S19a00506x479S19a08467x479S22a04514x504S2fb04493x515` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M534x521S22a14475x503S19a00506x479S19a08467x479S22a04514x504S2fb04493x515&pad=10&size=2) | `M533x521S22a04511x503S19a08465x479S19a00504x479S22a14472x504S2fb04492x515` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M533x521S22a04511x503S19a08465x479S19a00504x479S22a14472x504S2fb04492x515&pad=10&size=2) |

## Caveats

* Mirroring relies on the `SuttonSignWritingLine` font being available
  (loaded via `signwriting.visualizer.visualize.get_symbol_size`).
* `render(mirror(sign))` is not bit-exact equal to a horizontal flip of
  `render(sign)`. A handful of font glyphs differ from their mirror partner
  by ~1px (e.g. some S22a arrowheads). Tests allow a 20% pixel-diff
  tolerance for the render-equivalence assertion.
