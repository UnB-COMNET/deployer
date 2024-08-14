from typing import List

from classes.controller import Controller

class Topology():

    def __init__(self):
        self.nodes = {}
        self.controllers: List[Controller] = []
        self.operations = []

    def print_nodes(self) -> None:
        for key, value in self.nodes.items():
            print(key, ": ", value, end="\n\n")

    def add_controller(self, cm: Controller):
        self.controllers.append(cm)

    def make_network_graph(self) -> None:
        for controller in self.controllers:
            if controller.controller == "ONOS" and controller.is_main:
                cluster_nodes = controller.cluster_nodes()  # Get cluster nodes objects to add to the controllers list.
                controller.map_topology(self.nodes)
                for node in cluster_nodes:
                    self.add_controller(node)