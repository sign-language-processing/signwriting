from io import BytesIO

from flask import send_file
from flask_restful import Resource, reqparse

from signwriting.formats.swu_to_fsw import swu2fsw
from signwriting.visualizer.visualize import RGBA, signwriting_to_image


def hex_color_to_rgba(hex_color: str) -> RGBA:
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    a = int(hex_color[6:8], 16) if len(hex_color) > 6 else 255
    return r, g, b, a


def send_pil_image(pil_img):
    img_io = BytesIO()
    pil_img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


parser = reqparse.RequestParser()
parser.add_argument('fsw', type=str, required=False, help='FSW String (Must be provided if swu is not provided)')
parser.add_argument('swu', type=str, required=False, help='SWU String (Must be provided if fsw is not provided)')
parser.add_argument('line', type=str, default='000000ff', help='Line color in hex format')
parser.add_argument('fill', type=str, default='ffffffff', help='Fill color in hex format')


class Visualizer(Resource):
    def get(self):
        args = parser.parse_args()
        fsw = args.get("fsw")
        swu = args.get("swu")
        if fsw is None and swu is None:
            return {"message": "No fsw or swu provided"}, 400

        line_color = hex_color_to_rgba(args["line"])
        fill_color = hex_color_to_rgba(args["fill"])

        sw_string = fsw if fsw is not None else swu2fsw(swu)
        image = signwriting_to_image(fsw=sw_string, line_color=line_color, fill_color=fill_color)
        return send_pil_image(image)
