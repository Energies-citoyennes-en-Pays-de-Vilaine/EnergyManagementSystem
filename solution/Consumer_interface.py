from typing import *
from solution.Exceptions.ListShapeException import check_list_size
from solution.Exceptions.SpecifiedListTypeException import *
from solution.Exceptions.FunctionNotExistingException import *
from solution.Calculation_Params import CalculationParams
from dataclasses import InitVar
import numpy as np
import pyomo.environ as pyo

class Consumer_interface():
	id: int
	has_base_consumption : InitVar[bool]
	is_reocurring: InitVar[bool]
	consumer_machine_type : Optional[int]
	
	def create_consumer(self, block: pyo.Block, calculationParams: CalculationParams) -> None:
		checkFunctionExist(self, "_create_consumer_variable")
		self._create_consumer_variable(block, calculationParams)
		checkFunctionExist(self, "_create_consumer_constraint")
		self._create_consumer_constraint(block, calculationParams)
		self.calcul_consommation(calculationParams)

	def get_consumption_t(self, block: pyo.Block, calculationParams: CalculationParams, step_timestamp: int) -> pyo.Var:
		checkFunctionExist(self, "_get_consumption_t")
		return self._get_consumption_t(block, calculationParams, step_timestamp)

	def calcul_consommation(self, calculationParams: CalculationParams) -> None:
		checkFunctionExist(self, "_calcul_consommation")
		self._calcul_consommation(calculationParams)
	
	def get_decisions(self, calculationParams : CalculationParams, variables : List[float]) -> np.ndarray:
		checkFunctionExist(self, "_get_decisions")
		decisions = self._get_decisions(calculationParams, variables)
		return decisions

	def get_consumption_curve(self, calculationParams: CalculationParams, decision: int) -> np.ndarray:
		checkFunctionExist(self, "_get_consumption_curve")
		consumption_curve = self._get_consumption_curve(calculationParams, decision)
		#TODO_ELFE better unit tests
		check_for_specified_numpy_array_type_exception(consumption_curve, np.float64)
		return consumption_curve
		
	# def get_f_contrib(self, calculationParams : CalculationParams) -> List[float]:
	# 	checkFunctionExist(self, "_get_f_contrib")
	# 	f_contrib = self._get_f_contrib(calculationParams)
	# 	check_for_specified_list_type_exception(f_contrib, float)
	# 	return f_contrib

	# def get_integrality(self, calculationParams : CalculationParams) -> List[int]:
	# 	checkFunctionExist(self, "_get_integrality")
	# 	integrality = self._get_integrality(calculationParams)
	# 	check_for_specified_list_type_exception(integrality, int)
	# 	return integrality

	# def get_minimizing_constraints(self, calculationParams : CalculationParams) -> List[np.ndarray]:
	# 	matrices_to_return : List[np.ndarray] = [] #TODO_ELFE add a mecanism to identify the others if v2 is required
	# 	height = calculationParams.get_simulation_size()
	# 	width = self.get_constraints_size(calculationParams)
	# 	matrices_to_return.append(np.zeros((height, width)))
	# 	#zeros is height, width
	# 	self.fill_minimizing_constraints(calculationParams, matrices_to_return[0], [0], [0])
	# 	minimizing_constraints = matrices_to_return
	# 	check_for_specified_list_type_exception(minimizing_constraints, np.ndarray)
	# 	return minimizing_constraints

	# def get_functionnal_constraints(self, calculationParams : CalculationParams) -> np.ndarray:
	# 	checkFunctionExist(self, "_fill_functionnal_constraints")
	# 	width = self.get_minimizing_variables_count(calculationParams)
	# 	height = self.get_constraints_size(calculationParams)
	# 	functionnal_constraints = np.zeros((height, width))
	# 	self.fill_functionnal_constraints(calculationParams, functionnal_constraints, 0, 0)
	# 	check_for_specified_numpy_array_type_exception(functionnal_constraints, np.float64)
	# 	return functionnal_constraints
	
	# def get_functionnal_constraints_boundaries(self, calculationParams : CalculationParams) -> List[List[float]]:
	# 	checkFunctionExist(self, "_get_functionnal_constraints_boundaries")
	# 	functionnal_constraints = self._get_functionnal_constraints_boundaries(calculationParams)
	# 	check_for_specified_list_type_exception(functionnal_constraints, List)
	# 	check_list_size(functionnal_constraints, 2)
	# 	check_for_specified_list_type_exception(functionnal_constraints[0], float)
	# 	check_for_specified_list_type_exception(functionnal_constraints[1], float)
	# 	#TODO_ELFE add better checks once all get_size interfaces will be required
	# 	return functionnal_constraints
	
	# def get_minimizing_variables_count(self, calculationParams : CalculationParams) -> int:
	# 	checkFunctionExist(self, "_get_minimizing_variables_count")
	# 	functionnal_constraints = self._get_minimizing_variables_count(calculationParams)
	# 	return functionnal_constraints
	
	# def get_constraints_size(self, calculationParams : CalculationParams) -> int:
	# 	checkFunctionExist(self, "_get_constraints_size")
	# 	functionnal_constraints = self._get_constraints_size(calculationParams)
	# 	return functionnal_constraints

	# def get_base_consumption(self, calculationParams : CalculationParams) -> np.ndarray:
	# 	try : 
	# 		if not self.has_base_consumption:
	# 			return np.zeros((len(calculationParams.get_time_array()),))
	# 	except AttributeError:
	# 		return np.zeros((len(calculationParams.get_time_array()),))
	# 	checkFunctionExist(self, "_get_base_consumption")
	# 	base_consumption = self._get_base_consumption(calculationParams)
	# 	check_for_specified_numpy_array_type_exception(base_consumption, np.float64)
	# 	return base_consumption

	# def fill_minimizing_constraints(self, calculationParams : CalculationParams, tofill : np.ndarray, xpars : List[int], ypars : List[int]):
	# 	checkFunctionExist(self, "_fill_minimizing_constraints")
	# 	check_for_specified_list_type_exception(xpars, int)
	# 	check_for_specified_list_type_exception(ypars, int)
	# 	self._fill_minimizing_constraints(calculationParams, tofill, xpars, ypars)

	# def fill_functionnal_constraints(self, calculationParams: CalculationParams, tofill: np.ndarray, xpar: int, ypar: int):
	# 	checkFunctionExist(self, "_fill_functionnal_constraints")
	# 	self._fill_functionnal_constraints(calculationParams, tofill, xpar, ypar)
	