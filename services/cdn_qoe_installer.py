from __future__ import annotations

import urllib.parse
from typing import Any, Dict, List, Tuple


def _flow_body(src_ip_cidr: str, dst_ip_cidr: str, out_port: str | int,
                    device_id: str, priority: int = 40000) -> Dict[str, Any]:
    return {
        "appId": "org.onosproject.core",
        "priority": priority,
        "timeout": 0,
        "isPermanent": "true",
        "deviceId": device_id,
        "treatment": {
            "instructions": [
                {"type": "OUTPUT", "port": str(out_port)}
            ]
        },
        "selector": {
            "criteria": [
                {"type": "ETH_TYPE", "ethType": "0x0800"},
                {"type": "IPV4_SRC", "ip": src_ip_cidr},
                {"type": "IPV4_DST", "ip": dst_ip_cidr},
            ]
        }
    }


def _get_host_location(netgraph: Dict[str, Any], host_ip: str) -> Tuple[str, str]:
    host = netgraph.get("hosts", {}).get(host_ip)
    if not host:
        raise KeyError(f"Host {host_ip} not found in netgraph['hosts']. ONOS may not have discovered it yet!")

    locs = host.get("locations") or []
    if not locs:
        raise KeyError(f"Host {host_ip} has no locations in ONOS.")

    element_id = locs[0]["elementId"] # deviceId of the switch
    port = str(locs[0]["port"]) # host-facing port on that device
    return element_id, port


def _get_host_id(netgraph: Dict[str, Any], host_ip: str) -> str:
    host = netgraph.get("hosts", {}).get(host_ip)
    if not host:
        raise KeyError(f"Host {host_ip} not found in netgraph['hosts'].")

    host_id = host.get("id")
    if not host_id:
        raise KeyError(f"Host object for {host_ip} has no 'id' field.")
    return host_id


def _onos_paths(onos, src_host_id: str, dst_host_id: str) -> List[Dict[str, Any]]:
    # onos shall provide _make_request(method, path, data?, headers?)
    src_q = urllib.parse.quote_plus(src_host_id)
    dst_q = urllib.parse.quote_plus(dst_host_id)
    res = onos._make_request("GET", f"/paths/{src_q}/{dst_q}")

    paths = (res.get("content") or {}).get("paths") or []
    if not paths:
        raise RuntimeError(f"ONOS returned no paths between {src_host_id} and {dst_host_id}.")
    return paths


def install_flows(onos, netgraph: Dict[str, Any],
                            src_ip: str, dst_ip: str,
                            priority: int = 10) -> List[Dict[str, Any]]:
    """
    Installs IPv4 unidirectional flows src_ip -> dst_ip along the shortest ONOS path.
    Returns ONOS API responses (with 'location' field) to allow revocation later.
    """
    responses: List[Dict[str, Any]] = []

    src_ip_cidr = f"{src_ip}/32"
    dst_ip_cidr = f"{dst_ip}/32"

    src_host_id = _get_host_id(netgraph, src_ip)
    dst_host_id = _get_host_id(netgraph, dst_ip)

    # Get shortest path from ONOS
    path0 = _onos_paths(onos, src_host_id, dst_host_id)[0]
    links = path0.get("links") or []

    # Install flows on each device-to-device hop
    for link in links:
        src = link.get("src") or {}
        dev = src.get("device")
        port = src.get("port")
        if not dev or port is None:
            continue

        body = _flow_body(src_ip_cidr, dst_ip_cidr, port, dev, priority=priority)
        responses.append(
            onos._make_request("POST", f"/flows/{urllib.parse.quote_plus(dev)}",
                               data=body, headers={"Content-type": "application/json"})
        )

    # Ensure the last switch forwards to the destination host-facing port
    dst_sw, dst_port = _get_host_location(netgraph, dst_ip)
    body_last = _flow_body(src_ip_cidr, dst_ip_cidr, dst_port, dst_sw, priority=priority)
    responses.append(
        onos._make_request("POST", f"/flows/{urllib.parse.quote_plus(dst_sw)}",
                           data=body_last, headers={"Content-type": "application/json"})
    )

    return responses


def install_bidirectional_flows(onos, netgraph: Dict[str, Any],
                                     client_ip: str, server_ip: str,
                                     priority: int = 40000) -> List[Dict[str, Any]]:
    """
    Installs both directions:
      client -> server
      server -> client
    """
    responses: List[Dict[str, Any]] = []
    responses.extend(install_flows(onos, netgraph, client_ip, server_ip, priority=priority))
    responses.extend(install_flows(onos, netgraph, server_ip, client_ip, priority=priority))
    return responses


def pick_best_server(best_state_code: str, ip_to_estado_servidor: Dict[str, str]) -> str:
    """
    The mapping is: { "192.168.0.1": "BA", ... }
    """
    for ip, uf in ip_to_estado_servidor.items():
        if uf == best_state_code:
            return ip
    raise KeyError(f"No server IP mapped to state {best_state_code}.")
