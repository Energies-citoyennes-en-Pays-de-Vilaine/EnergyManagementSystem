from typing import List, Dict
from solution.Consumer_interface import Consumer_interface
from solution.Production_interface import Producer_interface
from solution.Calculation_Params import CalculationParams
import pyomo.environ as pyo
import numpy as np

class Utilisateur:
    id          : int
    consumers   : List[Consumer_interface]
    producers   : List[Producer_interface]
    production  : Dict[int, float]
    # horaireHC   : CalendrierHPHC

    def __init__(self, id) -> None:
        self.id = id
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
        productions = [p.get_production(prevision) for p in self.producers]
        to_return = {key: sum(p[key] for p in productions) for key in productions[0].keys()}
        self.production = to_return

    def create_block_submodel(self, submodel: pyo.Block, steps: pyo.RangeSet, calculationParams: CalculationParams, solar_prevision: Dict[int, float]) -> None:        
        submodel.production = pyo.Param(steps, initialize = self.get_production(solar_prevision), domain = pyo.Reals) #Production ACI

        submodel.n_consumer = pyo.Param(initialize = len(self.consumers))
        submodel.consumer_id = pyo.RangeSet(0, submodel.n_consumer - 1)
        submodel.consumers = pyo.Block(submodel.consumer_id)
        for i, consumer in enumerate(self.consumers):
            consumer.create_consumer(submodel.consumers[i], calculationParams)

        submodel.E_ACI = pyo.Var(steps, domain = pyo.NonNegativeReals)
        submodel.E_ACC = pyo.Var(steps, domain = pyo.NonNegativeReals)
        submodel.E_IMP = pyo.Var(steps, domain = pyo.NonNegativeReals)
        
        def E_ACI_limit(block, t):
            return block.E_ACI[t] <= submodel.production[t]
        submodel.E_ACI_limit = pyo.Constraint(steps, rule = E_ACI_limit)       

        def E_TOT_limit(block, t):
            return block.E_ACI[t] + block.E_ACC[t] + block.E_IMP[t] >= sum(c.get_consumption_t(block.consumers[i], calculationParams, t) for i, c in enumerate(self.consumers))
        submodel.E_TOT_limit = pyo.Constraint(steps, rule = E_TOT_limit)

        # #ACI pur
        # submodel.imports = pyo.Var(steps)
        # def import_pos(block, t):
        #     return block.imports[t] >= 0
        # submodel.import_pos = pyo.Constraint(steps, rule = import_pos)
        # def import_formula(block, t):
        #     return block.imports[t] >= (sum(c.get_consumption_t(block.consumers[i], calculationParams, t) for i, c in enumerate(self.consumers)) - block.production[t])
        # submodel.import_formula = pyo.Constraint(steps, rule = import_formula)

    def get_sum_energy(self, user_block: pyo.Block, steps):
        PRIX = {"ACI": 0, "ACCHC": 1, "ACCHP": 10, "IMPHC": 5, "IMPHP": 50} 
        return sum( user_block.E_ACI[step] * PRIX["ACI"] +
                    user_block.E_ACC[step] * PRIX["ACC" + ["HC", "HP"][self.get_HPHC(step)]] +
                    user_block.E_IMP[step] * PRIX["IMP" + ["HC", "HP"][self.get_HPHC(step)]]    for step in steps)

    def get_HPHC(self, step):
        return 0 if step%96<=8*4 or step % 96 >= 20*4 else 1 #TODO selection en fonction du calendrierHPHC interne

    def get_consumption(self, user_block: pyo.Block, calculationParams: CalculationParams) -> np.ndarray:
        simsize = calculationParams.get_simulation_size()
        consumption = np.zeros((simsize,), np.float64)

        for c, consumer in enumerate(self.consumers):
            model_consumer = user_block.consumers[c]
            for decision in [j for j in model_consumer.decision_set if round(pyo.value(model_consumer.decisions[j]),5)]:
                consumption += consumer.get_consumption_curve(calculationParams, decision)

        for i, k in zip(range(simsize), self.production.keys()):
            consumption[i] = min(0, self.production[k] - consumption[i])

        return consumption

    def get_model_consumer_decision(consumer: pyo.Block) -> List[int]:
        return [j for j in consumer.decision_set if round(pyo.value(consumer.decisions[j]),5)]
    
    def is_consumer_empty(self) -> bool:
        return len(self.consumers) == 0