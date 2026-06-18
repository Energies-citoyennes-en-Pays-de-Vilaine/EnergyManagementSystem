
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
import datetime as dt

class Problem():
    utilisateurs                  : List[Utilisateur]
    calculationParams             : CalculationParams
    is_optimal                    : bool
    has_ran                       : bool
    has_results                   : bool
    is_ready_to_run               : bool
    result                        : np.ndarray
    model                         : pyo.ConcreteModel

    def __init__(self, utilisateurs: List[Utilisateur], calculationParams: CalculationParams, solar_previsions: Dict[int, float], cohorte_balance: Dict[int, float]) -> None:
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
        round_start_timestamp = self.calculationParams.begin
        model.n_steps = pyo.Param(initialize = self.calculationParams.get_simulation_size(), domain = pyo.PositiveIntegers)
        model.steps = pyo.RangeSet(round_start_timestamp, round_start_timestamp + (model.n_steps - 1) * self.calculationParams.step_size_s, self.calculationParams.step_size_s)
        model.equilibre = pyo.Param(model.steps, initialize = self.cohorte_balance, domain = pyo.Reals)

        model.n_users = pyo.Param(initialize = len(self.utilisateurs), domain = pyo.PositiveIntegers)
        model.users_id = pyo.RangeSet(0, model.n_users - 1)
        model.utilisateurs = pyo.Block(model.users_id)
        for i, utilisateur in enumerate(self.utilisateurs):
            utilisateur.create_block_submodel(model.utilisateurs[i], model.steps, self.calculationParams, self.solar_previsions)
        
        def E_ACC_TOT_limit(block, t):
            return sum(block.utilisateurs[u].E_ACC[t] for u in block.users_id) <= max(0, block.equilibre[t])
        model.E_ACC_TOT_limit = pyo.Constraint(model.steps, rule = E_ACC_TOT_limit)

        def objective_function(block):
            return sum(self.utilisateurs[u].get_sum_energy(block.utilisateurs[u], block.steps) for u in block.users_id)
        model.objective = pyo.Objective(rule = objective_function, sense = pyo.minimize)

        self.model = model
        self.is_ready_to_run = True
    
    def solve(self, time_limit: int = 0, force: bool = False):
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
            # user_block = self.model.utilisateurs[u]
            # steps = self.model.steps
            # print("ACI_conso: ", [pyo.value(user_block.E_ACI[t]) for t in steps])
            # print("ACC_conso: ", [pyo.value(user_block.E_ACC[t]) for t in steps])
            # print("IMP_conso: ", [pyo.value(user_block.E_IMP[t]) for t in steps])
            # print("conso:",  [pyo.value(user_block.E_ACI[t]) + pyo.value(user_block.E_ACC[t]) + pyo.value(user_block.E_IMP[t]) for t in steps])
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

        
        data = np.zeros((self.calculationParams.simulation_size,), np.float64)
        x_data = np.arange(self.calculationParams.simulation_size)
        ACC_production = np.array(list(self.cohorte_balance.values()))# // (1000 * n_users)#TODO remove (for visibility purposes)
        # plt.bar(x=x_data, height=ACC_production, color = "#173C74", width=1, zorder=0)
        plt.plot(x_data, ACC_production, color="#173C74")
        plt.plot(np.arange(self.calculationParams.simulation_size), np.array([0]*self.calculationParams.simulation_size), "black", linewidth=.1)
        for i, utilisateur in enumerate(self.utilisateurs):
            curent_data = - utilisateur.get_consumption(self.model.utilisateurs[i], self.calculationParams)
            plt.bar(x=x_data, height=curent_data, bottom=data, color=yellows(i), width=.4, zorder=10)
            data += curent_data
        plt.bar(x=x_data, height=[min(0, max(0, p)-c) for p, c in zip(ACC_production,data)], width=.4, color="#C44536", zorder=0)
        plt.legend(handles=[Line2D([0],[0], color="#173C74", lw=8, label="Production"),
                            Line2D([0],[0], color="#FECB1B", lw=8, label="Consommation"),
                            Line2D([0],[0], color="#C44536", lw=8, label="Import")])
        # plt.show()
        step_x_ticks = [i for i in range(0, self.calculationParams.simulation_size, 24)]
        step_x_label = ["{:%a %d %Hh%M}".format(dt.datetime.fromtimestamp(timestamp = self.calculationParams.begin) + dt.timedelta(seconds=self.calculationParams.step_size_s) * i) for i in step_x_ticks]
        plt.xticks(step_x_ticks, labels=step_x_label, rotation=45, ha="right", rotation_mode="anchor", size=7)
        plt.savefig("./data/temp/ACC_file.svg", format="svg")

    def show_user_consumptions(self) -> None:
        n_users = len(self.utilisateurs)
        x = max(2, int(np.ceil(np.sqrt(n_users))))
        y = max(2, int(np.floor(np.sqrt(n_users))))
        fig = plt.figure()
        grid = fig.add_gridspec(y, x, hspace = 0, wspace = 0)
        axs = grid.subplots(sharex=True, sharey=True)
        ACC_production = np.array(list(self.cohorte_balance.values()))# // 1000#TODO remove (for visibility purposes)
        for i, utilisateur in enumerate(self.utilisateurs):
            utilisateur.show_user_consumptions(plt_ax=axs[i//x, i%x], user_block=self.model.utilisateurs[i], ACC_production=ACC_production, calculationParams=self.calculationParams)
        fig.legend(handles=[Line2D([0],[0], color="#008440", lw=8, label="Production"),
                            Line2D([0],[0], color="#96B1D6", lw=8, label="Heure Creuse"),
                            Line2D([0],[0], color="#173C74", lw=8, label="Heure Pleine"),
                            Line2D([0],[0], color="#FECB1B", lw=8, label="Consommation"),
                            Line2D([0],[0], color="#C44536", lw=8, label="Import")])
        # plt.show()
        plt.savefig(f"./data/temp/ACI_file.svg", format="svg")
    
def get_model_consumer_decision(consumer: pyo.Block) -> List[int]:
    return [j for j in consumer.decision_set if round(pyo.value(consumer.decisions[j]),5)]
