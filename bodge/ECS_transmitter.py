from typing import List
from database.EMS_db_types import EMSResult, EMSResultEcs
from database.ELFE_db_types import ELFE_database_names
from database.query import fetch
from credentials.db_credentials import db_credentials
from math import ceil
from solution.Calculation_Params import CalculationParams
MODE_PILOTE = 30
def get_ecs_results_to_transmit(first_valid_timestamp: int, sim_params : CalculationParams) -> List[EMSResult]:
	query = "SELECT result.* FROM result_ecs AS result\
		INNER JOIN (SELECT MAX(res.id) AS id, res.machine_id FROM result_ecs AS res\
		GROUP BY res.machine_id) AS res\
		ON res.id=result.id AND res.machine_id = result.machine_id"
	query_result = fetch(db_credentials["EMS"], query)
	ECS_in_piloted_mode_query = f"SELECT epm.id\
		FROM {ELFE_database_names['ELFE_EquipementPilote']} AS epm\
		INNER JOIN {ELFE_database_names['ELFE_BallonECS']} AS ecs ON epm.id = ecs.equipement_pilote_ou_mesure_id\
		WHERE epm.equipement_pilote_ou_mesure_mode_id={MODE_PILOTE}"
	ECS_in_piloted_mode_result = fetch(db_credentials["ELFE"], ECS_in_piloted_mode_query)
	ECS_in_piloted_mode = [int(elem[0]) for elem in ECS_in_piloted_mode_result]
	results = []
	for line in query_result:
		result_ecs : EMSResultEcs = EMSResultEcs.create_from_select_output(line)
		if result_ecs.machine_id in ECS_in_piloted_mode:
			result = EMSResult(0, first_valid_timestamp, result_ecs.machine_id, result_ecs.result_type, result_ecs.machine_type, [])
			for i in range(sim_params.simulation_size):
				result.decisions.append(0)
			index_start = 0
			for i, dec in enumerate(result_ecs.decisions):
				if dec == 1:
					index_start = i
			time_start = result_ecs.first_valid_timestamp + index_start * sim_params.step_size_s
			# print(result_ecs.duration / sim_params.step_size)
			time_end   = time_start + ceil(result_ecs.duration / sim_params.step_size_s) * sim_params.step_size_s 
			current_time = first_valid_timestamp
			for i in range(len(result.decisions)):
				if (current_time < time_start):
					current_time += sim_params.step_size_s
					continue
				if (current_time >= time_end):
					break
				result.decisions[i] = 1
				current_time += sim_params.step_size_s
			results.append(result)
	return results