from typing import List

from classes.controller import Controller

class Topology():

    def __init__(self):
        self.nodes = {}
        self.controllers: List[Controller] = []
        self.installed_intents = []

    def print_nodes(self) -> None:
        for key, value in self.nodes.items():
            print(key, ": ", value, end="\n\n")

    
    # Similar to attach method in observer pattern 
    def add_controller(self, cm: Controller):
        self.controllers.append(cm)


    def notify(self, request) -> None:
        responses = {
            "status": 200,
            "controller_responses": []
        }
        for controller in self.controllers:
            response = controller.update(request, self.nodes)
            if response["status"] > 299:
                responses["status"] = response["status"]
            responses["controller_responses"].append(response)     
        return responses


    def make_network_graph(self) -> None:
        for controller in self.controllers:
            if controller.controller == "ONOS" and controller.is_main:
                cluster_nodes = controller.cluster_nodes()  # Get cluster nodes objects to add to the controllers list.
                controller.map_topology(self.nodes)
                for node in cluster_nodes:
                    self.add_controller(node)


    # Adds a tuple ("Nile intent", [flow_rule1, flow_rule2, ...]) to the installed intents array
    def add_intent(self, nile_intent: str, flow_rules: list) -> None:
        self.installed_intents.append((nile_intent, flow_rules))


    # Revoke last installed intent
    def rollback(self):
        intent_tuple = self.installed_intents[-1]
        self.controllers[0].revoke_policies(intent_tuple[1])