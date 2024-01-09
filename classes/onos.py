import os
import logging
import re
import requests
from typing_extensions import override

from classes.target import DeployTarget

# Temp mappings
GROUP_MAP = {
    "professors": "192.168.0.0/24"
}

SERVICE_MAP = {
    "netflix": "192.168.1.4/32"
}

extract_value = re.compile(r"'(.*?)'")

class Onos(DeployTarget):
    # Class variable for controller identification.
    controller = "ONOS"

    def __init__(self, base_url, ip, credentials=(os.getenv("ONOSUSER"), os.getenv("ONOSPASS")), is_main=False):
        super().__init__()
        self.base_url = base_url  # ONOS IP and port
        self.ip = ip
        self.credentials = credentials
        self.link_lines = ""
        self.device_lines = ""
        self.host_lines = ""
        self.is_main = is_main

    @override
    def handle_request(self, request):
        pass
    
    # overriding abstract method
    @override
    def compile(self, intent):
        op_targets = super().parse_nile(intent)
        # Considering that every intent have the ACL type for now.
        # ...

        # 1. Iterate over operations, for each save the type (Allow or Block), save the function (service -> IP or MAC, protocol -> TCP, UDP and ICMP)
        # and the value (Service name or protcol name).
        request = {
        "priority": 40002,
        "appId": "",
        "action": "",
        "srcIp": "", # /32 for specific addresses
        } # 'http://127.0.0.1:8181/onos/v1/acl/rules # http://<ONOS_IP>:<ONOS_PORT>/onos/v1/acl/rules
        for operation in op_targets["operations"]:
            print(operation)
            if operation["type"] == "set":
                request["appId"] = "org.onosproject.core"
                print("Set operation")

            else:  # ACL type
                request["appId"] = "org.onosproject.acl"
                if operation["type"] == "block": operation["type"] = "deny"  # Change operation name because of ONOS syntax
                result = extract_value.search(operation["value"]) # Extract text between (' and ')
                operation["value"] = result.group(1)
                request["action"] = operation["type"]
                # Check structure of the op_targets dictionary
                # Targets
                if "origin" in op_targets and "destination" in op_targets:
                    result = extract_value.search(op_targets["origin"]["value"]) # Extract text between (' and ')
                    if result: op_targets["origin"]["value"] = result.group(1)
                    result = extract_value.search(op_targets["destination"]["value"]) # Extract text between (' and ')
                    if result: op_targets["destination"]["value"] = result.group(1)
                    request["srcIp"] = op_targets["origin"]["value"] + "/32"
                    request["dstIp"] = op_targets["destination"]["value"] + "/32"
                else:
                    # 2. Grab info about the targets.
                    for target in op_targets["targets"]:
                        # Map the service and group IPs
                        result = extract_value.search(target["value"]) # Extract text between (' and ')
                        target["value"] = result.group(1)
                        request["srcIp"] = GROUP_MAP[target["value"]]

                # Function
                if operation["function"] == "service":
                    request["dstIp"] = SERVICE_MAP[operation["value"]]

                elif operation["function"] == "protocol":
                    request["ipProto"] = operation["value"]

                print("Generated request body")
                print(request)
                # Make request
                self._make_request("POST", "/acl/rules", data=request, headers={'Content-Type':'application/json'})

        # result = re.search(r"'(.*?)'", input_string) Extract text between (' and ')
        # result.group(1)    

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


    # Retrieves information about ONOS cluster nodes
    def cluster_nodes(self) -> list:
        logging.info("Getting information about cluster nodes")
        res = self._make_request("GET", "/cluster")
        print(res)
        logging.info("Adding ONOS instances to controller list")
        controller_list = []
        for node in res["nodes"]:
            if node["ip"] != self.ip:  # Add only other ONOS instances
                node_obj = Onos("", ip=node["ip"])
                controller_list.append(node_obj)
        return controller_list

    # Private methods

    # Function to make requests
    def _make_request(self, method: str, path: str, data={}, headers={}):
        try:
            if data: response = requests.request(method=method, url=self.base_url+path, auth=self.credentials, json=data, headers=headers)
            else: response = requests.request(method=method, url=self.base_url+path, auth=self.credentials)
            if response.content: return response.json()
        except Exception as e:
            logging.error(f"Error occured wilhe retrieving information from {path}!\nError: {e}")
            logging.error(f"Response status: {response.status_code}")
            logging.error(f"Response: {response.content}")

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
        logging.info("Getting devices information")
        res = self._make_request("GET", "/devices")
        logging.info("Getting links information\n")
        for device in res["devices"]:
            logging.info(f"Getting information about {device['id']}")
            egress_links = self._make_request("GET", f"/links?device={device['id']}&direction=EGRESS")
            device["egress_links"] = egress_links["links"]
            graph[device["id"]] = device
            self._make_node_line("switch", device)
            self._make_link_line("switch", device)
            
            
    # Retrieves information about hosts in the network
    def _hosts(self, graph: dict):
        logging.info("Getting hosts information\n")
        res = self._make_request("GET", "/hosts")
        for host in res["hosts"]:
            graph[host["id"]] = host
            self._make_node_line("host", host)
            self._make_link_line("host", host)


