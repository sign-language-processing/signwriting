from flask import Flask
from flask_restful import Api

from signwriting.fingerspelling.server import Fingerspelling
from signwriting.mouthing.server import Mouthing
from signwriting.visualizer.server import Visualizer

app = Flask(__name__)
api = Api(app)

api.add_resource(Visualizer, '/visualizer')
api.add_resource(Fingerspelling, '/fingerspelling')
api.add_resource(Mouthing, '/mouthing')

if __name__ == "__main__":
    app.run()
