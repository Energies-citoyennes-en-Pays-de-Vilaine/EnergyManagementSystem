from database.ELFE_db_types import ELFE_BallonECS, ELFE_BallonECSHeuresCreuses, ELFE_ChauffageAsservi, ELFE_ChauffageAsserviModeleThermique, ELFE_ChauffageNonAsservi, ELFE_EquipementPilote, ELFE_MachineGenerique, ELFE_MachineGeneriqueCycle, ELFE_VehiculeElectriqueGenerique
from database.ELFE_db_types import ELFE_database_names
from database.query import execute_queries, fetch
from database.EMS_db_types import EMSCycle,EMSCycleData, EMSDeviceTemperatureData, EMSMachineData, EMSPowerCurveData, InitialWheatherForecast, HistoricalInitialWheatherForecast
from credentials.db_credentials import db_credentials
from typing import List, Tuple, Dict, Union
from dataclasses import dataclass, field
#chauffage = ELFE_ChauffageAsserviModeleThermique(0,"modle","thermique")
#print(fetch(db_credentials["ELFE"], chauffage.get_append_in_table_str("chauffage_asservi_modele_thermique")))

MODE_PILOTE = 30

@dataclass(init=True, repr=True)
class StudyCase():
	machines         : Dict[int, Tuple[ELFE_EquipementPilote, ELFE_MachineGenerique, ELFE_MachineGeneriqueCycle]]
	drived_heater    : Dict[int, Tuple[ELFE_EquipementPilote, ELFE_ChauffageAsservi]]
	undrived_heater  : Dict[int, Tuple[ELFE_EquipementPilote, ELFE_ChauffageNonAsservi]]
	electric_vehicle : Dict[int, 	Tuple[ELFE_EquipementPilote, ELFE_VehiculeElectriqueGenerique]]
	thermic_models   : Dict[int, ELFE_ChauffageAsserviModeleThermique]
	ecs              : Dict[int, Tuple[ELFE_EquipementPilote, ELFE_BallonECS, List[ELFE_BallonECSHeuresCreuses]]] = field(default_factory=dict)
	def save_to_loadable_py_file(self, varname, py_file_name: str):
		with open(py_file_name, "w") as outp:
			print("from elfe_interfaces.ELFE_database_populator import *", file=outp)
			print(varname, "=",self, file=outp )
	def schedule_machine(self, credentials, id, timestamp, delta):
		self.machines[id][1].timestamp_de_fin_souhaite        = timestamp
		self.machines[id][1].delai_attente_maximale_apres_fin = delta
		execute_queries(credentials, [self.machines[id][1].get_update_in_table_str(ELFE_database_names["ELFE_MachineGenerique"])])
		self.machines[id][0].equipement_pilote_ou_mesure_mode = MODE_PILOTE
		execute_queries(credentials, [self.machines[id][0].get_update_in_table_str(ELFE_database_names["ELFE_EquipementPilote"])])

def drop_and_recreate(credentials):
	from database.ELFE_db_creator import create_tables
	queries = [ ("DROP TABLE IF EXISTS %s;", [ELFE_database_names[table_id]]) for table_id in ELFE_database_names]
	execute_queries(credentials, queries)
	create_tables(credentials)

def populate_params_with(params, key, value):
	if key not in params.keys():
		params[key] = value

def register_equipement_pilote(credentials, params) -> ELFE_EquipementPilote: 
	# not to use as a single function
	equipment = ELFE_EquipementPilote(0, params["spec_equip_id"], 0, 0, 0, 0, params["eq_name"], params["eq_description"], 0, False, 0)
	equipment.Id = fetch(credentials, equipment.get_append_in_table_str(ELFE_database_names["ELFE_EquipementPilote"]))[0][0]
	return equipment

def register_machine_cycle(credentials, params) -> ELFE_MachineGeneriqueCycle:
	populate_params_with(params, "duree_cycle", 3600)
	populate_params_with(params, "cy_name", "aucun")
	populate_params_with(params, "cy_description", f"cycle '{params['cy_name'] if params['cy_name'] != 'aucun' else 'default'}' for machine {params['machine_id']}'")
	cycle = ELFE_MachineGeneriqueCycle(0, params["machine_id"], params["duree_cycle"], params["cy_name"], params["cy_description"], 0)
	cycle.Id = fetch(credentials, cycle.get_append_in_table_str(ELFE_database_names["ELFE_MachineGeneriqueCycle"]))[0][0]
	return cycle

