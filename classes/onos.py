import os
import logging
import requests
from typing_extensions import override

from classes.target import DeployTarget

class Onos(DeployTarget):

    def __init__(self, base_url, credentials=(os.getenv("ONOSUSER"), os.getenv("ONOSPASS"))):
        super().__init__()
        self.base_url = base_url  # ONOS IP and port
        self.credentials = credentials
        self.link_lines = ""
        self.device_lines = ""
        self.host_lines = ""
    
    @override
    def handle_request(self, request):
        print("handle request method")
        """ handles requests """
        status = {
        'code': 200,
        'details': 'Deployment success.'
        }

        intent = request.get('intent')
        policy = None
        try:
            policy= self.compile(intent)
            #merlin_deployer.deploy(policy)
        except ValueError as err:
            print('Error: {}'.format(err))
            print(intent)
            status = {
                'code': 404,
                'details': str(err)
            }

        return {
            'status': status,
            'input': {
            'type': 'nile',
            'intent': intent
            },
            'output': {
                'type': 'Onos',
                'policy': policy
            }
        }
    
    # overriding abstract method
    @override
    def compile(self,intent):
        return "Compile method"

    # Implements interface method
    def map_topology(self, net_graph):
        logging.info("Starting topology mapping...")
        logging.info("Getting topology information")
        # Three functions to get information about the network and populate the NetworkGraph object.
        #topologyInfo()
        self._devices(net_graph)
        self._hosts(net_graph)
        logging.info("\n\nHost Lines\n")
        logging.info(self.host_lines)
        logging.info("\n\nSwitch Lines\n")
        logging.info(self.device_lines)
        logging.info("\n\nLinks\n")
        logging.info(self.link_lines)


    # Private methods

    # Function to make requests
    def _make_request(self, method: str, path: str, data={}):
        try:
            response = requests.request(method=method, url=self.base_url+path, auth=self.credentials)
            return response.json()
        except Exception as e:
            logging.error(f"Error occured wilhe retrieving information from {path}!\nError: {e}")
            logging.error(f"Response status: {response.status_code}")

    # Makes a line entry for nodes
    def _make_node_line(self, type: str, node_object):
        if type == "host":
            self.host_lines += node_object["id"] + f"[type=host,ip={node_object['ipAddresses'][0]},mac={node_object['mac']}];\n"
        elif type == "switch":
            self.device_lines += node_object["id"] + f"[type=switch,ip={node_object['annotations']['managementAddress']}];\n"

    def _make_link_line(self, type: str, node_object):
        if type == "host":
            for location in node_object["locations"]:
                self.link_lines += node_object["id"] + " -> " + location["elementId"] + f" [src_port=0,dst_port={location['port']},cost=1];\n"  # host -> switch
                self.link_lines += location["elementId"] + " -> " + node_object["id"] + f" [src_port={location['port']},dst_port=0,cost=1];\n"  # switch -> host
        elif type == "switch":
            for link in node_object["egress_links"]:
                self.link_lines += link["src"]["device"] + " -> " + link["dst"]["device"] + f" [src_port={link['src']['port']},dst_port={link['dst']['port']},cost=1];\n"

    # Retrieves information about devices in the network
    def _devices(self, graph: dict):
        print("Getting devices information")
        res = self._make_request("GET", "/devices")
        print("Getting links information\n")
        for device in res["devices"]:
            print(f"Getting information about {device['id']}")
            egress_links = self._make_request("GET", f"/links?device={device['id']}&direction=EGRESS")
            device["egress_links"] = egress_links["links"]
            graph[device["id"]] = device
            self._make_node_line("switch", device)
            self._make_link_line("switch", device)
            
            
    # Retrieves information about hosts in the network
    def _hosts(self, graph: dict):
        print("Getting hosts information\n")
        res = self._make_request("GET", "/hosts")
        for host in res["hosts"]:
            graph[host["id"]] = host
            self._make_node_line("host", host)
            self._make_link_line("host", host)


