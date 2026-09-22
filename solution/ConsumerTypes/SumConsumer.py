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
	nb_lancement_24h_precedent	: int
	calendrier					: Calendrier_confort
	# calculationParams			: CalculationParams

	def __init__(self, id, conso_low: float, conso_high: float, pourcentage_eco: int, calendrier: Calendrier_confort, calculationParams: CalculationParams, nb_lancement_24h_precedent: int = 0, consumer_machine_type = -1):
		self.id = id
		self.conso_low = conso_low
		self.conso_high = conso_high
		self.pourcentage_eco_consigne = pourcentage_eco / 100
		self.calendrier = calendrier
		self.nb_lancement_24h_precedent = nb_lancement_24h_precedent
		self.consumer_machine_type = consumer_machine_type
		self.has_base_consumption = False
		self.is_reocurring = False
		# self.calculationParams = calculationParams

	def __repr__(self):
		return f"id:{self.id}, %:{self.pourcentage_eco_consigne}, low:{self.conso_low}, high:{self.conso_high},\n calendrier:{self.calendrier},\n historique:{self.nb_lancement_24h_precedent}"

	def calcul_pourcentage(self, calculationParams: CalculationParams) -> None:
		zone_passe, zone_futur = self.calendrier.get_past_confort_hours(calculationParams.begin), self.calendrier.get_futur_confort_hours(calculationParams.begin)
		self.pourcentage_eco_futur = self.pourcentage_eco_consigne + (self.pourcentage_eco_consigne * zone_passe - self.nb_lancement_24h_precedent) / zone_passe
		self.nb_lancement_48h_suivant = self.pourcentage_eco_futur * zone_futur

	def _create_consumer_variable(self, consumerBlock: pyo.Block, calculationParams: CalculationParams) -> None:
		filter_calendrier = lambda m, x: self.calendrier.is_confort_timestamp(x)
		consumerBlock.decision_set = pyo.RangeSet(calculationParams.begin, calculationParams.end, calculationParams.step_size_s, filter=filter_calendrier)
		consumerBlock.decisions = pyo.Var(consumerBlock.decision_set, domain = pyo.Binary)

	def _create_consumer_constraint(self, consumerBlock: pyo.Block, calculationParams: CalculationParams) -> None:
		def percentage_constraint(block: pyo.Block):
			return sum(block.decisions[i] for i in consumerBlock.decision_set) >= self.nb_lancement_48h_suivant
		consumerBlock.constraint_percentage = pyo.Constraint(rule = percentage_constraint)
	
	def _get_decisions(self, calculationParams : CalculationParams, activation_timestamps : List[int]) -> np.ndarray:
		toReturn = np.zeros((calculationParams.simulation_size,), np.int64)
		activation_steps = list(map(synchronise, activation_timestamps))
		for step in activation_steps:
			toReturn[step] = 1
		return toReturn
	
	def _calcul_consommation(self, calculationParams : CalculationParams) -> None:
		self.calcul_pourcentage(calculationParams)
		#TODO evolution future, estimer les consommations en fonction de la temperature exterieure

	def _get_consumption_curve(self, calculationParams : CalculationParams, decisions : List[int]):
		toReturn = np.zeros((calculationParams.simulation_size,), np.int64)
		for index, decision in enumerate(decisions):
			toReturn[index] = self.conso_low if decision == 0 else self.conso_high
		return toReturn
	
	def _get_consumption_t(self, consumerBlock: pyo.Block, calculationParams: CalculationParams, step_timestamp: int) -> pyo.Var:
		to_return = self.conso_low
		if step_timestamp in consumerBlock.decisions:
			to_return += consumerBlock.decisions[step_timestamp] * (self.conso_high - self.conso_low)
		return to_return 

if __name__ == "__main__":
	pass