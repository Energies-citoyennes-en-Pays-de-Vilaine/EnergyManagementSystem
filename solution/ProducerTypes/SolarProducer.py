from solution.Production_interface import Producer_interface
from typing import List
from numpy import array

class SolarProducer(Producer_interface):
    puissance_crete_W : int
    orientation : int

    def __init__(self, id: int, puissance_crete_W: int, orientation: int = 0):
        super().__init__()
        self.id = id
        self.puissance_crete_W = puissance_crete_W
        self.orientation = orientation

    def _get_production(self, prediction: List[float]) -> List[float]:
        return list(array(prediction) * self.puissance_crete_W)