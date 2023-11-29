from typing import List

from .controller_methods import ControllerMethods

class Topology():

    def __init__(self):
        self.nodes = {}
        self.controllers: List[ControllerMethods] = []
        # self.links = [] Nao ira precisar, os hosts tem os locations e os switches as portas.

    def printNodes(self) -> None:
        for key, value in self.nodes.items():
            print(key, ": ", value, end="\n\n")

    def addController(self, cm: ControllerMethods):
        self.controllers.append(cm)

    def makeNetworkGraph(self) -> None:
        for controller in self.controllers:
            controller.mapTopology(self.nodes)