def register_machine(credentials, params) -> Tuple[ELFE_EquipementPilote, ELFE_MachineGenerique, ELFE_MachineGeneriqueCycle]:
	#registers a generic machin without a cycle for the time
	populate_params_with(params, "timestamp", 0)
	populate_params_with(params, "timestamp_delta", 3600)
	populate_params_with(params, "cycle", 0)
	populate_params_with(params,"power_id", 0)
	machine = ELFE_MachineGenerique(0, 0, params["timestamp"], params["timestamp_delta"], params["cycle"], params["power_id"])
	machine_id = fetch(credentials, machine.get_append_in_table_str(ELFE_database_names["ELFE_MachineGenerique"]))[0][0]
	machine.Id = machine_id
	populate_params_with(params, "eq_name", f"machine_{machine_id}")
	populate_params_with(params, "eq_description", f"equipement pilote pour la machine {machine_id}")
	params["spec_equip_id"] = machine_id
	equipment = register_equipement_pilote(credentials, params)
	machine.equipement_pilote_ou_mesure_id = equipment.Id
	params["machine_id"] = machine_id
	cycle = register_machine_cycle(credentials, params)
	machine.cycle_equipement_pilote_machine_generique_id = cycle.Id
	execute_queries(credentials, [machine.get_update_in_table_str(ELFE_database_names["ELFE_MachineGenerique"])])
	return (equipment, machine, cycle)

def register_drived_heater(credentials, params) -> Tuple[ELFE_EquipementPilote, ELFE_ChauffageAsservi]:
	populate_params_with(params, "temp_eco",                2901)
	populate_params_with(params, "temp_comfort",            2931)
	populate_params_with(params, "week_period_1_active",    False)
	populate_params_with(params, "week_period_1_start",     0)
	populate_params_with(params, "week_period_1_end",       0)
	populate_params_with(params, "week_period_2_active",    False)
	populate_params_with(params, "week_period_2_start",     0)
	populate_params_with(params, "week_period_2_end",       0)
	populate_params_with(params, "weekend_period_1_active", False)
	populate_params_with(params, "weekend_period_1_start",  0)
	populate_params_with(params, "weekend_period_1_end",    0)
	populate_params_with(params, "weekend_period_2_active", False)
	populate_params_with(params, "weekend_period_2_start",  0)
	populate_params_with(params, "weekend_period_2_end",    0)
	populate_params_with(params, "delta_temp",              40)
	populate_params_with(params, "power",                   2000)
	populate_params_with(params, "mth_id",                  1)
	populate_params_with(params, "power_id",                0)
	populate_params_with(params, "temp_sensor_id",          0)

	heater = ELFE_ChauffageAsservi(0, 0, params["temp_eco"], params["temp_comfort"], 
	params["week_period_1_active"], params["week_period_1_start"], params["week_period_1_end"],
	params["week_period_2_active"], params["week_period_2_start"], params["week_period_2_end"],
	params["weekend_period_1_active"], params["weekend_period_1_start"], params["weekend_period_1_end"],
	params["weekend_period_2_active"], params["weekend_period_2_start"], params["weekend_period_2_end"],
	params["delta_temp"], params["power"], params["mth_id"], params["power_id"], params["temp_sensor_id"])
	heater.Id = fetch(credentials, heater.get_append_in_table_str(ELFE_database_names["ELFE_ChauffageAsservi"]))[0][0]
	populate_params_with(params, "eq_name", f"drived_heater_{heater.Id}")
	populate_params_with(params, "eq_description", f"equipement pilote pour le chauffage asservi {heater.Id}")
	params["spec_equip_id"] = heater.Id
	equipment = register_equipement_pilote(credentials, params)
	heater.equipement_pilote_ou_mesure_id = equipment.Id
	execute_queries(credentials, [heater.get_update_in_table_str(ELFE_database_names["ELFE_ChauffageAsservi"])])
	print(heater)
	print("drived_heater_params:", ", ".join(list(params.keys())))
	return (equipment, heater)

