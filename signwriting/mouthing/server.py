from flask import make_response, jsonify
from flask_restful import Resource, reqparse

from signwriting.mouthing.mouthing import mouth

parser = reqparse.RequestParser()
parser.add_argument('text', type=str, required=True, location='args', help='Text to mouth')
parser.add_argument('spoken_language', type=str, required=True, location='args',
                    help='Spoken Language code. See "Language Support" at https://pypi.org/project/epitran/')


class Mouthing(Resource):
    def get(self):
        args = parser.parse_args()

        result = mouth(args["text"], language=args["spoken_language"])

        return make_response(jsonify({
            "ipa": result.ipa,
            "fsw": result.fsw,
            "swu": result.swu
        }), 200)
