from abc import ABC, abstractmethod

# Controller Interface
class Controller(ABC):
    
    @abstractmethod
    def map_topology(self, graph: dict):
        pass
    
