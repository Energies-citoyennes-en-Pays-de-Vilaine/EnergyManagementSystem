# from elfe_interfaces.ELFE_data_gatherer import get_machines, get_ECS, get_electric_vehicle, get_sum_consumer, get_heater_consumer
from elfe_interfaces.ELFE_data_gatherer import get_calculation_params, get_cohorte_balance, get_utilisateurs, get_production_solaire, show_productions
from utils.time.timestamp import get_round_timestamp, get_timestamp, synchronise
from database.EMS_db_types import EMSPowerCurveData, EMSResult, EMSResultEcs, EMSEnergyWeather
from database.EMS_OUT_db_types import EMSRunInfo
from database.query import fetch, execute_queries
from credentials.db_credentials import db_credentials
from solution.Calculation_Params import CalculationParams
from solution.Problem import Problem
from typing import List, Tuple
from solution.Consumer_interface import Consumer_interface
from solution.ConsumerTypes.ECSConsumer import ECSConsumer
from solution.Utilisateur import Utilisateur
from logger.run_conditions_logger import log_run_conditions_to_file
from bodge.ECS_transmitter import get_ecs_results_to_transmit
from time import time
from config.config import Config, get_config
import traceback
import sys
import numpy as np

conf : Config = get_config()
ONE_HOUR_SEC = 3600
# cohorte_id = "ACI_1"

def write_energy_weather(problem_consumption: np.ndarray, cohorte_balance: List[Tuple[int, float]]) -> None:
	if ("EMS_SORTIE" in db_credentials):
		queries = []
		# print("problem_consumption\n", problem_consumption)
		meteo_energie = problem_consumption + np.array(cohorte_balance)[:,1]
		# print("meteo_energie\n", meteo_energie)
		times = sim_params.get_time_array()
		# min_conso_timestamp = None
		# max_conso_timestamp = None
		# min_conso = None
		# max_conso = None
		for i in range(len(times)):
			queries.append(EMSEnergyWeather(times[i], int(meteo_energie[i]), cohorte_id).get_create_or_update_in_table_str("p_c_with_flexible_consumption"))
		# 	if (datetime.fromtimestamp(times[i], timezone.utc).minute == 0):
		# 		j = 0
		# 		current_conso = 0
		# 		while (i + j < len(times) and times[i + j] - times[i] < ONE_HOUR_SEC):
		# 			current_conso += consumption[i + j]
		# 			j = j + 1
		# 		if (j != 0):
		# 			current_conso = int(current_conso / j)
		# 			if (min_conso == None or min_conso > current_conso):
		# 				min_conso = current_conso
		# 				min_conso_timestamp = times[i]
		# 			if (max_conso == None or max_conso < current_conso):
		# 				max_conso = current_conso
		# 				max_conso_timestamp = times[i]

		# queries.append(EMSRunInfo(round_start_timestamp, run_time_ms, len(utilisateurs), min_conso_timestamp, min_conso, max_conso_timestamp, max_conso).get_create_or_update_in_table_str("ems_run_info"))
		execute_queries(db_credentials["EMS_SORTIE"], queries)

if __name__ == "__main__":
	cohorte_id = sys.argv[1]
	if len(sys.argv) >= 3:
		timestamp = synchronise(int(sys.argv[2]))
		round_start_timestamp = timestamp + get_config().delta_time_simulation_s
	else:
		timestamp = get_timestamp()
		round_start_timestamp = get_round_timestamp()
	cohorte_balance = get_cohorte_balance(round_start_timestamp)
	cohorte_balance_dict = {t[0]:t[1] for t in cohorte_balance}
	# show_productions(round_start_timestamp)
	solar_expected_production = get_production_solaire(round_start_timestamp)
	sim_params: CalculationParams = get_calculation_params(simulation_datas=cohorte_balance, timestamp=timestamp)
	utilisateurs: List[Utilisateur] = []

	utilisateurs = get_utilisateurs(timestamp, sim_params, cohorte_id=cohorte_id) #temp

	# try:
	# 	utilisateurs = get_utilisateurs(timestamp, sim_params, cohorte_id=cohorte_id)
	# except Exception as e:
	# 	print(e, "tb=", e.__traceback__.tb_frame)

	if (conf.log_problem_settings_active):
		log_run_conditions_to_file(f"{conf.log_problem_settings_path}/{timestamp}_{round_start_timestamp}.py", timestamp, round_start_timestamp, sim_params, utilisateurs)

	if len(utilisateurs) == 0:
		if ("EMS_SORTIE" in db_credentials):
			write_energy_weather(np.zeros((sim_params.get_simulation_size(),), np.float64), cohorte_balance)
	else:
		try:
			problem = Problem(utilisateurs, sim_params, solar_expected_production, cohorte_balance_dict)
			problem.create_pyo_model()
			res = problem.solve(time_limit=conf.max_time_to_solve_s)
		except Exception as e:
			print("Erreur EMS launcher")
			traceback.print_exc()
			
		decisions = problem.get_decisions()	
		results = []
		results_ECS = []
		for decision in decisions:
			result_type = 0 if decision["reocurring"] == False else 1
			consumer : Consumer_interface = decision["consumer"]
			if decision["is_ECS"] == False:
				result = EMSResult(0, round_start_timestamp, decision["id"], result_type, consumer.consumer_machine_type, decision["decisions"] )
				results.append(result)
			else:
				ecs_consumer : ECSConsumer = decision["consumer"]
				result = EMSResultEcs(0, round_start_timestamp, decision["id"], result_type, consumer.consumer_machine_type, ecs_consumer.get_total_duration(), decision["decisions"])
				results_ECS.append(result)
		
		queries_ECS = [result.get_append_in_table_str("result_ecs") for result in results_ECS]
		execute_queries(db_credentials["EMS"], queries_ECS)
		results += get_ecs_results_to_transmit(round_start_timestamp, sim_params)
		queries = [result.get_append_in_table_str("result") for result in results]
		# execute_queries(db_credentials["EMS"], queries)
		# if ("EMS_SORTIE" in db_credentials):
		# 	execute_queries(db_credentials["EMS_SORTIE"], queries)
		
		write_energy_weather(problem.get_consumption(), cohorte_balance)
		problem.show_consumptions()
		problem.show_user_consumptions()