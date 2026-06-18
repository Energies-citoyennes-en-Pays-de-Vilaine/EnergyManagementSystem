#this is just a template of the functions required to implement, do not use
from time import time
from solution.Utils.VersionChecker import UpdateChecked
from solution.Consumer_interface import Consumer_interface
from solution.Calculation_Params import CalculationParams
import numpy as np
from typing import *
from solution.ConsumerTypes.types.SumPeriod import SumPeriod
from dataclasses import dataclass, InitVar

@dataclass(init=False, repr=True)
class SumConsumer(Consumer_interface):
    id                   : int
    conso_low            : float
    conso_high           : float
    sum_periods          : List[SumPeriod]
    variables_timestamps : InitVar[List[int]]
    def __init__(self, id,  conso_low: float, conso_high: float, sum_periods : List[SumPeriod], consumer_machine_type = -1):
        self.conso_low   = conso_low
        self.conso_high  = conso_high
        self.sum_periods = sum_periods#sum_period to assert that : expected_sum_min <=Sum(conso_high_t) <= expected_sum_max for each time period
        self.variables_timestamps = []
        self.has_base_consumption = not (conso_low == 0)
        self.id = id
        self.is_reocurring = True
        self.consumer_machine_type = consumer_machine_type
    def _get_f_contrib(self, calculationParams : CalculationParams) -> List[float]:
        return [0 for i in range(self._get_minimizing_variables_count(calculationParams))]
    def _get_integrality(self, calculationParams : CalculationParams) -> List[int]:
        return [1 for i in range(self._get_minimizing_variables_count(calculationParams))]
    def _get_minimizing_constraints(self, calculationParams : CalculationParams) -> List[np.ndarray]:
        raise "not implemented yet"
    def _get_functionnal_constraints(self, calculationParams : CalculationParams) -> np.ndarray:
        raise "not implemented yet"

    def _get_functionnal_constraints_boundaries(self, calculationParams : CalculationParams) -> List[List[float]]:
        self.sum_periods = self._get_feasible_periods(calculationParams)
        bound_min = [sum_period.expected_sum_min for sum_period in self.sum_periods]#TODO_ELFE add check that each sum_period is fesible to include them or not !!!!important
        bound_max = [sum_period.expected_sum_max for sum_period in self.sum_periods]
        return [bound_min[:] + [0 for i in range(self._get_minimizing_variables_count(calculationParams))], bound_max[:] + [1 for i in range(self._get_minimizing_variables_count(calculationParams))]]

    def get_variables_timestamps(self, calculationParams : CalculationParams, forceRebuild : bool = False) -> List[float]:
        if len(self.variables_timestamps) != 0 and not forceRebuild == True  and not self.has_been_updated:
            return self.variables_timestamps #this is lazy loaded to save computation power, add id method to check if calculation params stayed the same
        candidate_timestamps : List[int] = calculationParams.get_time_array()
        timestamps_used      : List[int] = []
        for i in range(len(candidate_timestamps)):
            candidate_timestamp = candidate_timestamps[i]
            for j in range(len(self.sum_periods)):
                if (self.sum_periods[j].beginning <= candidate_timestamp and self.sum_periods[j].end > candidate_timestamp):
                    timestamps_used.append(candidate_timestamps[i])
                    break
        self.variables_timestamps = timestamps_used
        self.has_been_updated = False
        return timestamps_used
        
    def _get_minimizing_variables_count(self, calculationParams : CalculationParams) -> int:
        self.sum_periods = self._get_feasible_periods(calculationParams)
        return len(self.get_variables_timestamps(calculationParams))

    def _get_constraints_size(self, calculationParams : CalculationParams) -> int:
        self.sum_periods = self._get_feasible_periods(calculationParams)
        return len(self.sum_periods) + len(self.get_variables_timestamps(calculationParams))
    def _get_feasible_periods(self, calculationParams: CalculationParams) -> List[SumPeriod]:
        sum_periods = []
        for i, sum_period in enumerate(self.sum_periods):
            if sum_period.end < sum_period.beginning:
                print(f"{sum_period} was baddly generated, end is lower thant beginning, dropping it")
                continue
            start = max(sum_period.beginning, calculationParams.begin)
            end   = min(sum_period.end, calculationParams.end)
            min_sum = sum_period.expected_sum_min
            max_sum = sum_period.expected_sum_max
            if (min_sum < 0 or max_sum < 0):
                print(f"constraint is wrong so dropping it because it expects a negative sum {sum_period}")
                continue
            if ((end - start) / calculationParams.step_size_s < min_sum):
                min_sum = (end - start) / calculationParams.step_size_s
            if (max_sum < min_sum):
                max_sum = min_sum
            sum_periods.append(SumPeriod(start, end, min_sum, max_sum))
        return sum_periods
        
    def _fill_minimizing_constraints(self, calculationParams: CalculationParams, tofill: np.ndarray, xpars: List[int], ypars: List[int]):
        x = xpars[0]
        y = ypars[0]
        delta_conso = self.conso_high - self.conso_low
        for i in range(self.get_minimizing_variables_count(calculationParams)):
            tofill[y + i, x + i] = -delta_conso

    def _fill_functionnal_constraints(self, calculationParams: CalculationParams, tofill: np.ndarray, xpar: int, ypar: int):
        timestamps = self.get_variables_timestamps(calculationParams)
        self.sum_periods = self._get_feasible_periods(calculationParams)
        for j in range(len(self.sum_periods)):
            period_count = 0
            for i in range(len(timestamps)):
                if self.sum_periods[j].beginning <= timestamps[i] and self.sum_periods[j].end > timestamps[i]:
                    tofill[j + ypar, i + xpar] = 1
                    period_count += 1
                tofill[i + ypar + len(self.sum_periods), i + xpar] = 1
    def _get_consumption_curve(self, calculationParams : CalculationParams, variables : List[float]) -> np.ndarray:
        consumption = self._get_base_consumption(calculationParams)
        timestamps = self.get_variables_timestamps(calculationParams)
        base_timestamps = calculationParams.get_time_array()
        for i, timestamp in enumerate(timestamps):
            if variables[i] != 0.0:
                consumption[base_timestamps.index(timestamp)] += variables[i] * (self.conso_high - self.conso_low)
        return consumption
    
    def _get_decisions(self, calculationParams : CalculationParams, variables : List[float]) -> np.ndarray:
        timestamps = self.get_variables_timestamps(calculationParams)
        base_timestamps = calculationParams.get_time_array()
        decisions =  np.zeros((calculationParams.get_simulation_size(),), dtype=np.int64)
        for i,timestamp in enumerate(timestamps):
            if variables[i] != 0.0:
                decisions[base_timestamps.index(timestamp)] += np.round(variables[i])
        return decisions

    def _get_base_consumption(self, calculationParams : CalculationParams) -> np.ndarray:
        base_consumption = np.zeros((calculationParams.get_simulation_size(),))
        base_timestamps = calculationParams.get_time_array()
        if self.conso_low == 0:
            return base_consumption
        for i in range(len(base_timestamps)):
            base_consumption[i] = self.conso_low
        return base_consumption
