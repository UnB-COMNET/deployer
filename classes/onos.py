import os
import requests

from .deploytarget import DeployTarget
linkLines = ""
deviceLines = ""
hostLines = ""

class Onos(DeployTarget):

    def __init__(self, base_url, auth=(os.getenv("ONOSUSER"), os.getenv("ONOSPASS"))):
        super().__init__()
        self.BASE_URL = base_url  # ONOS IP and port
        self.AUTH = auth
    
    def handleRequest(self, request):
        print("handle request method")
    
    # overriding abstract method
    def compile(self):
        print("Compile method")

    # Implements interface method
    def mapTopology(self, net_graph):
        print("Starting topology mapping...")
        print("Getting topology information")
        # Three functions to get information about the network and populate the NetworkGraph object.
        #topologyInfo()
        self.__devices(net_graph)
        self.__hosts(net_graph)
        print("\n\nHost Lines\n")
        print(hostLines)
        print("\n\nSwitch Lines\n")
        print(deviceLines)
        print("\n\nLinks\n")
        print(linkLines)


    # Private methods

    # Function to make requests
    def __makeRequest(self, method: str, path: str, data={}):
        try:
            response = requests.request(method=method, url=self.BASE_URL+path, auth=self.AUTH)
            return response.json()
        except Exception as e:
            print(f"Error occured wilhe retrieving information from {path}!\nError: {e}")
            print(f"Response status: {response.status_code}")

    # Makes a line entry for nodes
    def __makeNodeLine(self, type: str, nodeObject):
        global hostLines, deviceLines 
        if type == "host":
            hostLines += nodeObject["id"] + f"[type=host,ip={nodeObject['ipAddresses'][0]},mac={nodeObject['mac']}];\n"
        elif type == "switch":
            deviceLines += nodeObject["id"] + f"[type=switch,ip={nodeObject['annotations']['managementAddress']}];\n"

    def __makeLinkLine(self, type: str, nodeObject):
        global linkLines
        if type == "host":
            for location in nodeObject["locations"]:
                linkLines += nodeObject["id"] + " -> " + location["elementId"] + f" [src_port=0,dst_port={location['port']},cost=1];\n"  # host -> switch
                linkLines += location["elementId"] + " -> " + nodeObject["id"] + f" [src_port={location['port']},dst_port=0,cost=1];\n"  # switch -> host
        elif type == "switch":
            for link in nodeObject["egress_links"]:
                linkLines += link["src"]["device"] + " -> " + link["dst"]["device"] + f" [src_port={link['src']['port']},dst_port={link['dst']['port']},cost=1];\n"

    # Retrieves information about devices in the network
    def __devices(self, graph: dict):
        print("Getting devices information")
        res = self.__makeRequest("GET", "/devices")
        print("Getting links information\n")
        for device in res["devices"]:
            print(f"Getting information about {device['id']}")
            egress_links = self.__makeRequest("GET", f"/links?device={device['id']}&direction=EGRESS")
            device["egress_links"] = egress_links["links"]
            graph[device["id"]] = device
            self.__makeNodeLine("switch", device)
            self.__makeLinkLine("switch", device)
            
            
    # Retrieves information about hosts in the network
    def __hosts(self, graph: dict):
        print("Getting hosts information\n")
        res = self.__makeRequest("GET", "/hosts")
        for host in res["hosts"]:
            graph[host["id"]] = host
            self.__makeNodeLine("host", host)
            self.__makeLinkLine("host", host)


