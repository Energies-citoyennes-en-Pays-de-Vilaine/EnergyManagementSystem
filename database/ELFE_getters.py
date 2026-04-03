from typing import List, Dict, Union
from psycopg2 import sql
from dataclasses import dataclass
from database.query import fetch
from database.ELFE_db_types import ELFE_ChauffageNonAsservi, ELFE_database_names
MODE_PILOTE = 30

@dataclass
class MachineToScheduleType():
	Id             : int
	cycle_name     : str
	zabbix_id      : int
	end_timestamp  : int
	max_delay      : int
	utilisateur	   : str
	equipment_type : int

def get_machines_to_schedule(credentials: Dict[str: str], cohorte_id: str) -> List[MachineToScheduleType]:
	query = (sql.SQL("""SELECT machine.equipement_pilote_ou_mesure_id, cycle.nom, machine.mesures_puissance_elec_id, machine.timestamp_de_fin_souhaite, machine.delai_attente_maximale_apres_fin, epm.equipement_pilote_ou_mesure_type_id
						FROM {0} AS machine
						INNER JOIN {1} AS cycle ON cycle.id = machine.cycle_equipement_pilote_machine_generique_id 
						INNER JOIN {2} AS epm ON machine.equipement_pilote_ou_mesure_id = epm.id
				  		INNER JOIN {3} AS usr ON epm.utilisateur = usr.id
						WHERE epm.equipement_pilote_ou_mesure_mode_id = %s
				  		AND usr.cohorte = %s""").format(
				sql.Identifier(ELFE_database_names['ELFE_MachineGenerique']),
    			sql.Identifier(ELFE_database_names['ELFE_MachineGeneriqueCycle']),
				sql.Identifier(ELFE_database_names['ELFE_EquipementPilote']),
				sql.Identifier(ELFE_database_names['ELFE_Utilisateur'])
			),  [MODE_PILOTE, cohorte_id])
	result = fetch(credentials, query)
	result_typed : List[MachineToScheduleType] = [MachineToScheduleType(r[0], r[1], r[2], r[3], r[4], r[5]) for r in result]
	result_typed : List[MachineToScheduleType] = [MachineToScheduleType(*r[0:6]) for r in result]

	print("[debug info machine]", result_typed)
	return result_typed

@dataclass
class ECSToScheduleType():
	Id             	: int
	zabbix_id      	: int
	volume_L       	: str
	power_W        	: int
	start          	: int
	end            	: int
	utilisateur		: str
	equipment_type	: int

def get_ECS_to_schedule(credentials: Dict[str: str], timestamp: int, cohorte_id: str, ECS_not_to_schedule: Union[List[int], None] = None) -> List[ECSToScheduleType]:
	query = (sql.SQL("""SELECT epm.id, ecs.mesures_puissance_elec_id ,ecs.volume_ballon, ecs.puissance_chauffe, hc.debut, hc.fin, epm.equipement_pilote_ou_mesure_type_id
						FROM {0} AS epm
	    				INNER JOIN {1} AS ecs ON epm.id=ecs.equipement_pilote_ou_mesure_id 
						INNER JOIN {2} AS hc ON ecs.id = hc.equipement_pilote_ballon_ecs_id
				  		INNER JOIN {3} AS usr ON usr.id = epm.utilisateur
						WHERE hc.actif=true and epm.equipement_pilote_ou_mesure_mode_id=%s
				  		AND epm.timestamp_derniere_mise_en_marche + 12 * 3600 <= %s
				  		AND usr.cohorte = %s""").format(
				sql.Identifier(ELFE_database_names['ELFE_EquipementPilote']),
				sql.Identifier(ELFE_database_names['ELFE_BallonECS']),
				sql.Identifier(ELFE_database_names['ELFE_BallonECSHeuresCreuses']),
				sql.Identifier(ELFE_database_names['ELFE_Utilisateur'])
			), 
			[MODE_PILOTE, timestamp, cohorte_id])
	result = fetch(credentials, query)
	result_typed : List[ECSToScheduleType] = [ECSToScheduleType(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) for r in result]
	
	#gets only the biggest period where it can be scheduled
	biggest_period_ecs : Dict[int, ECSToScheduleType] = {}
	for ecs in result_typed:
		if ECS_not_to_schedule != None and ecs.Id in ECS_not_to_schedule:
			continue
		if ecs.Id not in biggest_period_ecs:
			biggest_period_ecs[ecs.Id] = ecs
		elif (ecs.end - ecs.start > biggest_period_ecs[ecs.Id].end - biggest_period_ecs[ecs.Id].start):
			biggest_period_ecs[ecs.Id] = ecs
	print("[debug info ECS]", biggest_period_ecs)
	return biggest_period_ecs

@dataclass
class ElectricVehicleToScheduleType:
	Id 							: int
	current_charge_left_percent : int
	target_charge_percent       : int
	end_timestamp               : int
	power_W                     : int
	capa_WH                     : int
	utilisateur					: str
	equipement_type             : int

