import unittest

from PIL import Image
from pathlib import Path

from signwriting.visualizer.visualize import signwriting_to_image


class VisualizeCase(unittest.TestCase):
    def test_image_fsw(self):
        fsw = "AS10011S10019S2e704S2e748M525x535S2e748483x510S10011501x466S20544510x500S10019476x475"
        image = signwriting_to_image(fsw)

        assets_path = Path(__file__).parent / "test_assets" / f"{fsw}.png"
        reference_image = Image.open(assets_path)

        self.assertEqual(reference_image, image)

    def test_image_invalid_fsw(self):
        fsw = "S20555"
        image = signwriting_to_image(fsw)

        assets_path = Path(__file__).parent / "test_assets" / f"{fsw}.png"
        reference_image = Image.open(assets_path)

        self.assertEqual(reference_image, image)


if __name__ == '__main__':
    unittest.main()
