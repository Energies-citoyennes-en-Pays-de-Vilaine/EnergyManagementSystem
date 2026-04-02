from typing import *
from dataclasses import dataclass

@dataclass(init=False, repr=True)
class CalculationParams():
	begin                         : int
	end                           : int
	step_size                     : int
	time_delta                    : int #time between two steps in seconds
	base_minimization_constraints : List[List[float]] #Sum of nonflexible consommation - prod
	simulation_size				  : int

	def __init__(self, begin: int, end: int, step_size: int, time_delta: int, base_minimization_constraints : List[List[float]]) -> None:
		self.base_minimization_constraints = base_minimization_constraints
		self.begin = begin
		self.end = end #end is always included in the simulation; this may be important for later
		self.step_size = step_size
		self.time_delta = time_delta
		self.simulation_size = (self.end - self.begin) / self.step_size + 1
		self.check()

	def check(self, werror = True) -> bool:
		if (self.get_simulation_size() != len(self.base_minimization_constraints[0])):
			print("[\u001b[31merror\u001b[0m]: wrong size for calculationParams, constraint size:", len(self.base_minimization_constraints[0]), "expected to be", self.get_simulation_size() )
			return False
		if (self.time_delta != self.step_size):
			print("[\u001b[35;1mwarning\u001b[0m]: different step_size isn't fully supported yet, use with utmost care")
			if werror:
				return False
		return True
	
	def get_simulation_size(self) -> int:
		result = (self.end - self.begin) / self.step_size
		return int(result) + 1
	
	def get_time_array(self):
		return [i * self.step_size + self.begin for i in range(self.get_simulation_size())]