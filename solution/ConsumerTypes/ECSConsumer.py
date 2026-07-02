from dataclasses import dataclass
import pyomo.environ as pyo
from utils.time.timestamp import synchronise
import numpy as np
from typing import *
from solution.Consumer_interface import Consumer_interface
from solution.Calculation_Params import CalculationParams

WATER_CTH_J  = 4180#J/K/kg
WATER_CTH_WH = WATER_CTH_J / 3600 #Wh/K/kg
BASE_TEMP	= 283 #10 °C
END_TEMP	 = 333 #60° C

class _CalculatedTimeParameters(TypedDict):
	start_time		: int
	end_time		: int
	last_time_start	: int
	steps_count		: int

class ECSConsumer(Consumer_interface):
	id			  	: int 
	power_W	  		: int
	volume_litre	: int
	
	def __init__(self, id, last_consumption_Wh, start_time, end_time, power_W, volume_litre, calculationParams, consumer_machine_type=-1):
		self.id = id
		self.last_consumption_Wh = last_consumption_Wh
		self.start_time = start_time
		self.end_time = end_time #machine MUST have finished BEFORE end_time
		self.machine_count = 1
		self.has_base_consumption = False
		self.is_reocurring = False
		self.consumer_machine_type = consumer_machine_type
		self.power_W = power_W
		self.volume_litre = volume_litre
		self.tp : _CalculatedTimeParameters = self._get_calculated_time_parameters(calculationParams)
		self.consommation = None
		print(f"ECS_Consummer start:{self.tp['start_time']} last_time:{self.tp['last_time_start']} end:{self.tp['end_time']}")

	def __repr__(self):
		to_return = "ECSConsumer("
		to_return += f"id={self.id},"
		to_return += f"last_consumption_Wh={self.last_consumption_Wh},"
		to_return += f"start_time={self.start_time},"
		to_return += f"end_time={self.end_time},"
		to_return += f"power={self.power_W},"
		to_return += f"volume={self.volume_litre},"
		to_return += f"consumer_machine_type={self.consumer_machine_type},"
		to_return += ")"
		return to_return
	
	def _create_consumer_variable(self, consumerBlock: pyo.Block, calculationParams: CalculationParams) -> None:
		last_time = max(self.tp["start_time"], self.tp["last_time_start"])
		consumerBlock.decision_set = pyo.RangeSet(self.tp["start_time"], last_time, calculationParams.step_size_s)
		consumerBlock.decisions = pyo.Var(consumerBlock.decision_set, domain = pyo.Binary)
			
	def _create_consumer_constraint(self, consumerBlock: pyo.Block, calculationParams: CalculationParams) -> None:
		def unicity_constraint(block: pyo.Block):
			return sum(block.decisions[i] for i in consumerBlock.decision_set) == 1
		consumerBlock.constraint_unicity = pyo.Constraint(rule = unicity_constraint)

	def _calcul_consommation(self, calculationParams: CalculationParams) -> None:
		self.consommation = {calculationParams.step_size_s * i: self.power_W for i in range(self.tp["steps_count"])}
		
	def _get_consumption_t(self, consumerBlock: pyo.Block, calculationParams: CalculationParams, step_timestamp: int) -> pyo.Var:
		if self.consommation == None:
			self._calcul_consommation(calculationParams)
		to_return = 0
		if self.tp["start_time"] <= step_timestamp <= self.tp["end_time"]:
			for lancement_timestamp in consumerBlock.decision_set:
				to_return += (0 if step_timestamp - lancement_timestamp < 0 or step_timestamp - lancement_timestamp >= self.tp["steps_count"] * calculationParams.step_size_s
								else self.consommation[step_timestamp-lancement_timestamp]) * consumerBlock.decisions[lancement_timestamp]
		return to_return
	
	def _get_decisions(self, calculationParams: CalculationParams, launch_timestamp : int) -> np.ndarray:
		toReturn = np.zeros((calculationParams.simulation_size,), np.int64)
		launch_step = synchronise(launch_timestamp)
		end_step = min(launch_step + self.tp["steps_count"] + 8, calculationParams.simulation_size - 1)
		self.total_duration = end_step - launch_step
		toReturn[launch_step: end_step] = 1
		return toReturn
	
	def _get_consumption_curve(self, calculationParams: CalculationParams, decision: int) -> np.ndarray:
		decision = (decision - calculationParams.begin) // calculationParams.step_size_s
		sim_size = calculationParams.simulation_size
		toReturn = np.zeros((sim_size,), np.float64)
		for k, v in self.consommation.items():
			index = k // calculationParams.step_size_s + decision
			if index >= sim_size:
				break
			toReturn[index] = v
		return toReturn
	
	def get_total_duration(self) -> int:
		return self.total_duration
	
	def _get_calculated_time_parameters(self, calculationParams: CalculationParams) -> _CalculatedTimeParameters:
		step_size_s		 		: int = calculationParams.step_size_s
		start_time				: int = max(self.start_time, calculationParams.begin)
		end_time		  		: int = min(self.end_time, calculationParams.end)
		previous_duration_step 	: int = int(np.ceil((self.last_consumption_Wh / self.power_W) * 3600 / step_size_s))
		total_duration			: int = int(np.ceil((3600 * (END_TEMP - BASE_TEMP) * self.volume_litre * WATER_CTH_WH / self.power_W) / step_size_s))
		steps_count		 		: int = max(previous_duration_step, total_duration) 
		heat_time				: int = steps_count * step_size_s
		last_time_start		 	: int = end_time - heat_time
		return {
			"start_time" 			: start_time,
			"end_time"				: end_time,
			"last_time_start"		: last_time_start,
			"steps_count"	 		: steps_count
			}