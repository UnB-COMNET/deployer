from abc import ABC, abstractmethod

# CM Interface
class ControllerMethods(ABC):
    
    @abstractmethod
    def map_topology(self, graph: dict):
        pass
    
