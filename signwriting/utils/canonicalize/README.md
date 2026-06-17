# canonicalize

Rewrite a single SignWriting sign so its symbols are listed in a canonical
order and its box fits tightly.

```python
from signwriting.utils.canonicalize import canonicalize

canonicalize("M521x547S20310506x500S33100482x443")
# "M521x515S33100482x443S20310506x500"
```

`canonicalize` accepts ASCII **Formal SignWriting (FSW)**. For SWU input,
convert first via `signwriting.formats.swu_to_fsw.swu2fsw`.

## Algorithm

1. **Order by category.** Each symbol belongs to one ISWA category, sorted in
   the order below. Within a category, symbols are written top-to-bottom, then
   left-to-right.

   | Rank | Category  | Base range  |
   | ---- | --------- | ----------- |
   | 0    | faces     | `S2ff-S36c` |
   | 1    | other     | `S36d+`     |
   | 2    | hands     | `S100-S204` |
   | 3    | contact   | `S205-S220` |
   | 4    | movement  | `S221-S2fe` |

   This order was derived empirically: across the `single_signs` corpus, for
   every pair of categories the dominant writing order is faces → other →
   hands → contact → movement (e.g. faces precede hands 69% of the time,
   hands precede movement 78%).

2. **Keep an overlap only when its draw order is visible.** When two glyphs
   share an inked pixel, one is drawn on top of the other - but that only
   affects the image if the two paint a shared pixel with *different* colors
   (e.g. a hand's opaque white fill covering a face's line). So each
   overlapping pair is rendered both ways: if the images match, the order is
   free and the pair sorts into canonical order; if they differ, the pair keeps
   its input order. (Glyphs whose ink is disjoint trivially commute and are
   never rendered.) These order-sensitive pairs become hard precedence
   constraints, and the canonical order is produced by a topological sort that
   honours them while otherwise following the category order above.

3. **Tighten the box.** The box's bottom-right corner is recomputed from the
   symbols' rendered sizes (the same calculation `signwriting_to_image`
   performs with `trust_box=False`, exposed as
   `signwriting.visualizer.visualize.signwriting_box`). The box marker
   (`M`/`L`/`R`/`B`) is preserved.

`canonicalize` is idempotent, and `render(canonicalize(sign))` is
pixel-identical to `render(sign)` (with the same box), because two symbols are
only ever reordered when swapping their draw order leaves the image unchanged.

## Caveats

* Overlap detection relies on the `SuttonSignWriting` fonts being available
  (loaded via `signwriting.visualizer.visualize`).
* Overlap and the both-ways render comparison use crisp 1-bit glyph masks.
  Antialiased rendering can blend glyph fringes that the 1-bit masks treat as
  disjoint, so the render-equivalence guarantee holds for non-antialiased
  rendering.

## Examples

Real signs from the `single_signs` corpus, one per kind of fix. Images are
rendered live by
[signbank.org's glyphogram](https://www.signbank.org/signpuddle2.0/glyphogram.php),
which trusts the box in the FSW (so a wrong box shows up as clipping or
padding).

| Fix | Source | Target |
| --- | --- | --- |
| **Box too small.** The downward arrow (`S21b00` at y=582) falls below the stated box (`550`), so it renders clipped. The symbols are already in canonical order; only the box is tightened to `591`. | `M521x550S36d00479x450S1001c494x520S21b00500x582` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M521x550S36d00479x450S1001c494x520S21b00500x582&pad=10&size=2) | `M521x591S36d00479x450S1001c494x520S21b00500x582` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M521x591S36d00479x450S1001c494x520S21b00500x582&pad=10&size=2) |
| **Order fixed, no overlap.** The face (`S32400`) is written after the hand (`S18500`), but faces come first. They don't overlap, so the face moves to the front; the image is unchanged. | `M563x553S18500536x495S32400482x483S29900549x521` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M563x553S18500536x495S32400482x483S29900549x521&pad=10&size=2) | `M563x553S32400482x483S18500536x495S29900549x521` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M563x553S32400482x483S18500536x495S29900549x521&pad=10&size=2) |
| **Order fixed despite overlap.** The face (`S33100`) overlaps the hand (`S11511`), but the hand has no fill there, so rendering both orders is identical - the face can safely move to the front. | `M544x527S11511503x500S33100482x482S20600522x495` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M544x527S11511503x500S33100482x482S20600522x495&pad=10&size=2) | `M544x527S33100482x482S11511503x500S20600522x495` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M544x527S33100482x482S11511503x500S20600522x495&pad=10&size=2) |
| **Order fixed despite overlap.** The eyebrow (`S30a00`) overlaps the hand (`S10000`), but again neither covers the other, so the rendered image is unaffected and the face is written first. | `M518x529S10000469x499S30a00482x482` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M518x529S10000469x499S30a00482x482&pad=10&size=2) | `M518x529S30a00482x482S10000469x499` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M518x529S30a00482x482S10000469x499&pad=10&size=2) |
| **Order can't be fixed.** Two hands (`S10010`, `S15d59`) overlap, and the right one's opaque white fill covers the left one's lines - rendering the two orders gives different images, so the input order is kept. We'd normally write the top-left hand (`S15d59`) first, but here it has to come second. | `M515x516S10010500x486S15d59485x484` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M515x516S10010500x486S15d59485x484&pad=10&size=2) | `M515x516S10010500x486S15d59485x484` <br> ![](https://www.signbank.org/signpuddle2.0/glyphogram.php?text=M515x516S10010500x486S15d59485x484&pad=10&size=2) |
