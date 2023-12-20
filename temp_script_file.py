"""
    Script test - Getting topology information from ONOS automatically.
"""

# Imports
# -- Local Imports --
from classes.onos import Onos
from classes.topology import Topology

if __name__ == "__main__":
    topo = Topology()
    onos = Onos(base_url="http://127.0.0.1:8181/onos/v1")

    topo.add_controller(onos)
    topo.make_network_graph()
    print("Printing network nodes\n")
    topo.print_nodes()

    