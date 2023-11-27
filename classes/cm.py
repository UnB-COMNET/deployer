from abc import ABC, abstractmethod

# CM Interface
class CM(ABC):
    
    @abstractmethod
    def mapTopology(self, graph: dict):
        pass
    
