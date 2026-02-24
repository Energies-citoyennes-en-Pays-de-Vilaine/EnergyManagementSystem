
from solution.Consumer_interface import Consumer_interface
from solution.Calculation_Params import CalculationParams
from solution.ConsumerTypes.ECSConsumer import ECSConsumer
from solution.Exceptions.SpecifiedListTypeException import SpecifiedListTypeException, check_for_specified_list_type_exception
from typing import *
import scipy.optimize as opt
import numpy as np


class Problem():
    consumers                     : List[Consumer_interface]
    calculationParams             : CalculationParams
    is_optimal                    : bool
    has_ran                       : bool
    has_results                   : bool
    is_ready_to_run               : bool
    result                        : np.ndarray
    constraint_matrix             : np.ndarray
    constraint_low                : List[float]
    constraint_high               : List[float]
    integrality                   : List[int]
    minimizing_matrix             : List[float]
    def __init__(self, consumers : List[Consumer_interface], calculationParams : CalculationParams) -> None:
        self.consumers                     = consumers
        self.calculationParams             = calculationParams
        self.has_ran                       = False
        self.is_optimal                    = False
        self.has_results                   = False
        self.is_ready_to_run               = False
        self.result                        = None
    def prepare(self, force = False) :
        if self.is_ready_to_run and not force:
            #TODO add a warning
            return
        consumers = self.consumers
        calculationParams = self.calculationParams
        check_for_specified_list_type_exception(consumers, Consumer_interface)
        check_for_specified_list_type_exception(calculationParams.base_minimization_constraints, List)
        for base_minimization_constraint in calculationParams.base_minimization_constraints:
            check_for_specified_list_type_exception(base_minimization_constraint, float)
        constraint_matrix_width  = calculationParams.get_simulation_size()
        constraint_matrix_height = calculationParams.get_simulation_size()
        for consumer in consumers:
            constraint_matrix_width  += consumer.get_minimizing_variables_count(calculationParams)
            constraint_matrix_height += consumer.get_constraints_size(calculationParams)
        constraint_matrix = np.zeros((constraint_matrix_height, constraint_matrix_width), dtype=np.float64)
        current_x = 0
        current_y = 0
        for i in range(calculationParams.get_simulation_size()):
            constraint_matrix[i, i] = 1
        current_x += calculationParams.get_simulation_size()
        current_y += calculationParams.get_simulation_size()
        constraint_low    = []
        for base_minimization_constraint in calculationParams.base_minimization_constraints:
            constraint_low += base_minimization_constraint
        for consumer in consumers:
            if consumer.has_base_consumption:
                consumer_base_consumption = consumer.get_base_consumption(calculationParams)
                for i in range(len(consumer_base_consumption)):
                    if consumer_base_consumption[i] != 0:
                        constraint_low[i] += consumer_base_consumption[i]
        constraint_high   = [np.inf for i in range(calculationParams.get_simulation_size())]
        minimizing_matrix = [1 for i in range(calculationParams.get_simulation_size())]
        integrality       = [0 for i in range(calculationParams.get_simulation_size())]
        for consumer in consumers:
            consumer.fill_minimizing_constraints(calculationParams, constraint_matrix, [current_x], [0])
            consumer.fill_functionnal_constraints(calculationParams, constraint_matrix, current_x, current_y)
            current_x += consumer.get_minimizing_variables_count(calculationParams)
            current_y += consumer.get_constraints_size(calculationParams)
            consumer_constraints_boundaries = consumer.get_functionnal_constraints_boundaries(calculationParams)
            constraint_low    += consumer_constraints_boundaries[0]
            constraint_high   += consumer_constraints_boundaries[1]
            minimizing_matrix += consumer.get_f_contrib(calculationParams)
            integrality       += consumer.get_integrality(calculationParams)
        self.constraint_matrix = constraint_matrix
        self.constraint_bound_low    = constraint_low
        self.constraint_bound_high   = constraint_high
        self.integrality       = integrality
        self.minimizing_matrix = minimizing_matrix
        self.is_ready_to_run   = True
    def solve(self, timeout: int = 100, has_solver : bool = False, force : bool = False):
        if self.has_results and not force:
            return
        if not self.calculationParams.check():
            return
        if not self.is_ready_to_run:
            self.prepare()
        if has_solver:
            result = opt.milp(self.minimizing_matrix, integrality = self.integrality, bounds = opt.Bounds(lb = 0, ub = np.inf), constraints = opt.LinearConstraint(self.constraint_matrix, self.constraint_bound_low, self.constraint_bound_high), options={"time_limit": timeout, "solver": "ipm"})
        else:
            result = opt.milp(self.minimizing_matrix, integrality = self.integrality, bounds = opt.Bounds(lb = 0, ub = np.inf), constraints = opt.LinearConstraint(self.constraint_matrix, self.constraint_bound_low, self.constraint_bound_high), options={"time_limit": timeout})
        self.result = result.x
        if (result.x is None):
            print("fatal error, solver didn't work")
            print(result)
        self.has_results = True
        self.fun_val     = result.fun
        return result
    def get_consumption(self) -> np.ndarray:
        consumption = np.zeros((self.calculationParams.get_simulation_size(),), np.float64)
        i = self.calculationParams.get_simulation_size()
        for consumer in self.consumers:
            consumption += consumer.get_consumption_curve(self.calculationParams, self.result[i: i+consumer.get_minimizing_variables_count(self.calculationParams)])
            i += consumer.get_minimizing_variables_count(self.calculationParams)
        return consumption
    def get_decisions(self) -> List:
        decisions = []
        i = self.calculationParams.get_simulation_size()
        for consumer in self.consumers:
            decisions.append(
                {
                    "id"                   : consumer.id,
                    "reocurring"           :  consumer.is_reocurring,
                    "is_ECS"               : type(consumer) == ECSConsumer,
                    "minimizing_variables" : self.result[i: i+consumer.get_minimizing_variables_count(self.calculationParams)],
                    "decisions"            : consumer.get_decisions(self.calculationParams, self.result[i: i+consumer.get_minimizing_variables_count(self.calculationParams)]).tolist(),
                    "consumer"             : consumer
                })
            i += consumer.get_minimizing_variables_count(self.calculationParams)
        return decisions
        """
        constraint_matrix        : np.ndarray
        constraint_bound_low     : List[float]
    constraint_bound_high    : List[float]
    minimizing_matrix        : np.ndarray
    integrality              : List[int]
    solve_status             : int
    solution_optim_variables : List[float]
    def __init__(self, constraint_matrix : np.ndarray, constraint_bound_low : List[float], constraint_bound_high : List[float], minimizing_matrix : np.ndarray, integrality : List[int]) -> None:
        self.constraint_matrix        = constraint_matrix
        self.constraint_bound_low     = constraint_bound_low
        self.constraint_bound_high    = constraint_bound_high
        self.minimizing_matrix        = minimizing_matrix
        self.integrality              = integrality
        self.solve_status             = -1
        self.solution_optim_variables = []
    def solve(self, timeout):
        if self.solve_status == -1:
            opt.milp(self.minimizing_matrix, integrality = self.integrality, bounds = opt.Bounds(0, np.inf), constraints = opt.LinearConstraint(self.constraint_matrix, self.constraint_bound_low, self.constraint_bound_high), options={"time_limit" : timeout})
    
def get_base_variables_matrix(calculationParams : CalculationParams) -> np.ndarray: 
    return np.eye(calculationParams.get_simulation_size())

def create_problem(consumers : List[Consumer_interface], calculationParams : CalculationParams):
    check_for_specified_list_type_exception(consumers, Consumer_interface)
    constraint_matrix_width  = calculationParams.get_simulation_size()
    constraint_matrix_height = calculationParams.get_simulation_size()
    for consumer in consumers:
        constraint_matrix_width  += consumer.get_minimizing_variables_count(calculationParams)
        constraint_matrix_height += consumer.get_constraints_size(calculationParams)
    constraint_matrix = np.zeros((constraint_matrix_height, constraint_matrix_width), dtype=np.float64)
    current_x = 0
    current_y = 0
    for i in range(calculationParams.get_simulation_size()):
        constraint_matrix[i, i] = 1
    current_x += calculationParams.get_simulation_size()
    current_y += calculationParams.get_simulation_size()
    constraint_low    = [0.0 for i in range(calculationParams.get_simulation_size())]
    constraint_high   = [np.inf for i in range(calculationParams.get_simulation_size())]
    minimizing_matrix = [1 for i in range(calculationParams.get_simulation_size())]
    integrality       = [0 for i in range(calculationParams.get_simulation_size())]
    for consumer in consumers:
        consumer.fill_minimizing_constraints(calculationParams, constraint_matrix, [current_x], [0])
        consumer.fill_functionnal_constraints(calculationParams, constraint_matrix, current_x, current_y)
        current_x += consumer.get_minimizing_variables_count(calculationParams)
        current_y += consumer.get_constraints_size(calculationParams)
        consumer_constraints_boundaries = consumer.get_functionnal_constraints_boundaries(calculationParams)
        constraint_low    += consumer_constraints_boundaries[0]
        constraint_high   += consumer_constraints_boundaries[1]
        minimizing_matrix += consumer.get_f_contrib(calculationParams)
        integrality       += consumer.get_integrality(calculationParams)
    return Problem(constraint_matrix, constraint_low, constraint_high, minimizing_matrix, integrality)
    """