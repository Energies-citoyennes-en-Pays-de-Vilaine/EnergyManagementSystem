
# from solution.Consumer_interface import Consumer_interface
from solution.Utilisateur import Utilisateur
from solution.Calculation_Params import CalculationParams
from solution.ConsumerTypes.ECSConsumer import ECSConsumer
from solution.Exceptions.SpecifiedListTypeException import SpecifiedListTypeException, check_for_specified_list_type_exception
from typing import *
# import scipy.optimize as opt
import numpy as np
import pyomo.environ as pyo
from utils.time import timestamp


class Problem():
    utilisateurs                  : List[Utilisateur]
    calculationParams             : CalculationParams
    is_optimal                    : bool
    has_ran                       : bool
    has_results                   : bool
    is_ready_to_run               : bool
    result                        : np.ndarray
    model                         : pyo.ConcreteModel
    # consumers                     : List[Consumer_interface]
    # constraint_matrix             : np.ndarray
    # constraint_low                : List[float]
    # constraint_high               : List[float]
    # integrality                   : List[int]
    # minimizing_matrix             : List[float]

    def __init__(self, utilisateurs: List[Utilisateur], calculationParams: CalculationParams) -> None:
        self.utilisateurs                  = utilisateurs
        self.calculationParams             = calculationParams
        self.has_ran                       = False
        self.is_optimal                    = False
        self.has_results                   = False
        self.is_ready_to_run               = False
        self.result                        = None
    
    def create_model(self, solar_prevision: Dict[int, float]) -> None:
        model = pyo.ConcreteModel()
        round_start_timestamp = timestamp.get_round_timestamp()
        model.n_steps = pyo.Param(initialize = self.calculationParams.get_simulation_size(), domain = pyo.PositiveIntegers)
        model.steps = pyo.RangeSet(round_start_timestamp, round_start_timestamp + (model.n_steps - 1) * self.calculationParams.step_size, self.calculationParams.step_size)

        model.n_users = pyo.Param(initialize = len(self.utilisateurs), domain = pyo.PositiveIntegers)
        model.users_id = pyo.RangeSet(0, model.n_users - 1)
        model.utilisateurs = pyo.Block(model.users_id)
        for i, utilisateur in enumerate(self.utilisateurs):
            utilisateur.create_block_submodel(model.utilisateurs[i], model.steps, self.calculationParams, solar_prevision)
        
        def objective_function(m):
            return sum(sum(m.utilisateurs[u].imports[t] for t in m.steps) for u in m.users_id)
        model.objective = pyo.Objective(rule = objective_function, sense = pyo.minimize)  

        self.model = model
        self.is_ready_to_run = True
    
    def solve(self, time_limit: int = 100, force: bool = False):
        if self.has_results and not force:
            return
        # if not self.calculationParams.check():
        #     return
 
        time_limit_dict = {
        'scip'               : "limits/time",
        'gurobi'             : "TimeLimit",
        }
        solver_name = "scip"
        solver = pyo.SolverFactory(solver_name)
        options = {}
        if time_limit: 
            options[time_limit_dict[solver_name]] = time_limit
        
        result = solver.solve(self.model, options = options)
        self.result = result.solver.status

        self.has_results = True
        print("Resultats: ", self.result)
        # self.fun_val     = result.fun
        return result
    
    def get_consumption(self) -> np.ndarray:
        consumption = np.zeros((self.calculationParams.get_simulation_size(),), np.float64)
        for u, utilisateur in enumerate(self.utilisateurs):
            # utilisateur.get_consumption()
            for c, consumer in enumerate(utilisateur.consumers):
                for decision in get_model_consumer_decision(self.model.utilisateurs[u].consumers[c]):
                    consumption += consumer.get_consumption_curve(self.calculationParams, decision)
        return consumption
    
    def get_decisions(self) -> List:
        problem_decisions = []
        for u, utilisateur in enumerate(self.utilisateurs):
            for c, consumer in enumerate(utilisateur.consumers):
                decisions = get_model_consumer_decision(self.model.utilisateurs[u].consumers[c])
                if len(problem_decisions) == 1:
                    problem_decisions.append(
                        {
                            "id"            : consumer.id,
                            "reocurring"    : consumer.is_reocurring,
                            "is_ECS"        : type(consumer) == ECSConsumer,
                            "decisions"     : consumer.get_decisions(self.calculationParams, decisions[0]).tolist(),
                            "consumer"      : consumer
                        })
                #TODO considérer les décicions multiples (ECS, Chauffage)
        return problem_decisions
    
