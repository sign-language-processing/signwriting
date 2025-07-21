from datetime import datetime, UTC

from flask import Flask, jsonify
from flask_restful import Api
from flask_cors import CORS

from signwriting.fingerspelling.server import Fingerspelling
from signwriting.mouthing.server import Mouthing
from signwriting.visualizer.server import Visualizer

app = Flask(__name__)
CORS(app)

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
