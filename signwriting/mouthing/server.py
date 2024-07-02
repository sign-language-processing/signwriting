from flask import make_response, jsonify
from flask_restful import Resource, reqparse

from signwriting.mouthing.mouthing import mouth

parser = reqparse.RequestParser()
parser.add_argument('text', type=str, required=True, help='Text to mouth')
parser.add_argument('spoken_language', type=str, required=True,
                    help='Spoken Language code. See "Language Support" at https://pypi.org/project/epitran/')


class Mouthing(Resource):
    def get(self):
        args = parser.parse_args()

        fsw = mouth(args["text"], language=args["spoken_language"])
        return make_response(jsonify({"fsw": fsw}), 200)
