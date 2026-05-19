
from solution.Utilisateur import Utilisateur
from solution.Calculation_Params import CalculationParams
from solution.ConsumerTypes.ECSConsumer import ECSConsumer
from solution.Exceptions.SpecifiedListTypeException import SpecifiedListTypeException, check_for_specified_list_type_exception
from typing import *
import numpy as np
import pyomo.environ as pyo
from utils.time import timestamp
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D

class Problem():
    utilisateurs                  : List[Utilisateur]
    calculationParams             : CalculationParams
    is_optimal                    : bool
    has_ran                       : bool
    has_results                   : bool
    is_ready_to_run               : bool
    result                        : np.ndarray
    model                         : pyo.ConcreteModel

    def __init__(self, utilisateurs: List[Utilisateur], calculationParams: CalculationParams, solar_previsions: Dict[int, float], cohorte_balance: List[Tuple[int, float]]) -> None:
        self.utilisateurs                  = utilisateurs
        self.calculationParams             = calculationParams
        self.solar_previsions              = solar_previsions
        self.cohorte_balance               = cohorte_balance
        self.has_ran                       = False
        self.is_optimal                    = False
        self.has_results                   = False
        self.is_ready_to_run               = False
        self.result                        = None
    
    def create_pyo_model(self) -> None:
        model = pyo.ConcreteModel()
        round_start_timestamp = timestamp.get_round_timestamp()
        model.n_steps = pyo.Param(initialize = self.calculationParams.get_simulation_size(), domain = pyo.PositiveIntegers)
        model.steps = pyo.RangeSet(round_start_timestamp, round_start_timestamp + (model.n_steps - 1) * self.calculationParams.step_size, self.calculationParams.step_size)

        model.equilibre = pyo.Param(model.steps, initialize = self.cohorte_balance, domain = pyo.Reals)

        model.n_users = pyo.Param(initialize = len(self.utilisateurs), domain = pyo.PositiveIntegers)
        model.users_id = pyo.RangeSet(0, model.n_users - 1)
        model.utilisateurs = pyo.Block(model.users_id)
        for i, utilisateur in enumerate(self.utilisateurs):
            utilisateur.create_block_submodel(model.utilisateurs[i], model.steps, self.calculationParams, self.solar_previsions)
        
        def E_ACC_TOT_limit(block, t):
            return sum(block.utilisateurs[u].E_ACC[t] for u in block.users_id) <= block.equilibre[t]
        model.E_ACC_TOT_limit = pyo.Constraint(model.steps, rule = E_ACC_TOT_limit)

        def objective_function(m):
            return sum(self.utilisateurs[u].get_sum_energy(m.utilisateurs[u], m.steps) for u in m.users_id)
        model.objective = pyo.Objective(rule = objective_function, sense = pyo.minimize)

        self.model = model
        self.is_ready_to_run = True
    
    def solve(self, time_limit: int = 100, force: bool = False):
        if self.has_results and not force:
            return
 
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
        return result
    
    def get_consumption(self) -> np.ndarray:
        consumption = np.zeros((self.calculationParams.get_simulation_size(),), np.float64)
        for u, utilisateur in enumerate(self.utilisateurs):
            consumption += utilisateur.get_consumption(self.model.utilisateurs[u], self.calculationParams)
        return consumption
    
    def get_decisions(self) -> List:
        problem_decisions = []
        for u, utilisateur in enumerate(self.utilisateurs):
            for c, consumer in enumerate(utilisateur.consumers):
                model_consumer = self.model.utilisateurs[u].consumers[c]
                decisions = [j for j, d in enumerate(model_consumer.decision_set) if round(pyo.value(model_consumer.decisions[d]),5)]
                if len(decisions) == 1:
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
    
    def show_consumptions(self) -> None:
        n_users = len(self.utilisateurs)
        vals = np.ones((n_users, 4))
        vals[:, 0] = np.linspace(254/256, 255/256, n_users)
        vals[:, 1] = np.linspace(203/256, 239/256, n_users)
        vals[:, 2] = np.linspace(27/256, 188/256, n_users)
        yellows = ListedColormap(vals)

        data = []
        plt.bar(x = np.array(self.calculationParams.get_time_array()), height=[self.cohorte_balance[1] for _ in len(self.cohorte_balance)])
        for i, utilisateur in enumerate(self.utilisateurs):
            curent_data = utilisateur.get_consumption(self.model.utilisateurs[utilisateur], self.calculationParams)
            data.append(curent_data)
            plt.bar(x = np.arange(self.calculationParams.simulation_size), height = curent_data, bottom=sum(data[0:i]), color=yellows(i), width=0.5, label=(None if i else "Consommation"))
        plt.bar(x = np.arange(self.calculationParams.simulation_size), height = [min(0,self.cohorte_balance[i][1]-sum(data)[i]) for i in range(self.calculationParams.simulation_size)], width=.5)
        plt.legend(handles=[Line2D([0],[0], color="#008440", lw=8, label="Heure Creuse"),
                            Line2D([0],[0], color="#173C74", lw=8, label="Heure Pleine"),
                            Line2D([0],[0], color="#FECB1B", lw=8, label="Consommation"),
                            Line2D([0],[0], color="#C44536", lw=8, label="Import")])
        plt.show()

    def show_user_consumptions(self) -> None:
        n_users = len(self.utilisateurs)
        x = int(np.ceil(np.sqrt(n_users)))
        y = int(np.floor(np.sqrt(n_users)))
        fig = plt.figure()
        grid = fig.add_gridspec(y, x, hspace = 0, wspace = 0)
        axs = grid.subplots(sharex=True, sharey=True)
        for i, utilisateur in enumerate(self.utilisateurs):
            utilisateur.show_user_consumptions(plt_ax=axs[i//x, i%x], user_block=self.model.utilisateurs[i], calculationParams=self.calculationParams)
        fig.legend(handles=[Line2D([0],[0], color="#008440", lw=8, label="Heure Creuse"),
                            Line2D([0],[0], color="#173C74", lw=8, label="Heure Pleine"),
                            Line2D([0],[0], color="#FECB1B", lw=8, label="Consommation"),
                            Line2D([0],[0], color="#C44536", lw=8, label="Import")])
        plt.show()
    
def get_model_consumer_decision(consumer: pyo.Block) -> List[int]:
    return [j for j in consumer.decision_set if round(pyo.value(consumer.decisions[j]),5)]
