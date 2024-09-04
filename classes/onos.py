import os
import logging
import re
import urllib.parse
import requests
from typing_extensions import override
import urllib
import ipaddress

from classes.target import DeployTarget

# Temp mappings
GROUP_MAP = {
    "professors": ("192.168.0.0/24", "172.17.0.2"),
    "users": ["192.168.0.3/32", "192.168.0.4/32"],
    "students": "192.168.1.3/32"
}

SERVICE_MAP = {
    "netflix": "192.168.1.4/32"
}

MIDDLEBOX_MAP = {
    "dpi": "192.168.1.4",
    "honeypot": "192.168.1.4",
    "quarantine": "192.168.1.4"
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
        self.is_main = is_main  # Know if controller is the main one of the cluster

    
    @override
    def update(self, request, subject_info):
        intent = request.get('intent')
        op_targets = super().parse_nile(intent)
        targets = []
        # Initial treatment
        if "origin" in op_targets:
            # Add origin IP for controller ip verification
            result = extract_value.search(op_targets["origin"]["value"]) # Extract text between (' and ')
            if result: op_targets["origin"]["value"] = result.group(1)
            targets.append(op_targets["origin"]["value"] + "/32")
            result = extract_value.search(op_targets["destination"]["value"]) # Extract text between (' and ')
            if result: op_targets["destination"]["value"] = result.group(1)

        else: # Intent uses groups
            for target in op_targets["targets"]:
                    # Extract group names
                    result = extract_value.search(target["value"]) # Extract text between (' and ')
                    if result: 
                        target["value"] = result.group(1)
                    print(target["value"])
                    if isinstance(GROUP_MAP[target["value"]], list):
                        targets = GROUP_MAP[target["value"]]
                    else:
                        targets.append(GROUP_MAP[target["value"]])
        
        # Controller verification
        for i, target in enumerate(targets):
            if isinstance(target, tuple):  # Target is a subnetwork
                if self.ip == target[1]:
                    target = target[0]  # remove tuple
                    targets[i] = target
                    return self.compile(intent, op_targets, subject_info, targets)
            else:  # Target is not a subnetwork
                device_id = subject_info["hosts"][target.split("/")[0]]["locations"][0]["elementId"]
                if self.ip == subject_info["devices"][device_id]["controller"]:
                    return self.compile(intent, op_targets, subject_info, targets)
        

        #if self.is_main:
            #self.compile(intent, subject_info)


    # overriding abstract method
    @override
    def compile(self, intent, op_targets: dict, netgraph: dict, srcip_list: list[str]):
        # Auxiliary data structure for general request information
        request = {
        "priority": 40002,
        "appId": "",
        "action": "",
        "srcIp": "", # /32 for specific addresses
        } # 'http://127.0.0.1:8181/onos/v1/acl/rules # http://<ONOS_IP>:<ONOS_PORT>/onos/v1/acl/rules
        
        gen_req = []  # List to save generated requests to the ONOS API
        responses = []  # List to track api responses
        error_flag = False # Flag to break outer loop in case of error

        # Flow rule request body template - Add Operations
        body = {
            "appId": "org.onosproject.core",
            "priority": 40000,
            "timeout": 0,
            "isPermanent": "true",
            "deviceId": "",

            "treatment": {
                "instructions": [
                    {
                        "type": "OUTPUT",
                        "port": ""
                    }
                ]
            },

            "selector": {
                "criteria": [
                    {
                        "type": "ETH_TYPE",
                        "ethType": "0x0800"
                    },
                    {
                        "type": "IPV4_SRC",
                        "ip": ""
                    }
                ]
            }
        }

        try:
            # Targets initial treatment
            if "origin" in op_targets and "destination" in op_targets:
                request["srcIp"] = op_targets["origin"]["value"] + "/32"
                request["dstIp"] = op_targets["destination"]["value"] + "/32"

            for operation in op_targets["operations"]:
                print(operation)

                # Operations
                if operation["type"] == "set":
                    request["appId"] = "org.onosproject.core"
                    print("Set operation")

                # Middleboxes
                elif operation["type"] == "add":
                    print("ADD Operation")
                    print(srcip_list)
                    result = extract_value.search(operation["value"])  # Extract Middlebox name
                    middlebox_ip = MIDDLEBOX_MAP[result.group(1)]  # Get middlebox IP address
                    
                    # Add dst_ip selector criteria if the intent uses endpoints
                    if "origin" in op_targets:
                        # Add the destination address criteria using the destination endpoint
                        body["selector"]["criteria"].append({
                            "type": "IPV4_DST",
                            "ip": request["dstIp"]
                        })
                    
                    # Loop through the srcIP list, creating the flow rule requests and applying them
                    for src_ip in srcip_list:
                        ip, cidr = src_ip.split("/")
                        body["selector"]["criteria"][1]["ip"] = src_ip
                        print(cidr)
                        # Checks if the src_ip is a subnetwork
                        if cidr != "32":
                            print("SUBNETWORK")
                            affected_switches = []

                            for host in netgraph["hosts"].keys():
                                # https://stackoverflow.com/questions/819355/how-can-i-check-if-an-ip-is-in-a-network-in-python
                                if ipaddress.ip_address(host) in ipaddress.ip_network(src_ip):
                                    print(host)
                                    middlebox_paths = self._make_request("GET", f"/paths/{urllib.parse.quote_plus(netgraph['hosts'][host]['id'])}/{urllib.parse.quote_plus(netgraph['hosts'][middlebox_ip]['id'])}")
                                    for link in middlebox_paths["content"]["paths"][0]["links"]:
                                        device_id = link["src"].get("device")
                                        if device_id in affected_switches:
                                            break
                                        if device_id:
                                            affected_switches.append(device_id)
                                            body["deviceId"] = device_id
                                            body["treatment"]["instructions"][0]["port"] = link["src"]["port"]
                                            gen_req.append(body)
                                            print(body)
                                            responses.append(self._make_request("POST", f"/flows/{device_id}", data=body, headers={'Content-type': 'application/json'}))
                        
                        else:  # Not a subnetwork
                            """
                                Calculate shortest path to middlebox first. The shortest path to the original destination will be calculated
                                if the middlebox type is firewall, dpi, ...
                            """
                            print("NOT SUBNETWORK")
                            middlebox_paths = self._make_request("GET", f"/paths/{urllib.parse.quote_plus(netgraph['hosts'][ip]['id'])}/{urllib.parse.quote_plus(netgraph['hosts'][middlebox_ip]['id'])}")
                            
                            for link in middlebox_paths["content"]["paths"][0]["links"]:
                                device_id = link["src"].get("device")
                                if device_id:
                                    body["deviceId"] = device_id
                                    body["treatment"]["instructions"][0]["port"] = link["src"]["port"]
                                    gen_req.append(body)
                                    print(body)
                                    responses.append(self._make_request("POST", f"/flows/{device_id}", data=body, headers={'Content-type': 'application/json'}))

                            # Depending on the middlebox type and if the intent has a destination endpoint, install the necessary flow rules to allow the packets to reach the final target
                            if (result.group(1) == 'dpi' or result.group(1) == 'firewall') and request["dstIp"]:
                                # Get shortest path from middlebox to original destination host
                                host_paths = self._make_request("GET", f"/paths/{urllib.parse.quote_plus(netgraph['hosts'][middlebox_ip]['id'])}/{urllib.parse.quote_plus(netgraph['hosts'][op_targets['destination']['value']]['id'])}")
                                # Change src IP address for flow rule selector
                                body["selector"]["criteria"][1]["ip"] = middlebox_ip + "/32"
                                for link in host_paths["content"]["paths"][0]["links"]:
                                    device_id = link["src"].get("device")
                                    if device_id:
                                        body["deviceId"] = device_id
                                        body["treatment"]["instructions"][0]["port"] = link["src"]["port"]
                                        gen_req.append(body)
                                        print(body)
                                        responses.append(self._make_request("POST", f"/flows/{device_id}", data=body, headers={'Content-type': 'application/json'}))
                        
                else:  # ACL type
                    request["appId"] = "org.onosproject.acl"
                    if operation["type"] == "block": operation["type"] = "deny"  # Change operation name because of ONOS syntax
                    result = extract_value.search(operation["value"]) # Extract text between (' and ')
                    operation["value"] = result.group(1)
                    request["action"] = operation["type"]
                        
                    # Function
                    if operation["function"] == "service":
                        request["dstIp"] = SERVICE_MAP[operation["value"]]

                    elif operation["function"] == "protocol":
                        request["ipProto"] = operation["value"]
                        
                    else:
                        logging.info("Traffic operation")

                    # See targets and make request
                    if op_targets["targets"]:
                        for target in op_targets["targets"]:
                            if type(GROUP_MAP[target["value"]]) == list:
                                for ip in GROUP_MAP[target["value"]]:
                                    request["srcIp"] = ip
                                    print("Generated request body")
                                    print(request)
                                    gen_req.append(request)
                                    responses.append(self._make_request("POST", "/acl/rules", data=request, headers={'Content-Type':'application/json'}))
                            else:
                                request["srcIp"] = GROUP_MAP[target["value"]]
                                print("Generated request body")
                                print(request)
                                gen_req.append(request)
                                # Make request
                                responses.append(self._make_request("POST", "/acl/rules", data=request, headers={'Content-Type':'application/json'}))
                    else:
                        print("Generated request body")
                        print(request)
                        gen_req.append(request)
                        responses.append(self._make_request("POST", "/acl/rules", data=request, headers={'Content-Type':'application/json'}))      
        except Exception as e:
            logging.error("Something went wrong. Revoking applied policies")
            self.revoke_policies(responses)
            return {
                'status': 500,
                'details': e.args
            }
                    
        print("RESPONSES")
        print(responses)
        # Craft response details field
        return {
            'status': 200,
            'type': 'nile',
            'intent': intent,
            'output': {
                'requests': gen_req,
                'responses': responses
            }
        }
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
        logging.info("Adding ONOS instances to controller list")
        controller_list = []
        for node in res["content"]["nodes"]:
            if node["ip"] != self.ip:  # Add only other ONOS instances
                node_obj = Onos("", ip=node["ip"])
                controller_list.append(node_obj)
        return controller_list

    # Private methods

    # Function to make requests
    def _make_request(self, method: str, path: str, data={}, headers={}):
        res = {}
        if data: response = requests.request(method=method, url=self.base_url+path, auth=self.credentials, json=data, headers=headers)
        else: response = requests.request(method=method, url=self.base_url+path, auth=self.credentials, headers={"Accept": "application/json"})
            
        if response.status_code < 299:
            # Add information fields to response object
            if response.headers.get('Location'):
                res["location"] = response.headers.get('Location')
            if response.content:  
                res["content"] = response.json()
            
            return {
                'status': response.status_code,
                **res
            }
            
        else:
            logging.error(f"Error occured for request to {path}!")
            logging.error(f"Response status: {response.status_code}")
            logging.error(f"Response: {response.content}")
            # Craft an error message with request and response information
            raise Exception({
                'message': "A request to the ONOS API returned an error code.",
                'request': {
                    'method': method,
                    'path': path,
                },
                'response': response.json()
            })

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


    # Revoke policies that have already been applied for an intent in case a request fails.
    def revoke_policies(self, policies_list: list):
        for policy in policies_list:
            print("Deleting policy:", policy["location"])
            # URL encode the device ID string
            url = policy["location"].split("/")
            url[6] = urllib.parse.quote(url[6])
            url_s = "/" + "/".join(url[5:])
            self._make_request("DELETE", url_s)


    # Retrieves information about devices in the network
    def _devices(self, graph: dict):
        logging.info("Getting devices information")
        res = self._make_request("GET", "/devices")
        logging.info("Getting links information\n")
        graph["devices"] = {}
        for device in res["content"]["devices"]:
            logging.info(f"Getting information about {device['id']}")
            egress_links = self._make_request("GET", f"/links?device={device['id']}&direction=EGRESS")
            device["egress_links"] = egress_links["content"]["links"]
            device["controller"] = self.ip
            graph["devices"][device["id"]] = device
            self._make_node_line("switch", device)
            self._make_link_line("switch", device)
            
            
    # Retrieves information about hosts in the network
    def _hosts(self, graph: dict):
        logging.info("Getting hosts information\n")
        res = self._make_request("GET", "/hosts")
        graph["hosts"] = {}
        for host in res["content"]["hosts"]:
            graph["hosts"][host["ipAddresses"][0]] = host
            self._make_node_line("host", host)
            self._make_link_line("host", host)
