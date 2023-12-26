"""
    Script test - Getting topology information from ONOS automatically.
"""

# Imports
# -- Local Imports --
from classes.onos import Onos
from classes.topology import Topology

if __name__ == "__main__":
    topo = Topology()
    onos = Onos(base_url="http://127.0.0.1:8181/onos/v1", ip="172.17.0.2", is_main=True)
    topo.add_controller(onos)
    topo.make_network_graph()
    print("Printing network nodes\n")
    topo.print_nodes()

    intent = "define intent stnIntent: for group('professors') allow service('netflix')"
    # This will change after the modifications in the topology and onos class.
    onos.compile(intent)

    # Test with endpoint ACL intent
    intent = "define intent stnIntent: from endpoint('19.16.1.1') to endpoint('172.16.22.95') allow service('vimeo'), service('youtube')"
    onos.compile(intent)

    