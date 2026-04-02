from solution.Exceptions.FunctionNotExistingException import *
from solution.Calculation_Params import CalculationParams
from typing import List

class Producer_interface():
    id: int

    def get_production(self, prediction: List[float]) -> List[float]:
        checkFunctionExist(self._get_production())
        production = self._get_production(prediction)
        return production
    