def register_undrived_heater(credentials, params) -> Tuple[ELFE_EquipementPilote, ELFE_ChauffageNonAsservi]:
	populate_params_with(params, "week_period_1_active",    False)
	populate_params_with(params, "week_period_1_start",     0)
	populate_params_with(params, "week_period_1_end",       0)
	populate_params_with(params, "week_period_2_active",    False)
	populate_params_with(params, "week_period_2_start",     0)
	populate_params_with(params, "week_period_2_end",       0)
	populate_params_with(params, "weekend_period_1_active", False)
	populate_params_with(params, "weekend_period_1_start",  0)
	populate_params_with(params, "weekend_period_1_end",    0)
	populate_params_with(params, "weekend_period_2_active", False)
	populate_params_with(params, "weekend_period_2_start",  0)
	populate_params_with(params, "weekend_period_2_end",    0)
	populate_params_with(params, "average_eco_power",       100)
	populate_params_with(params, "average_comfort_power",   2000)
	populate_params_with(params, "forced_eco_pourc",        75)
	populate_params_with(params, "power_id",                0)
	
	heater = ELFE_ChauffageNonAsservi(0,0,
	params["week_period_1_active"], params["week_period_1_start"], params["week_period_1_end"],
	params["week_period_2_active"], params["week_period_2_start"], params["week_period_2_end"],
	params["weekend_period_1_active"], params["weekend_period_1_start"], params["weekend_period_1_end"],
	params["weekend_period_2_active"], params["weekend_period_2_start"], params["weekend_period_2_end"],
	params["average_eco_power"], params["average_comfort_power"], params["forced_eco_pourc"], params["power_id"]
	)
	heater.Id = fetch(credentials, heater.get_append_in_table_str(ELFE_database_names["ELFE_ChauffageNonAsservi"]))[0][0]
	params["spec_equip_id"] = heater.Id
	populate_params_with(params, "eq_name", f"undrived_heater_{heater.Id}")
	populate_params_with(params, "eq_description", f"equipement pilote pour le chauffage non-asservi {heater.Id}")
	equipment = register_equipement_pilote(credentials, params)
	heater.equipement_pilote_ou_mesure_id = equipment.Id
	execute_queries(credentials, [heater.get_update_in_table_str(ELFE_database_names["ELFE_ChauffageNonAsservi"])])
	print(heater)
	print("not_drived_heater_params:", ", ".join(list(params.keys())))
	return (equipment, heater)

def register_electric_vehicle(credentials, params) -> Tuple[ELFE_EquipementPilote, ELFE_VehiculeElectriqueGenerique]:
	populate_params_with(params, "charge_left"          , 0)
	populate_params_with(params, "expected_final_charge", 0)
	populate_params_with(params, "charge_duration"      , 0)
	populate_params_with(params, "usable_time"          , 0)
	populate_params_with(params, "power"                , 1000)
	populate_params_with(params, "capacity"             , 50_000)
	populate_params_with(params, "power_id"             , 0)
	
	electric_vehicle = ELFE_VehiculeElectriqueGenerique(0, 0, params["charge_left"], params["expected_final_charge"], params["charge_duration"], params["usable_time"], params["power"], params["capacity"], params["power_id"])
	electric_vehicle.Id = fetch(credentials, electric_vehicle.get_append_in_table_str(ELFE_database_names["ELFE_VehiculeElectriqueGenerique"]))[0][0]
	params["spec_equip_id"] = electric_vehicle.Id
	populate_params_with(params, "eq_name", f"electric_vehicle_{electric_vehicle.Id}")
	populate_params_with(params, "eq_description", f"equipement pilote pour le vehicule electrique {electric_vehicle.Id}")
	equipment = register_equipement_pilote(credentials, params)
	electric_vehicle.equipement_pilote_ou_mesure_id = equipment.Id
	execute_queries(credentials, [electric_vehicle.get_update_in_table_str(ELFE_database_names["ELFE_VehiculeElectriqueGenerique"])])
	print(electric_vehicle)
	print("electric_vehicle_params:", ", ".join(list(params.keys())))
	return (equipment, electric_vehicle)

def register_modele_thermique(credentials, params) -> ELFE_ChauffageAsserviModeleThermique:
	populate_params_with(params, "mth_description", f"EMS thermic model for '{params['mth_name']}'")
	thermic_model = ELFE_ChauffageAsserviModeleThermique(0, params['mth_name'], params['mth_description'])
	thermic_model.Id = fetch(credentials, thermic_model.get_append_in_table_str(ELFE_database_names["ELFE_ChauffageAsserviModeleThermique"]))[0][0]
	return thermic_model
	