def get_electric_vehicle_to_schedule(credentials: Dict[str: str], cohorte_id: str, vehicle_not_to_schedule : Union[List[int], None] = None) -> List[ElectricVehicleToScheduleType]:
	query = (sql.SQL("""SELECT ve.equipement_pilote_ou_mesure_id, ve.pourcentage_charge_restant, ve.pourcentage_charge_finale_minimale_souhaitee,
	    				ve.timestamp_dispo_souhaitee, ve.puissance_de_charge, ve.capacite_de_batterie, usr.id, epm.equipement_pilote_ou_mesure_type_id
						FROM {1} AS ve
						INNER JOIN {0} AS epm ON ve.equipement_pilote_ou_mesure_id = epm.id
	 			  		INNER JOIN {2} AS usr ON usr.id = epm.utilisateur			  
						WHERE epm.equipement_pilote_ou_mesure_mode_id = %s
				  		AND usr.cohorte = %s""").format(
			sql.Identifier(ELFE_database_names['ELFE_EquipementPilote']),
			sql.Identifier(ELFE_database_names['ELFE_VehiculeElectriqueGenerique']),
	 		sql.Identifier(ELFE_database_names['ELFE_Utilisateur'])
		),
		[MODE_PILOTE, cohorte_id]
	)
	result = fetch(credentials, query)
	if result == None:
		print("error, returning empty list for electric vehicle to prevent crash")
		return []
	result_typed : List[ElectricVehicleToScheduleType] = []
	for r in result:
		if vehicle_not_to_schedule == None or int(r[0]) not in vehicle_not_to_schedule:
			result_typed.append(ElectricVehicleToScheduleType(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]))
	print("[debug info Electric vehicle]", result_typed)
	return result_typed

def get_elfe_not_piloted_heater(credentials: Dict[str: str], cohorte_id: str) -> List[ELFE_ChauffageNonAsservi]:
	#not piloted means that we have no temperature sensor here
	query = (sql.SQL("""SELECT heater.*, epm.equipement_pilote_ou_mesure_type_id 
						FROM {0} AS heater
						INNER JOIN {1} AS epm ON epm.id = heater.equipement_pilote_ou_mesure_id
				  		INNER JOIN {2} AS usr ON usr.id = epm.utilisateur
						WHERE epm.equipement_pilote_ou_mesure_mode_id = %s
				  		AND usr.cohorte = %s""").format(
			sql.Identifier(ELFE_database_names['ELFE_ChauffageNonAsservi']),
			sql.Identifier(ELFE_database_names['ELFE_EquipementPilote']),
			sql.Identifier(ELFE_database_names['ELFE_Utilisateur'])
		),
		[MODE_PILOTE, cohorte_id])
	result = fetch(credentials, query)
	to_return : List[ELFE_ChauffageNonAsservi] = []
	if (result == None):
		print("an error occured in ELFE_Chauffage_non_asservi, sending back empty array not to block")
		return []
	for r in result:
		new_elem = ELFE_ChauffageNonAsservi.create_from_select_output(r[:-1])
		new_elem.equipement_type = r[-1]
		to_return.append(new_elem)
	print("[debug info chauffage non asservi]", to_return)
	return to_return

@dataclass
class SolarPVInputType:
	Id 					: int
	puissance_crete_W	: int
	orientation      	: int
	utilisateur			: str
	equipement_type		: int

def get_elfe_solar_pv(credentials: Dict[str: str], cohorte_id: str) -> List[SolarPVInputType]:
	query = (sql.SQL("""SELECT pv.id, pv.puissance_installee, pv.orientation, epm.utilisateur, epm.equipement_pilote_ou_mesure_type_id 
				  		FROM {0} AS pv
				  		INNER JOIN {1} AS epm ON epm.id = pv.equipement_pilote_ou_mesure_id
				  		INNER JOIN {2} AS usr ON usr.id = epm.utilisateur
				  		WHERE usr.cohorte = %s
				  		AND epm.utilisateur IN (
				  			SELECT DISTINCT usr.id
							FROM {2} AS usr
							INNER JOIN {1} AS epm ON usr.id = epm.utilisateur
							WHERE epm.equipement_pilote_ou_mesure_mode_id = 30
							AND usr.cohorte = %s)"""
				  ).format(
					  sql.Identifier(ELFE_database_names['ELFE_PanneauxPhotovoltaiques']),
					  sql.Identifier(ELFE_database_names['ELFE_EquipementPilote']),
					  sql.Identifier(ELFE_database_names['ELFE_Utilisateur']),
				  ),
				  [cohorte_id, cohorte_id])
	result = fetch(credentials, query)
	if (result == None):
		print("an error occured in SolarPVInput, sending back empty array not to block")
		return []
	to_return=[(SolarPVInputType(*r)) for r in result]
	print("[debug info panneaux PV]", to_return)
	return to_return

@dataclass
class utilisateurType:
	Id 	: str

def get_elfe_utilisateurs(credentials: Dict[str: str], cohorte_id: str) -> List[utilisateurType]:
	query = (sql.SQL("""SELECT DISTINCT usr.id
				  		FROM {0} AS usr
						INNER JOIN {1} AS epm ON usr.id = epm.utilisateur
						WHERE epm.equipement_pilote_ou_mesure_mode_id = %s
				  		AND usr.cohorte = %s""").format(
		sql.Identifier(ELFE_database_names['ELFE_Utilisateur']),
		sql.Identifier(ELFE_database_names['ELFE_EquipementPilote']),
		),
		[MODE_PILOTE, cohorte_id])
	result = fetch(credentials, query)
	if (result == None):
		print("an error occured in SolarPVInput, sending back empty array not to block")
		return []
	to_return=[(utilisateurType(r[0])) for r in result]
	print("[debug info utilisateur]", to_return)
	return to_return

# def get_condition_utilisateur_statement(base: int, cohorte_id: str):
# 	return (f"""IN (SELECT DISTINCT usr.id
# 		 			FROM {{{base + 0}}} AS usr
# 					INNER JOIN {{{base + 1}}} AS epm ON usr.id = epm.utilisateur
# 					WHERE epm.equipement_pilote_ou_mesure_mode_id = 30
# 					AND usr.cohorte = {{{base + 2}}})""",
# 		[		
# 		sql.Identifier(ELFE_database_names['ELFE_Utilisateur']),
# 		sql.Identifier(ELFE_database_names['ELFE_EquipementPilote']),
# 		cohorte_id
# 	])

if __name__ == "__main__":
	print("ELFE_getters")