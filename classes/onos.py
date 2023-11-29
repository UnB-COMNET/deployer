import os
import requests

from .deploy_target import DeployTarget
link_lines = ""
device_lines = ""
host_lines = ""

class Onos(DeployTarget):

    def __init__(self, base_url, auth=(os.getenv("ONOSUSER"), os.getenv("ONOSPASS"))):
        super().__init__()
        self.base_url = base_url  # ONOS IP and port
        self.auth = auth
    
    def handle_request(self, request):
        print("handle request method")
    
    # overriding abstract method
    def compile(self):
        print("Compile method")

    # Implements interface method
    def map_topology(self, net_graph):
        print("Starting topology mapping...")
        print("Getting topology information")
        # Three functions to get information about the network and populate the NetworkGraph object.
        #topologyInfo()
        self._devices(net_graph)
        self._hosts(net_graph)
        print("\n\nHost Lines\n")
        print(host_lines)
        print("\n\nSwitch Lines\n")
        print(device_lines)
        print("\n\nLinks\n")
        print(link_lines)


    # Private methods

    # Function to make requests
    def _make_request(self, method: str, path: str, data={}):
        try:
            response = requests.request(method=method, url=self.base_url+path, auth=self.auth)
            return response.json()
        except Exception as e:
            print(f"Error occured wilhe retrieving information from {path}!\nError: {e}")
            print(f"Response status: {response.status_code}")

    # Makes a line entry for nodes
    def _make_node_line(self, type: str, node_object):
        global host_lines, device_lines 
        if type == "host":
            host_lines += node_object["id"] + f"[type=host,ip={node_object['ipAddresses'][0]},mac={node_object['mac']}];\n"
        elif type == "switch":
            device_lines += node_object["id"] + f"[type=switch,ip={node_object['annotations']['managementAddress']}];\n"

    def _make_link_line(self, type: str, node_object):
        global link_lines
        if type == "host":
            for location in node_object["locations"]:
                link_lines += node_object["id"] + " -> " + location["elementId"] + f" [src_port=0,dst_port={location['port']},cost=1];\n"  # host -> switch
                link_lines += location["elementId"] + " -> " + node_object["id"] + f" [src_port={location['port']},dst_port=0,cost=1];\n"  # switch -> host
        elif type == "switch":
            for link in node_object["egress_links"]:
                link_lines += link["src"]["device"] + " -> " + link["dst"]["device"] + f" [src_port={link['src']['port']},dst_port={link['dst']['port']},cost=1];\n"

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


