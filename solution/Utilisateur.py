from typing import List, Dict
from solution.Consumer_interface import Consumer_interface
from solution.Production_interface import Producer_interface
from solution.Calculation_Params import CalculationParams
import pyomo.environ as pyo
from numpy import array

class Utilisateur:
    id          : int
    consumers   : List[Consumer_interface]
    producers  : List[Producer_interface]
    # horaireHC   : CalendrierHPHC

    def __init__(self, id) -> None:
        self.id = id
        self.consumers = []
        self.producers = []

    def add_consumer(self, machine: Consumer_interface) -> None:
        self.consumers.append(machine)
    
    def add_producer(self, production: Producer_interface) -> None:
        self.producers.append(production)

    def get_production(self, prevision: Dict[int, float]) -> Dict[int, float]:
        productions = [p.get_production(prevision) for p in self.producers]
        to_return = {key: sum(p[key] for p in productions) for key in productions[0].keys()}
        return to_return

    def create_block_submodel(self, submodel: pyo.Block, steps: pyo.RangeSet, calculationParams: CalculationParams, solar_prevision: Dict[int, float]) -> None:        
        submodel.production = pyo.Param(steps, initialize = self.get_production(solar_prevision), domain = pyo.Reals)

        submodel.n_consumer = pyo.Param(initialize = len(self.consumers))
        submodel.consumer_id = pyo.RangeSet(0, submodel.n_consumer - 1)
        submodel.consumers = pyo.Block(submodel.consumer_id)
        for i, consumer in enumerate(self.consumers):
            consumer.create_consumer(submodel.consumers[i], calculationParams)

        #TODO calendrier
        # submodel.horaires = pyo.Param(steps, initialize = self.horaireHC.calculate_steps(params.begin))

        submodel.imports = pyo.Var(steps)
        def import_pos(block, t):
            return block.imports[t] >= 0
        submodel.import_pos = pyo.Constraint(steps, rule = import_pos)
        def import_formula(block, t):
            return block.imports[t] >= (sum(c.get_consumption_t(block.consumers[i], calculationParams, t) for i, c in enumerate(self.consumers)) - block.production[t])# * (submodel.horaires[t] * 49 + 1)
        submodel.import_formula = pyo.Constraint(steps, rule = import_formula)