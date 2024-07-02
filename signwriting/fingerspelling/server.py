from flask import make_response, jsonify
from flask_restful import Resource, reqparse

from signwriting.fingerspelling.fingerspelling import spell, get_chars_by

parser = reqparse.RequestParser()
parser.add_argument('text', type=str, required=True, help='Text to fingerspell')
parser.add_argument('signed_language', type=str, required=True, help='Signed language ISO-3 code')


class Fingerspelling(Resource):
    def get(self):
        args = parser.parse_args()

        try:
            chars = get_chars_by(value=args["signed_language"], category="SIGNED")
        except ValueError as e:
            return make_response(jsonify({"message": str(e)}), 400)

        fsw = spell(args["text"], chars=chars)
        return make_response(jsonify({"fsw": fsw}), 200)
