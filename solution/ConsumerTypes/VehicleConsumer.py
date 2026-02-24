import numpy as np
from typing import *
from solution.Consumer_interface import Consumer_interface
from solution.Calculation_Params import CalculationParams
from solution.Utils.utils import maxi, mini
from math import ceil, floor
from typing import TypedDict
from dataclasses import dataclass

class _CalculatedTimeParameters(TypedDict):
	start_time          : int
	end_time            : int
	min_charge_time     : int
	max_charge_time     : int
	end_time_min_charge : int
	end_time_max_charge : int
	steps_count         : int

@dataclass(init=False, repr=True)
class VehicleConsumer(Consumer_interface):
	id : int # Elfe_Equipement_pilote_id
	power_watt : int
	capacity_watt_hour : int
	initial_charge_pourc : int
	end_charge_pourc : int
	
	def __init__(self, id, power_watt, capacity_watt_hour, initial_charge_pourc, end_charge_pourc, start_time, end_time, consumer_machine_type = -1):
		self.id = id
		self.power_watt = power_watt
		self.capacity_watt_hour = capacity_watt_hour
		self.initial_charge_pourc = initial_charge_pourc
		self.end_charge_pourc = end_charge_pourc
		self.start_time = start_time
		self.end_time = end_time #vehicle must be charged up to end_charge_pourc before the end time
		self.consumer_machine_type = consumer_machine_type
		self.has_base_consumption = False
		self.is_reocurring = False
	
	def _get_f_contrib(self, calculationParams : CalculationParams) -> List[float]:
		self._make_machine_possible(calculationParams)
		return [0.0] * self.get_minimizing_variables_count(calculationParams)
	
	def _get_integrality(self, calculationParams : CalculationParams) -> List[int]:
		self._make_machine_possible(calculationParams)
		return [1] * self.get_minimizing_variables_count(calculationParams)
		
	def _get_functionnal_constraints_boundaries(self, calculationParams : CalculationParams) -> List[List[List[float]]]:
		self._make_machine_possible(calculationParams)
		return [[1], [1]]
	
	def _get_calculated_time_parameters(self, calculationParams: CalculationParams) -> _CalculatedTimeParameters:
		step_size         		= calculationParams.step_size
		start_time        		= maxi(self.start_time, calculationParams.begin)
		end_time          		= mini(self.end_time, calculationParams.end)
		capacity_watt_seconds 	= 3600.0 * self.capacity_watt_hour
		min_charge_proportion 	= max(0,(self.end_charge_pourc - self.initial_charge_pourc) / 100.0)
		max_charge_proportion 	= (100.0 - self.initial_charge_pourc) / 100.0
		min_charge_time   		= step_size * ceil(capacity_watt_seconds * min_charge_proportion / (self.power_watt * step_size))
		max_charge_time   		= step_size * ceil(capacity_watt_seconds * max_charge_proportion / (self.power_watt * step_size))
		end_time_min_charge 	= start_time + min_charge_time
		end_time_max_charge 	= start_time + max_charge_time
		steps_count         	=  floor((end_time - start_time - min_charge_time) / calculationParams.step_size)
		return {
			"start_time" 			: start_time,
			"end_time"				: end_time,
	  		"end_time_min_charge" 	: end_time_min_charge,
			"end_time_max_charge" 	: end_time_max_charge,
			"max_charge_time" 		: max_charge_time,
			"min_charge_time" 		: min_charge_time,
			"steps_count"     		: steps_count
			}
	
	def _get_constraint_repr(self, calculationParams) -> str:
		tp = self._get_calculated_time_parameters(calculationParams)
		return f"ElectricVehicle {self.id}(start = {tp["start_time"]}, end={tp["end_time"]}, charge_time = {tp['min_charge_time']})"
	
	def _make_machine_possible(self, calculationParams: CalculationParams):
		tp = self._get_calculated_time_parameters(calculationParams)
		start_time = tp["start_time"]
		end_time = tp["end_time"]
		if (start_time + tp["min_charge_time"]  > end_time):
			print(f"warning, {self._get_constraint_repr(calculationParams)} is impossible because user constraints doesn't allow it to fit, rescheduling end constraint")
			self.start_time = tp["start_time"]
			self.end_time   = self.start_time + tp["min_charge_time"]
			tp              = self._get_calculated_time_parameters(calculationParams)
			start_time 		= tp["start_time"]
			end_time 		= tp["end_time"]
			print(f"result is {self._get_constraint_repr(calculationParams)}")
		if (start_time + tp["min_charge_time"] > calculationParams.end):
			print(f"warning, {self._get_constraint_repr(calculationParams)} is impossible because it doesn't fit before the end of simulation. making it earlier so it fits, will be rescheduled later")
			self.end_time   = tp["end_time"]
			self.start_time = self.end_time - tp["min_charge_time"]
			tp              = self._get_calculated_time_parameters(calculationParams)
			start_time 		= tp["start_time"]
			end_time 		= tp["end_time"]
			print(f"result is {self._get_constraint_repr(calculationParams)}")
		if (end_time <= calculationParams.begin):
			print(f"warning, {self._get_constraint_repr(calculationParams)} is impossible because it's supposed to end before the start of simulation. scheduling it for next step")
			self.start_time = calculationParams.begin
			self.end_time   = self.start_time + tp["end_time_min_charge"]
			print(f"result is {self._get_constraint_repr(calculationParams)}")

	def _get_minimizing_variables_count(self, calculationParams : CalculationParams) -> int:
		self._make_machine_possible(calculationParams)
		tp = self._get_calculated_time_parameters(calculationParams)
		steps_count = tp["steps_count"]
		if steps_count < 0:
			print(steps_count, tp, calculationParams.step_size)
		return steps_count + 1

	def _get_constraints_size(self, calculationParams : CalculationParams) -> int:
		return 1 # only a sum constraint

	def _calcul_liste_puissance_charge(self, calculationParams : CalculationParams):#intergration de courbe possible
		#Code fournit par Thomas BREMBILLA, Clement EGO et Mathis AUBERT dans le cadre des mini-projets de 1ère année à l'ENS
		pourcent_init = self.initial_charge_pourc
		nb_pourcent = 100 - pourcent_init
		valeur_pas = self.power_watt * calculationParams.step_size / 3600 #3600 secondes dans une heure
		pourcent_par_pas = 100 * valeur_pas / self.capacity_watt_hour
		nb_pas = int(nb_pourcent//pourcent_par_pas)
		P = [-self.power_watt for _ in range(nb_pas)]
		residue = self.power_watt * (nb_pourcent - pourcent_par_pas * nb_pas)/pourcent_par_pas
		if (residue >= 0.1):
			P += [ - self.power_watt * (nb_pourcent - pourcent_par_pas * nb_pas)/pourcent_par_pas]
		return(P)

	def _fill_minimizing_constraints(self, calculationParams: CalculationParams, tofill: np.ndarray, xpars: List[int], ypars: List[int]):
		self._make_machine_possible(calculationParams)
		tp = self._get_calculated_time_parameters(calculationParams)
		sim_size = calculationParams.get_simulation_size()
		start_time = tp["start_time"]
		start_step = int(round((start_time - calculationParams.begin) / calculationParams.step_size))
		end_step = int(round((tp["end_time"] - calculationParams.begin) / calculationParams.step_size))
		power_curve = self._calcul_liste_puissance_charge(calculationParams)
		xpar = xpars[0]
		ypar = ypars[0]
		for i in range(self._get_minimizing_variables_count(calculationParams)):
			for j in range(tp["max_charge_time"] // calculationParams.step_size):
				if (start_step + i + j < sim_size and start_step + i + j < end_step ):
					tofill[start_step + ypar + i + j, xpar + i] = power_curve[j]

	def _fill_functionnal_constraints(self, calculationParams: CalculationParams, tofill: np.ndarray, xpar: int, ypar: int):
		self._make_machine_possible(calculationParams)
		for x in range(self._get_minimizing_variables_count(calculationParams)):
			tofill[ypar, xpar + x] = 1

	def _get_consumption_curve(self, calculationParams : CalculationParams, variables : List[float]) -> np.ndarray:
		tp = self._get_calculated_time_parameters(calculationParams)
		sim_size = calculationParams.get_simulation_size()
		toReturn = np.zeros((sim_size,), np.float64)
		start_time = tp["start_time"]
		start_step = int(round((start_time - calculationParams.begin) / calculationParams.step_size))
		end_step = int(round((tp["end_time"] - calculationParams.begin) / calculationParams.step_size))
		power_curve = self._calcul_liste_puissance_charge(calculationParams)
		for i in range(len(variables)):
			if (variables[i] != 0):
				for j in range(len(power_curve)):
					if (start_step + i + j < sim_size and start_step + i + j < end_step):
						toReturn[start_step + i + j] = - variables[i] * power_curve[j]
		return toReturn
	
	def _get_decisions(self, calculationParams : CalculationParams, variables : List[float]) -> np.ndarray:
		tp = self._get_calculated_time_parameters(calculationParams)
		sim_size = calculationParams.get_simulation_size()
		toReturn = np.zeros((sim_size,), np.int64)
		start_time = tp["start_time"]
		start_step = int(round((start_time - calculationParams.begin) / calculationParams.step_size))
		for i in range(len(variables)):
			if (variables[i] != 0):
				toReturn[start_step + i] = np.round(variables[i])
		return toReturn