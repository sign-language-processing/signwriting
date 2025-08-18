import unittest
from pathlib import Path

import numpy as np
from PIL import Image
from numpy.testing import assert_array_equal

from signwriting.visualizer.visualize import signwriting_to_image


class VisualizeCase(unittest.TestCase):
    def assert_image_equal_with_reference(self, fsw, image):
        assets_path = Path(__file__).parent / "test_assets" / f"{fsw}.png"
        reference_image = Image.open(assets_path)

        self.assertEqual(reference_image.size, image.size)
        assert_array_equal(np.array(image), np.array(reference_image))

    def test_image_fsw(self):
        fsw = "AS10011S10019S2e704S2e748M525x535S2e748483x510S10011501x466S20544510x500S10019476x475"
        image = signwriting_to_image(fsw)
        self.assert_image_equal_with_reference(fsw, image)

    def test_image_swu(self):
        swu = "𝠃𝤟𝤩񋛩𝣵𝤐񀀒𝤇𝣤񋚥𝤐𝤆񀀚𝣮𝣭"
        image = signwriting_to_image(swu)
        self.assert_image_equal_with_reference('swu_test', image)

    def test_image_without_antialiasing(self):
        fsw = "M528x526S1ce40506x474S1ce48472x474S22a04507x511S22a14480x510"
        image = signwriting_to_image(fsw, antialiasing=False)
        self.assert_image_equal_with_reference(fsw, image)

    def test_image_invalid_fsw(self):
        fsw = "S20555"
        image = signwriting_to_image(fsw)
        self.assert_image_equal_with_reference(fsw, image)

    def test_image_small_box(self):
        fsw = "M500x500S2ff00407x501S1ce20436x535S2e300413x552S22b04418x565S36520420x523"

        with self.assertRaises(ValueError):
            signwriting_to_image(fsw)

    def test_image_small_box_is_corrected(self):
        fsw = "M500x500S2ff00407x501S1ce20436x535S2e300413x552S22b04418x565S36520420x523"
        image = signwriting_to_image(fsw, trust_box=False)
        self.assert_image_equal_with_reference(fsw, image)

    def test_image_with_line_color(self):
        fsw = "M518x517S10040482x485S26500493x474"
        image = signwriting_to_image(fsw, line_color=(123, 234, 0, 255))
        self.assert_image_equal_with_reference(fsw, image)

    def test_image_with_fill_color(self):
        fsw = "M536x517S30a00482x482S33e00482x482S17e11516x464S17e19460x481S22a07523x481S22a11463x481"
        image = signwriting_to_image(fsw, fill_color=(123, 234, 0, 255))
        self.assert_image_equal_with_reference(fsw, image)

    def test_image_with_embedded_color(self):
        fsw = "M518x517S10043487x482S20500487x507"
        image = signwriting_to_image(fsw, embedded_color=True)
        self.assert_image_equal_with_reference(fsw, image)

    def test_image_with_line_and_fill_color(self):
        fsw = "M530x518S19a30500x482S19a38465x481S22f04509x506S22f14467x504"
        image = signwriting_to_image(fsw,
                                     line_color=(10, 23, 122, 255),
                                     fill_color=(255, 255, 255, 0))
        self.assert_image_equal_with_reference(fsw, image)

    def test_image_with_line_and_embedded_color(self):
        fsw = "M518x518S30a00482x483S33e00482x483"
        image = signwriting_to_image(fsw, embedded_color=True,
                                     line_color=(144, 70, 180, 255))
        self.assert_image_equal_with_reference(fsw, image)

    def test_image_with_fill_and_embedded_color(self):
        fsw = "M518x533S20348482x515S10040493x485S20b00497x468S26600502x468"
        image = signwriting_to_image(fsw, embedded_color=True,
                                     fill_color=(123,234,0,255))
        self.assert_image_equal_with_reference(fsw, image)

    def test_layout_signwriting(self):
        fsw_list = ["AS14c20S27106M518x529S14c20481x471S27106503x489",
            "AS18701S1870aS2e734S20500M518x533S1870a489x515S18701482x490S20500508x496S2e734500x468"] # Hello World

        for direction in ["horizontal", "vertical"]:
            image = signwriting_to_image(fsw_list, direction=direction)
            self.assert_image_equal_with_reference(direction, image)


if __name__ == '__main__':
    unittest.main()
