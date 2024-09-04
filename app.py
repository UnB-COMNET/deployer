""" Deployer API server for Lumi """

from __future__ import print_function

import json
import os
import traceback

from flask import Flask, make_response, request
from flask_cors import CORS
from future.standard_library import install_aliases

from classes.onos import Onos
from classes.topology import Topology

install_aliases()

# Flask app should start in global layout
app = Flask(__name__)
CORS(app)

topo = Topology()

onos = Onos(base_url="http://127.0.0.1:8181/onos/v1", ip="172.17.0.2", is_main=True)
topo.add_controller(onos)
topo.make_network_graph()

@app.route("/", methods=["GET"])
def home():
    """ Blank page to check if APIs are running """
    return "Lumi Deployer APIs"


@app.route("/deploy", methods=["POST"])
def deploy():
    """ Endpoint to compile given Nile intent into Merlin, and deploy it to Mininet """
    req = request.get_json(silent=True, force=True)

    print("Request: {}".format(json.dumps(req, indent=4)))  
    res = topo.notify(req)  # Notify observers
    
    r = make_response(res, res["status"])

    r.headers["Content-Type"] = "application/json"
    print(r.data)

    # Keep track of installed flow rules
    if r.status == 200:
        topo.add_intent(r.data["nile"], r.data["output"]["responses"])

    return r



if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))

    print("Starting app on port %d" % port)

    app.run(debug=True, port=port, host="0.0.0.0")
