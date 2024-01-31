import unittest
from pathlib import Path

import numpy as np
from PIL import Image
from numpy.testing import assert_array_equal

from signwriting.visualizer.visualize import signwriting_to_image


class VisualizeCase(unittest.TestCase):
    def test_image_fsw(self):
        fsw = "AS10011S10019S2e704S2e748M525x535S2e748483x510S10011501x466S20544510x500S10019476x475"
        image = signwriting_to_image(fsw)

        assets_path = Path(__file__).parent / "test_assets" / f"{fsw}.png"
        reference_image = Image.open(assets_path)

        self.assertEqual(reference_image.size, image.size)
        assert_array_equal(np.array(image), np.array(reference_image))

    def test_image_without_antialiasing(self):
        fsw = "M528x526S1ce40506x474S1ce48472x474S22a04507x511S22a14480x510"
        image = signwriting_to_image(fsw, antialiasing=False)

        assets_path = Path(__file__).parent / "test_assets" / f"{fsw}.png"
        reference_image = Image.open(assets_path)

        self.assertEqual(reference_image.size, image.size)
        assert_array_equal(np.array(image), np.array(reference_image))

    def test_image_invalid_fsw(self):
        fsw = "S20555"
        image = signwriting_to_image(fsw)

        assets_path = Path(__file__).parent / "test_assets" / f"{fsw}.png"
        reference_image = Image.open(assets_path)

        assert_array_equal(np.array(image), np.array(reference_image))

    def test_image_small_box(self):
        fsw = "M500x500S2ff00407x501S1ce20436x535S2e300413x552S22b04418x565S36520420x523"

        with self.assertRaises(ValueError):
            signwriting_to_image(fsw)

    def test_image_small_box_is_corrected(self):
        fsw = "M500x500S2ff00407x501S1ce20436x535S2e300413x552S22b04418x565S36520420x523"

        image = signwriting_to_image(fsw, trust_box=False)

        assets_path = Path(__file__).parent / "test_assets" / f"{fsw}.png"
        reference_image = Image.open(assets_path)

        assert_array_equal(np.array(image), np.array(reference_image))


if __name__ == '__main__':
    unittest.main()
