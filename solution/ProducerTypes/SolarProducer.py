from solution.Production_interface import Producer_interface
from typing import Dict
from numpy import array

class SolarProducer(Producer_interface):
    puissance_crete_W : int
    orientation : int

    def __init__(self, id: int, puissance_crete_W: int, orientation: int = 0):
        super().__init__()
        self.id = id
        self.puissance_crete_W = puissance_crete_W
        self.orientation = orientation

    def _get_production(self, prediction: Dict[int, float]) -> Dict[int, float]:
        production = {key: value * self.puissance_crete_W for key, value in prediction.items()}
        return production