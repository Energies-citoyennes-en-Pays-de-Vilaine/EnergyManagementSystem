from typing import List, Dict
from solution.Consumer_interface import Consumer_interface
from solution.Production_interface import Producer_interface
from solution.Calculation_Params import CalculationParams
from solution.Calendrier import Calendrier
import pyomo.environ as pyo
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from utils.colored_line import colored_line
from config.poids import get_poids
import datetime as dt

class Utilisateur:
    id          : int
    consumers   : List[Consumer_interface]
    producers   : List[Producer_interface]
    production  : Dict[int, float]
    calendrierHPHC   : Calendrier

    def __init__(self, id, cohorte_id) -> None:
        self.id = id
        self.cohorte_id = cohorte_id
        self.consumers = []
        self.producers = []
        self.production = {}

    def add_consumer(self, machine: Consumer_interface) -> None:
        self.consumers.append(machine)
    
    def add_producer(self, production: Producer_interface) -> None:
        self.producers.append(production)

    def get_production(self, prevision: Dict[int, float] = {}) -> Dict[int, float]:
        if self.production == {}:
            self.calcul_production(prevision)
        return self.production
    
    def calcul_production(self, prevision: Dict[int, float]) -> Dict[int, float]:
        productions = [{k: 0 for k in prevision.keys()}] + [p.get_production(prevision) for p in self.producers]
        to_return = {key: sum(p[key] for p in productions) for key in productions[0].keys()}
        self.production = to_return

    def set_calendrier(self, calendrier: Calendrier) -> None:
        self.calendrierHPHC = calendrier

    def create_block_submodel(self, user_block: pyo.Block, steps: pyo.RangeSet, calculationParams: CalculationParams, solar_prevision: Dict[int, float]) -> None:        
        user_block.production = pyo.Param(steps, initialize = self.get_production(solar_prevision), domain = pyo.Reals) #Production ACI

        user_block.n_consumer = pyo.Param(initialize = len(self.consumers))
        user_block.consumer_id = pyo.RangeSet(0, user_block.n_consumer - 1)
        user_block.consumers = pyo.Block(user_block.consumer_id)
        for i, consumer in enumerate(self.consumers):
            consumer.create_consumer(user_block.consumers[i], calculationParams)

        user_block.E_ACI = pyo.Var(steps, domain = pyo.NonNegativeReals)
        user_block.E_ACC = pyo.Var(steps, domain = pyo.NonNegativeReals)
        user_block.E_IMP = pyo.Var(steps, domain = pyo.NonNegativeReals)
        
        def E_ACI_limit(block, t):
            return block.E_ACI[t] <= user_block.production[t]
        user_block.E_ACI_limit = pyo.Constraint(steps, rule = E_ACI_limit)       

        def E_TOT_limit(block, t):
            return (block.E_ACI[t] + block.E_ACC[t] + block.E_IMP[t]) >= sum(consumer.get_consumption_t(block.consumers[i], calculationParams, t) for i, consumer in enumerate(self.consumers))
        user_block.E_TOT_limit = pyo.Constraint(steps, rule = E_TOT_limit)

    def is_step_HPHC(self, step) -> bool:
        return self.calendrierHPHC.is_heure_creuse(dt.datetime.fromtimestamp(step))
    
    def get_sum_energy(self, user_block: pyo.Block, steps):
        poids = get_poids(self.cohorte_id)
        return sum( user_block.E_ACI[step] * poids["ACI"] +
                    user_block.E_ACC[step] * poids["ACC" + ["HP", "HC"][self.is_step_HPHC(step)]] +
                    user_block.E_IMP[step] * poids["IMP" + ["HP", "HC"][self.is_step_HPHC(step)]]    for step in steps)

    def get_consumption(self, user_block: pyo.Block, calculationParams: CalculationParams) -> np.ndarray:
        consumption = np.zeros((calculationParams.simulation_size,), np.float64)

        for c, consumer in enumerate(self.consumers):
            model_consumer = user_block.consumers[c]
            decisions = [j for j in model_consumer.decision_set if round(pyo.value(model_consumer.decisions[j]),5)]
            # print(decisions, [pyo.value(model_consumer.decisions[j]) for j in model_consumer.decision_set])
            for decision in decisions:
                consumption += consumer.get_consumption_curve(calculationParams, decision)

        for i, k in zip(range(calculationParams.simulation_size), self.production.keys()):
            consumption[i] = min(0, self.production[k] - consumption[i])

        return consumption

    def get_model_consumer_decision(consumer_block: pyo.Block) -> List[int]:
        return [j for j in consumer_block.decision_set if round(pyo.value(consumer_block.decisions[j]),5)]
    
    def is_consumer_empty(self) -> bool:
        return len(self.consumers) == 0
    
    
    def show_user_consumptions(self, plt_ax, user_block: pyo.Block, ACC_production: np.ndarray, calculationParams: CalculationParams) -> None:
        # print("ACI prod: ", sum(list(self.get_production().values())))
        machine_number = len(self.consumers)
        vals = np.ones((machine_number, 4))
        vals[:, 0] = np.linspace(254/256, 255/256, machine_number)
        vals[:, 1] = np.linspace(203/256, 239/256, machine_number)
        vals[:, 2] = np.linspace(27/256, 188/256, machine_number)
        yellows = ListedColormap(vals)

        # print(f"{self.id}\n{[int(pyo.value(user_block.E_ACI[v])) for v in user_block.E_ACI]}"+
        #       f"\n{[int(pyo.value(user_block.E_ACC[v])) for v in user_block.E_ACC]}"+
        #       f"\n{[int(pyo.value(user_block.E_IMP[v])) for v in user_block.E_IMP]}")

        data = []
        # production_colors = [["#96B1D6","#173C74"][self.is_step_HPHC(s)] for s in calculationParams.get_time_array()]
        blues = ListedColormap(["#173C74", "#96B1D6"])
        ACI_production = np.array(list(self.get_production().values()))
        plt_ax.bar(x=np.arange(calculationParams.simulation_size), height=ACI_production, color="#008440", width=1.2, zorder=0)
        # plt_ax.bar(x=np.arange(calculationParams.simulation_size), height=ACC_production, bottom=ACI_production, color=production_colors, width=1.2, zorder=0)
        # plt_ax.scatter(x=np.arange(calculationParams.simulation_size), y=ACC_production, color=production_colors, zorder=0)
        colored_line(x=np.arange(calculationParams.simulation_size), y=ACC_production, color=[self.is_step_HPHC(s) for s in calculationParams.get_time_array()], ax=plt_ax, cmap=blues)
        plt_ax.plot(np.arange(calculationParams.simulation_size), np.array([0]*calculationParams.simulation_size), "black", linewidth=.1)
        for c, consumer in enumerate(self.consumers):
            model_consumer = user_block.consumers[c]
            curent_data = np.zeros((calculationParams.get_simulation_size(),), np.float64)
            for decision in [j for j in model_consumer.decision_set if round(pyo.value(model_consumer.decisions[j]),5)]:
                curent_data += consumer.get_consumption_curve(calculationParams, decision)
            data.append(curent_data)
            plt_ax.bar(x = np.arange(calculationParams.simulation_size), height = curent_data, bottom=sum(data[0:c]), color=yellows(c), zorder=2, width=.4)#, width=.4
        plt_ax.bar(x = np.arange(calculationParams.simulation_size), height = [min(0,list(self.get_production().values())[i] - sum(data)[i]) for i in range(calculationParams.simulation_size)], color="#C44536", width=.5, zorder=2)
        step_x_ticks = [i for i in range(0, calculationParams.simulation_size, 24)]
        step_x_label = ["{:%a %d %Hh%M}".format(dt.datetime.fromtimestamp(timestamp = calculationParams.begin) + dt.timedelta(seconds=calculationParams.step_size_s) * i) for i in step_x_ticks]
        plt_ax.set_xticks(step_x_ticks, labels=step_x_label, rotation=45, ha="right", rotation_mode="anchor", size=7)
        plt_ax.set_ylabel(f"{self.id}")
        plt_ax.label_outer()