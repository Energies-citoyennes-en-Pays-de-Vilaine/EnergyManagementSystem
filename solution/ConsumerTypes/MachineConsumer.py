import numpy as np
from typing import *
from solution.Consumer_interface import Consumer_interface
from solution.Calculation_Params import CalculationParams
from solution.Utils.utils import maxi, mini
from dataclasses import dataclass
from typing import TypedDict
class _CalculatedTimeParametersMachine(TypedDict):
	start_time          : int
	end_time            : int
	steps_count         : int
@dataclass(repr=True, init=False)
class MachineConsumer(Consumer_interface):
    id:int
    profile:int
    start_time:int
    end_time:int
    machine_count:int
    consumer_machine_type:int
    def __init__(self, id, profile, start_time, end_time, machine_count = 1, consumer_machine_type = -1):
        self.id = id
        self.profile = profile
        self.start_time = start_time
        self.end_time = end_time #machine MUST have finished BEFORE end_time
        self.machine_count = machine_count
        self.has_base_consumption = False
        self.is_reocurring = False
        self.consumer_machine_type = consumer_machine_type
    def _get_f_contrib(self, calculationParams : CalculationParams) -> List[float]:
        self._make_machine_possible(calculationParams)
        return [0.0] * self.get_minimizing_variables_count(calculationParams)
    def _get_integrality(self, calculationParams : CalculationParams) -> List[int]:
        self._make_machine_possible(calculationParams)
        return [1] * self.get_minimizing_variables_count(calculationParams)
    def _get_functionnal_constraints_boundaries(self, calculationParams : CalculationParams) -> List[List[List[float]]]:
        self._make_machine_possible(calculationParams)
        return [[self.machine_count], [self.machine_count]]

    def _get_constraints_repr(self, calculationParams : CalculationParams) -> str:
        tp = self._get_calculated_time_parameters(calculationParams)
        return f"Machine {self.id} (start={tp['start_time']}, end={tp['end_time']}, steps={tp['steps_count']}), {self.start_time} : {calculationParams.begin}, {self.end_time} : {calculationParams.end} : {calculationParams.step_size} "
    
    def _get_calculated_time_parameters(self, calculationParams: CalculationParams) -> _CalculatedTimeParametersMachine:
        start_time = maxi(self.start_time, calculationParams.begin)
        end_time = mini(self.end_time, calculationParams.end + calculationParams.step_size)
        step_count = len(self.profile)
        return {
            "start_time"  : start_time,
            "end_time"    : end_time,
            "steps_count" : step_count

        }
    
    def _make_machine_possible(self, calculationParams: CalculationParams):
        tp = self._get_calculated_time_parameters(calculationParams)
        start_time = tp["start_time"]
        end_time   = tp["end_time"]

        if (start_time + len(self.profile) * calculationParams.time_delta  > end_time ):
            print(f"warning, {self._get_constraints_repr(calculationParams)} impossible because user constraints doesn't allow it to fit, rescheduling end constraint")
            self.end_time = start_time + len(self.profile) * calculationParams.time_delta
            self.start_time = start_time
            tp = self._get_calculated_time_parameters(calculationParams)
            start_time = tp["start_time"]
            end_time   = tp["end_time"]
            print(f"new {self._get_constraints_repr(calculationParams)}")

        if (start_time + len(self.profile) * calculationParams.time_delta > calculationParams.end):
            print(f"warning, {self._get_constraints_repr(calculationParams)} impossible because it doesn't fit before the end of simulation. making it earlier so it fits, will be rescheduled later")
            self.start_time = calculationParams.end - len(self.profile) * calculationParams.time_delta
            tp = self._get_calculated_time_parameters(calculationParams)
            start_time = tp["start_time"]
            end_time   = tp["end_time"]
            print(f"new {self._get_constraints_repr(calculationParams)}")

        if (self.end_time <= calculationParams.begin):
            print(f"warning, {self._get_constraints_repr(calculationParams)} impossible because it's supposed to end before the start of simulation. scheduling it for next step")
            self.start_time = calculationParams.begin
            self.end_time = self.start_time + len(self.profile) * calculationParams.time_delta
            tp = self._get_calculated_time_parameters(calculationParams)
            start_time = tp["start_time"]
            end_time   = tp["end_time"]
            print(f"new {self._get_constraints_repr(calculationParams)}")
    
    def _get_minimizing_variables_count(self, calculationParams : CalculationParams) -> int:
        self._make_machine_possible(calculationParams)
        start_time = maxi(self.start_time, calculationParams.begin)
        end_time = mini(self.end_time, calculationParams.end + calculationParams.step_size)
        steps_count = (end_time - start_time) / calculationParams.step_size
        steps_count -= len(self.profile)
        steps_count = round(steps_count)
        if steps_count < 0:
            print(steps_count, start_time, end_time, calculationParams.step_size)
        return steps_count + 1

    def _get_constraints_size(self, calculationParams : CalculationParams) -> int:
        return 1 # only a sum constraint

    def _fill_minimizing_constraints(self, calculationParams: CalculationParams, tofill: np.ndarray, xpars: List[int], ypars: List[int]):
        self._make_machine_possible(calculationParams) 
        sim_size = calculationParams.get_simulation_size()
        start_time = maxi(self.start_time, calculationParams.begin)
        start_step = int(round((start_time - calculationParams.begin) / calculationParams.step_size))
        xpar = xpars[0]
        ypar = ypars[0]
        for i in range(self._get_minimizing_variables_count(calculationParams)):
            for j in range(len(self.profile)):
                tofill[start_step + ypar + i + j, xpar + i] = -self.profile[j]

    def _fill_functionnal_constraints(self, calculationParams: CalculationParams, tofill: np.ndarray, xpar: int, ypar: int):
        self._make_machine_possible(calculationParams)
        for x in range(self._get_minimizing_variables_count(calculationParams)):
            tofill[ypar, xpar + x] = 1

    def _get_consumption_curve(self, calculationParams : CalculationParams, variables : List[float]) -> np.ndarray:
        sim_size = calculationParams.get_simulation_size()
        toReturn = np.zeros((sim_size,), np.float64)
        start_time = maxi(self.start_time, calculationParams.begin)
        start_step = int(round((start_time - calculationParams.begin) / calculationParams.step_size))
        for i in range(len(variables)):
            if (variables[i] != 0):
                for j in range(len(self.profile)):
                    toReturn[start_step + i + j] = variables[i] * self.profile[j]
        return toReturn
    def _get_decisions(self, calculationParams : CalculationParams, variables : List[float]) -> np.ndarray:
        sim_size = calculationParams.get_simulation_size()
        toReturn = np.zeros((sim_size,), np.int64)
        start_time = maxi(self.start_time, calculationParams.begin)
        start_step = int(round((start_time - calculationParams.begin) / calculationParams.step_size))
        for i in range(len(variables)):
            if (variables[i] != 0):
                toReturn[start_step + i] = np.round(variables[i])
        return toReturn