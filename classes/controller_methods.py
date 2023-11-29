from abc import ABC, abstractmethod

# CM Interface
class ControllerMethods(ABC):
    
    @abstractmethod
    def mapTopology(self, graph: dict):
        pass
    