def register_ballon_ECS_heures_creuses(credentials, params) -> ELFE_BallonECSHeuresCreuses:
	HCid = params["heures_creuses_id"]
	populate_params_with(params["heures_creuses"][HCid], "ECS_HC_nom", f"HC_{params['spec_equip_id']}_{HCid + 1}")
	populate_params_with(params["heures_creuses"][HCid], "ECS_HC_description", f"heure creuse numero {HCid + 1} pour le chauffe eau {params['spec_equip_id']}")
	populate_params_with(params["heures_creuses"][HCid], "ECS_HC_actif", False)
	heures_creuses = ELFE_BallonECSHeuresCreuses(0, params["spec_equip_id"], params["heures_creuses"][HCid]["ECS_HC_nom"], params["heures_creuses"][HCid]["ECS_HC_description"], params["heures_creuses"][HCid]["ECS_HC_actif"], params["heures_creuses"][HCid]["ECS_HC_start"], params["heures_creuses"][HCid]["ECS_HC_end"])	
	heures_creuses.Id = fetch(credentials, heures_creuses.get_append_in_table_str(ELFE_database_names["ELFE_BallonECSHeuresCreuses"]))[0][0]
	return heures_creuses

def register_ballon_ECS(credentials, params) -> Tuple[ELFE_EquipementPilote, ELFE_BallonECS, List[ELFE_BallonECSHeuresCreuses]]:
	populate_params_with(params, "ECS_volume", 200)
	populate_params_with(params, "ECS_power", 2000)
	ballon_ecs = ELFE_BallonECS(0, 0, params["ECS_volume"], params["ECS_power"], params["ECS_mesures"])
	ballon_ecs.Id = fetch(credentials, ballon_ecs.get_append_in_table_str(ELFE_database_names["ELFE_BallonECS"]))[0][0]
	params["spec_equip_id"] = ballon_ecs.Id
	populate_params_with(params, "eq_name", f"ballon_ecs_{ballon_ecs.Id}")
	populate_params_with(params, "eq_description", f"equipement pilote pour le ballon ecs {ballon_ecs.Id}")
	equipment = register_equipement_pilote(credentials, params)

	ballon_ecs.equipement_pilote_ou_mesure_id = equipment.Id
	execute_queries(credentials, [ballon_ecs.get_update_in_table_str(ELFE_database_names["ELFE_BallonECS"])])
	ballon_ecs_heures_creuses = []
	for i in range(len(params["heures_creuses"])):
		params["heures_creuses_id"] = i
		ballon_ecs_heure_creuse = register_ballon_ECS_heures_creuses(credentials, params)
		ballon_ecs_heures_creuses.append(ballon_ecs_heure_creuse)
	return (equipment, ballon_ecs, ballon_ecs_heures_creuses)

def make_study_case(credentials, csvPath: str) -> StudyCase:
	drop_and_recreate(credentials)
	to_return = StudyCase({}, {}, {}, {}, {}, {})
	with open(csvPath, "r") as inp:
		for line in inp:
			splitted_line = line.strip().replace(" ", "").split(",")
			object_type = splitted_line[0]
			if (object_type == "Machine"):
				new_machine = register_machine(credentials, {"power_id" : int(splitted_line[1])})
				to_return.machines[new_machine[1].Id] = new_machine
			elif (object_type == "Thermic_model"):
				new_thermic_model = register_modele_thermique(credentials, {"mth_name" : splitted_line[1]})
				to_return.thermic_models[new_thermic_model.Id] = new_thermic_model
			elif (object_type == "Drived_heater"):
				params = {
					"temp_eco" : int(splitted_line[1]),
					"temp_comfort" : int(splitted_line[2]),
					"delta_temp" : int(splitted_line[3]),
					"power" : int(splitted_line[4]),
					"mth_id" : int(splitted_line[5]),
					"power_id" : int(splitted_line[6]),
					"temp_sensor_id" : int(splitted_line[7]),
				}
				new_drived_heater = register_drived_heater(credentials, params)
				to_return.drived_heater[new_drived_heater[1].Id] = new_drived_heater
			elif (object_type == "ECS"):
				params = {
					"ECS_volume" : int(splitted_line[1]),
					"ECS_power" : int(splitted_line[2]),
					"ECS_mesures" : int(splitted_line[3]),# TODO_ELFE finish me
					"ECS_HC_count" : int(splitted_line[4]),
					"heures_creuses" : [],
				}
				splitted_offset = 4
				for i in range(params["ECS_HC_count"]):
					params_heure_creuses = {
						"ECS_HC_actif" : eval(splitted_line[splitted_offset + 1]),
						"ECS_HC_start" : int(splitted_line[splitted_offset + 2]),
						"ECS_HC_end" : int(splitted_line[splitted_offset + 3]),
					}
					splitted_offset += 3
					params["heures_creuses"].append(params_heure_creuses)
				new_ecs = register_ballon_ECS(credentials, params)
				to_return.ecs[new_ecs[1].Id] = new_ecs
	return to_return
