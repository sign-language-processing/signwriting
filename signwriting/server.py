from datetime import datetime, UTC

from flask import Flask, jsonify, request
from flask_restful import Api
from flask_cors import CORS

from signwriting.fingerspelling.server import Fingerspelling
from signwriting.mouthing.server import Mouthing
from signwriting.visualizer.server import Visualizer

MAX_INPUT_CHARS = 4096
MAX_REQUEST_BYTES = 1024 * 1024

app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_BYTES


@app.before_request
def bound_inputs():
    for name in ("text", "fsw", "swu"):
        if len(request.args.get(name, "")) > MAX_INPUT_CHARS:
            return jsonify(message=f"Input exceeds {MAX_INPUT_CHARS} characters"), 413

    return None


@app.route('/health', methods=['GET'])
def health_check():
    body = {
        'status': 'healthy',
        'timestamp': datetime.now(tz=UTC).isoformat(),
        'service': 'signwriting',
    }
    return jsonify(body), 200

api = Api(app)

api.add_resource(Visualizer, '/visualizer')
api.add_resource(Fingerspelling, '/fingerspelling')
api.add_resource(Mouthing, '/mouthing')

if __name__ == "__main__":
    app.run()
