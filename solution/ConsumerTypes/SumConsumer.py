from utils.time.timestamp import synchronise
from solution.Utils.VersionChecker import UpdateChecked
from solution.Consumer_interface import Consumer_interface
from solution.Calculation_Params import CalculationParams
import numpy as np
from typing import *
from solution.Calendrier import Calendrier_confort
from dataclasses import dataclass, InitVar
import pyomo.environ as pyo
from datetime import datetime


@dataclass(init=False, repr=True)
class SumConsumer(Consumer_interface):
	id							: int
	conso_low					: float
	conso_high					: float
	pourcentage_eco_consigne	: float
	lancement_45m_precedent		: List[int]
	calendrier					: Calendrier_confort

	def __init__(self, id, conso_low: float, conso_high: float, pourcentage_eco: int, calendrier: Calendrier_confort, lancement_45m_precedent: List[int], consumer_machine_type = -1):
		self.id = id
		self.conso_low = conso_low
		self.conso_high = conso_high
		self.pourcentage_eco_consigne = pourcentage_eco / 100
		self.calendrier = calendrier
		self.lancement_45m_precedent = lancement_45m_precedent
		self.consumer_machine_type = consumer_machine_type
		self.has_base_consumption = False
		self.is_reocurring = False

	def __repr__(self):
		return f"id:{self.id}, %:{self.pourcentage_eco_consigne}, low:{self.conso_low}, high:{self.conso_high},\n calendrier:{self.calendrier},\n historique:{self.lancement_45m_precedent}"

	def calcul_pourcentage(self, calculationParams: CalculationParams) -> None:
		return
	# 	zone_passe, zone_futur = self.calendrier.get_past_confort_hours(calculationParams.begin), self.calendrier.get_futur_confort_hours(calculationParams.begin)
	# 	self.nb_lancement_48h_suivant = min(zone_futur, self.pourcentage_eco_consigne * (zone_passe + zone_futur) - self.lancement_45m_precedent)
		# print(f"%:{self.pourcentage_eco_consigne}, _-:{zone_passe}, n-:{self.nb_lancement_24h_precedent}, _+:{zone_futur}, n+:{self.nb_lancement_48h_suivant}")

	def _create_consumer_variable(self, consumerBlock: pyo.Block, calculationParams: CalculationParams) -> None:
		filter_calendrier = lambda m, x: self.calendrier.is_confort_timestamp(x)
		consumerBlock.decision_set = pyo.RangeSet(calculationParams.begin, calculationParams.end, calculationParams.step_size_s, filter=filter_calendrier)
		consumerBlock.decisions = pyo.Var(consumerBlock.decision_set, domain = pyo.Binary)

	def _create_consumer_constraint(self, consumerBlock: pyo.Block, calculationParams: CalculationParams) -> None:
		periodes_chauffage = self.calendrier.get_confort_periods(calculationParams.begin)
		# print(f"begin:{calculationParams.begin}\ntimestamps:{[d for d in consumerBlock.decisions]}\nperiodes:{periodes_chauffage}")

		all_period = []
		for p in periodes_chauffage:
			all_period.extend(p)
		# print(f"begin:{calculationParams.begin}\ntimestamps:{[d for d in consumerBlock.decisions]}\nperiodes:{periodes_chauffage}\nperiod==timestamps: {all_period == [d for d in consumerBlock.decisions]}")
		
		periode_timestamps_dict: Dict[int, List[int]] = {}
		for periode in periodes_chauffage:
			for i in range(max(1,len(periode) - 3)):
				current_periode = periode[i:i+4]
				periode_timestamps_dict[current_periode[-1]] = current_periode
		# print(f"periodes:{periodes_chauffage}\ndict:{periode_timestamps_dict}")

		def percentage_constraint(block: pyo.Block, t):
			if t in periode_timestamps_dict.keys():
				periode = periode_timestamps_dict[t]
				periodes_values = [block.decisions[p] for p in periode if p > calculationParams.begin]
				if len(periodes_values) == 0:
					return pyo.Constraint.Feasible
				previous_values = [1 if p in self.lancement_45m_precedent else 0 for p in periode if p <= calculationParams.begin]
				if len(previous_values) > 0:
					goal = (self.pourcentage_eco_consigne * len(periode) - max(2, sum(previous_values)))
				else:
					goal = self.pourcentage_eco_consigne * len(periode)
				# print(f"{t=} pv:{periodes_values} >= {goal=}")
				return sum(periodes_values) >= goal
			else:
				return pyo.Constraint.Feasible
		consumerBlock.constraint_percentage = pyo.Constraint(consumerBlock.decision_set, rule = percentage_constraint)
	
	def _get_decisions(self, calculationParams : CalculationParams, activation_timestamps : List[int]) -> np.ndarray:
		toReturn = np.zeros((calculationParams.simulation_size,), np.int64)
		activation_steps = list(map((lambda x: (x - calculationParams.begin) // calculationParams.step_size_s), activation_timestamps))
		for step in activation_steps:
			toReturn[step] = 1
		return toReturn
	
	def _calcul_consommation(self, calculationParams : CalculationParams) -> None:
		self.calcul_pourcentage(calculationParams)
		#TODO evolution future, estimer les consommations en fonction de la temperature exterieure

	def _get_consumption_curve(self, calculationParams : CalculationParams, decisions : List[int]):
		toReturn = np.full((calculationParams.simulation_size,), self.conso_low, dtype=np.int64)
		for index, timestamp in enumerate(range(calculationParams.begin, calculationParams.end + 1, calculationParams.step_size_s)):
			if timestamp in decisions:
				toReturn[index] = self.conso_high
		return toReturn
	
	def _get_consumption_t(self, consumerBlock: pyo.Block, calculationParams: CalculationParams, step_timestamp: int) -> pyo.Var:
		to_return = self.conso_low
		if step_timestamp in consumerBlock.decision_set:
			to_return += consumerBlock.decisions[step_timestamp] * (self.conso_high - self.conso_low)
		return to_return 

if __name__ == "__main__":
	pass