def get_model_consumer_decision(consumer: pyo.Block) -> List[int]:
    return [j for j in consumer.decision_set if round(pyo.value(consumer.decisions[j]),5)]

#region ELFE
    # def prepare(self, force = False) :
    #     if self.is_ready_to_run and not force:
    #         #TODO_ELFE add a warning
    #         return
    #     consumers = self.consumers
    #     calculationParams = self.calculationParams
    #     check_for_specified_list_type_exception(consumers, Consumer_interface)
    #     check_for_specified_list_type_exception(calculationParams.base_minimization_constraints, List)
    #     for base_minimization_constraint in calculationParams.base_minimization_constraints:
    #         check_for_specified_list_type_exception(base_minimization_constraint, float)
    #     constraint_matrix_width  = calculationParams.get_simulation_size()
    #     constraint_matrix_height = calculationParams.get_simulation_size()
    #     for consumer in consumers:
    #         constraint_matrix_width  += consumer.get_minimizing_variables_count(calculationParams)
    #         constraint_matrix_height += consumer.get_constraints_size(calculationParams)
    #     constraint_matrix = np.zeros((constraint_matrix_height, constraint_matrix_width), dtype=np.float64)
    #     current_x = 0
    #     current_y = 0
    #     for i in range(calculationParams.get_simulation_size()):
    #         constraint_matrix[i, i] = 1
    #     current_x += calculationParams.get_simulation_size()
    #     current_y += calculationParams.get_simulation_size()
    #     constraint_low    = []
    #     for base_minimization_constraint in calculationParams.base_minimization_constraints:
    #         constraint_low += base_minimization_constraint
    #     for consumer in consumers:
    #         if consumer.has_base_consumption:
    #             consumer_base_consumption = consumer.get_base_consumption(calculationParams)
    #             for i in range(len(consumer_base_consumption)):
    #                 if consumer_base_consumption[i] != 0:
    #                     constraint_low[i] += consumer_base_consumption[i]
    #     constraint_high   = [np.inf for i in range(calculationParams.get_simulation_size())]
    #     minimizing_matrix = [1 for i in range(calculationParams.get_simulation_size())]
    #     integrality       = [0 for i in range(calculationParams.get_simulation_size())]
    #     for consumer in consumers:
    #         consumer.fill_minimizing_constraints(calculationParams, constraint_matrix, [current_x], [0])
    #         consumer.fill_functionnal_constraints(calculationParams, constraint_matrix, current_x, current_y)
    #         current_x += consumer.get_minimizing_variables_count(calculationParams)
    #         current_y += consumer.get_constraints_size(calculationParams)
    #         consumer_constraints_boundaries = consumer.get_functionnal_constraints_boundaries(calculationParams)
    #         constraint_low    += consumer_constraints_boundaries[0]
    #         constraint_high   += consumer_constraints_boundaries[1]
    #         minimizing_matrix += consumer.get_f_contrib(calculationParams)
    #         integrality       += consumer.get_integrality(calculationParams)
    #     self.constraint_matrix = constraint_matrix
    #     self.constraint_bound_low    = constraint_low
    #     self.constraint_bound_high   = constraint_high
    #     self.integrality       = integrality
    #     self.minimizing_matrix = minimizing_matrix
    #     self.is_ready_to_run   = True

    # def get_consumption_old(self) -> np.ndarray:
    #     consumption = np.zeros((self.calculationParams.get_simulation_size(),), np.float64)
    #     i = self.calculationParams.get_simulation_size()
    #     for consumer in self.consumers:
    #         consumption += consumer.get_consumption_curve(self.calculationParams, self.result[i: i+consumer.get_minimizing_variables_count(self.calculationParams)])
    #         i += consumer.get_minimizing_variables_count(self.calculationParams)
    #     return consumption
#endregion