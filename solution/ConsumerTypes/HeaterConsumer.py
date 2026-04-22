import numpy as np
from solution.Calculation_Params import CalculationParams
from solution.Consumer_interface import Consumer_interface
from typing import *
from dataclasses import dataclass
#TODO_ELFE think about how to use it as a cooler
#power -> Tinit -> Text
#TODO_ELFE add some strong testing that text and Twish has values for all sim_size
@dataclass(repr=True, init=False)
class HeaterConsumer(Consumer_interface):
    """
        temperatures are in K
    """
    id            : int
    T_init        : float
    initial_state : bool
    T_ext         : np.ndarray #note T_ext[0] has to be the current temperature
    T_wish_low    : np.ndarray
    T_wish_high   : np.ndarray
    R_th          : float
    C_th          : float
    P_rad         : float
    def __init__(self, id, T_init: float, initial_state: bool, T_ext: np.ndarray, T_wish_low: np.ndarray, T_wish_high: np.ndarray, R_th: float, C_th: float, P_rad: float, consumer_machine_type = -1) -> None:
        self.T_init        = T_init 
        self.initial_state = initial_state 
        self.T_ext         = T_ext   
        self.T_wish_low    = T_wish_low
        self.T_wish_high   = T_wish_high
        self.R_th          = R_th    
        self.C_th          = C_th    
        self.P_rad         = P_rad
        self.has_base_consumption = False
        self.id = id
        self.consumer_machine_type = consumer_machine_type
        self.is_reocurring = True

    def simulate_next_step(self, calculationParams : CalculationParams, current_temp, T_ext, next_T_ext, P_th) -> float:
        #TODO_ELFE use this in stead once calculation is validated
        rc = self.R_th * self.C_th
        delta_T_i = current_temp - T_ext
        delta_t = calculationParams.time_delta
        return next_T_ext + P_th * delta_t / self.C_th + (1.0 - delta_t / rc) * delta_T_i


    def _get_f_contrib(self, calculationParams : CalculationParams) -> List[float]:
        return [0.0 for i in range(self._get_minimizing_variables_count(calculationParams))]
    def _get_integrality(self, calculationParams : CalculationParams) -> List[int]:
        return [1 for i in range(calculationParams.get_simulation_size())] + [0] + [0 for i in range(calculationParams.get_simulation_size())]
    
    def _get_functionnal_constraints_boundaries(self, calculationParams : CalculationParams) -> List[List[float]]:
        #start with Power constraints
        #form : - Prad(i) + a2 Tin(i) + a1 Tin(i + 1)  == a2 Text(i) + a1 Text(i + 1)
        R = self.R_th
        C = self.C_th
        P = self.P_rad
        DT = calculationParams.time_delta
        sim_size = calculationParams.get_simulation_size()
        to_return_low  : List[float] = []
        to_return_high : List[float] = []
        #power constraint:
        #only one heater
        for i in range(sim_size):
            to_return_low.append(0)
            to_return_high.append(1)
        #physics is ok
        for i in range(1, sim_size + 1):
            power_ok = self.T_ext[i + 1] + (DT / (R * C)  - 1) * self.T_ext[i]
            to_return_low.append(power_ok)
            to_return_high.append(power_ok)
        #temperature target
        initial_delta_T = self.T_init - self.T_ext[0]
        temperature_lower_bound = self.get_temperature_lower_bound(calculationParams)[0]
        temperature_upper_bound = self.get_temperature_upper_bound(calculationParams)[0]
        for i in range(len(temperature_lower_bound)):
            to_return_low.append(min(temperature_lower_bound[i], temperature_upper_bound[i]))
            to_return_high.append(max(temperature_lower_bound[i], temperature_upper_bound[i]))
        return [to_return_low, to_return_high]

    def get_temperature_lower_bound(self, calculationParams : CalculationParams) -> Tuple[List[float], List[bool]]:
        sim_size = calculationParams.get_simulation_size()
        simulated_temp = []
        decisions      = []
        simulated_temp.append(self.simulate_next_step(calculationParams, self.T_init, self.T_ext[0], self.T_ext[1], self.P_rad if self.initial_state else 0.0))#take into account the current state
        for i in range(1, sim_size + 1):
            next_step_high = self.simulate_next_step(calculationParams, simulated_temp[-1], self.T_ext[i], self.T_ext[i + 1], self.P_rad)
            next_step_low  = self.simulate_next_step(calculationParams, simulated_temp[-1], self.T_ext[i], self.T_ext[i + 1], 0.0)
            if (next_step_low >= self.T_wish_low[i - 1]):
                simulated_temp.append(next_step_low)
                decisions.append(False)
            else:
                simulated_temp.append(next_step_high)
                decisions.append(True)
        return (simulated_temp, decisions)
    
    def get_temperature_upper_bound(self, calculationParams : CalculationParams) -> Tuple[List[float], List[bool]]:
        sim_size = calculationParams.get_simulation_size()
        simulated_temp = []
        decisions      = []
        simulated_temp.append(self.simulate_next_step(calculationParams, self.T_init, self.T_ext[0], self.T_ext[1], self.P_rad if self.initial_state else 0.0))
        for i in range(1, sim_size + 1):
            next_step_high = self.simulate_next_step(calculationParams, simulated_temp[-1], self.T_ext[i], self.T_ext[i + 1], self.P_rad)
            next_step_low  = self.simulate_next_step(calculationParams, simulated_temp[-1], self.T_ext[i], self.T_ext[i + 1], 0.0)
            if (next_step_high >= self.T_wish_high[i - 1]):
                simulated_temp.append(next_step_low)
                decisions.append(False)
            else:
                simulated_temp.append(next_step_high)
                decisions.append(True)
        return (simulated_temp, decisions)

    def _get_minimizing_variables_count(self, calculationParams : CalculationParams) -> int:
        return 2 * calculationParams.get_simulation_size() + 1
    def _get_constraints_size(self, calculationParams : CalculationParams) -> int:
        return 3 * calculationParams.get_simulation_size() + 1
    def _fill_minimizing_constraints(self, calculationParams: CalculationParams, tofill: np.ndarray, xpars: List[int], ypars: List[int]):
        x = xpars[0]
        y = ypars[0]
        for i in range(calculationParams.get_simulation_size()):
            tofill[y + i, x + i] = - self.P_rad
    def _fill_functionnal_constraints(self, calculationParams: CalculationParams, tofill: np.ndarray, xpar: int, ypar: int):
        R = self.R_th
        C = self.C_th
        P = self.P_rad
        #start with Power constraints
        #power is 0 or one
        sim_size = calculationParams.get_simulation_size()
        x = xpar
        y = ypar
        for i in range(sim_size):
            tofill[y + i, x + i] = 1
        y = y + sim_size
        #physics ok : 

        for i in range(sim_size):
            tofill[y + i, x + i] = - calculationParams.time_delta * P / C
            tofill[y + i, x + i + sim_size] = calculationParams.time_delta / (R * C) - 1
            tofill[y + i, x + i + sim_size + 1] = 1
        y = y + sim_size
        #Temperature constraint
        for i in range(sim_size + 1):
            tofill[y + i, x + i + sim_size] = 1
        
        
    def _get_consumption_curve(self, calculationParams : CalculationParams, variables : List[float]) -> np.ndarray:
        return self.P_rad * np.array(variables[:calculationParams.get_simulation_size()])
    def _get_decisions(self, calculationParams : CalculationParams, variables : List[float]) -> np.ndarray:
        decisions = [np.round(i) for i in variables[:calculationParams.get_simulation_size()]]
        return np.array(decisions, dtype=np.int64)
    def get_temperature(self, calculationParams : CalculationParams, variables : List[float]):
        return np.array(variables[calculationParams.get_simulation_size() + 1:])
   