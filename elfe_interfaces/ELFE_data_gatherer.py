from database.ELFE_db_types import ELFE_BallonECS, ELFE_BallonECSHeuresCreuses, ELFE_ChauffageAsservi, ELFE_ChauffageAsserviModeleThermique, ELFE_ChauffageNonAsservi, ELFE_EquipementPilote, ELFE_MachineGenerique, ELFE_MachineGeneriqueCycle, ELFE_VehiculeElectriqueGenerique
from database.ELFE_db_types import ELFE_database_names
from database.EMS_db_types import EMSCycle, EMSCycleData, EMSDeviceTemperatureData, EMSMachineData, EMSPowerCurveData, InitialWheatherForecast, EMS_Modele_Thermique
from database.query import execute_queries, fetch
from database.EMS_getters import *
from database.ELFE_getters import *
from credentials.db_credentials import db_credentials
from typing import List, Tuple, Dict
from solution.ConsumerTypes.HeaterConsumer import HeaterConsumer
from solution.ConsumerTypes.SumConsumer import SumConsumer, SumPeriod
from solution.ConsumerTypes.MachineConsumer import MachineConsumer
from solution.ConsumerTypes.ECSConsumer import ECSConsumer
from solution.ConsumerTypes.VehicleConsumer import VehicleConsumer
from solution.Utilisateur import Utilisateur
from solution.Calculation_Params import CalculationParams
from solution.ProducerTypes.SolarProducer import SolarProducer
from utils.time.period import Period, get_merged_periods
from utils.time.midnight import get_midnight_date
from utils.time.timestamp import get_timestamp, get_round_timestamp
from math import ceil
from datetime import datetime
import numpy as np
from config.config import Config, get_config
from operator import itemgetter

config : Config = get_config()
MODE_PILOTE = 30
DAY_TIME_SECONDS = 24 * 60 * 60
DELTA_SIMULATION = config.delta_time_simulation_s
COHORTE_ID = 'ACI_1'

def get_machines(timestamp) -> List[MachineConsumer]:
	to_return : List[MachineConsumer]= []
	machines_not_to_schedule = get_equipment_started_last_round(db_credentials["EMS"], timestamp, "result")
	machines_to_schedule : List[MachineToScheduleType] = get_machines_to_schedule(db_credentials["ELFE"])
	for machine in machines_to_schedule:
		if machine.Id in machines_not_to_schedule:
			print(f"not to schedule {machine.Id}")
			continue
		cycle_filename = get_cycle_filename_for_machine(db_credentials["EMS"], f"default_cycle_for_machine({machine.zabbix_id}", machine.zabbix_id)
	
		cycle_data = []
		with open(f"data/in_use/{cycle_filename}") as inp:
			for line in inp:
				for data in line.strip().replace(" ", "").split(","):
					cycle_data.append(float(data))
		cycle_duration = DELTA_SIMULATION * len(cycle_data)
		end_time = max( DELTA_SIMULATION + cycle_duration + timestamp, machine.end_timestamp)
		start_time = machine.end_timestamp - machine.max_delay - cycle_duration
		machine_consumer = MachineConsumer(id=machine.Id, profile = cycle_data, start_time = start_time, end_time = end_time, machine_count = 1, consumer_machine_type = machine.equipment_type)
		machine_consumer.consumer_machine_type = machine.equipment_type
		to_return.append(machine_consumer)
	return to_return
 
def get_ECS(timestamp: int, calculation_params: CalculationParams) -> List[ECSConsumer]:
	#ECS means "Eau Chaude Sanitaire" which is the hot water tank
	midnight = get_midnight_date(timestamp)
	midnight_timestamp = midnight.timestamp()
	ECS_not_to_schedule = get_equipment_started_last_round(db_credentials["EMS"], timestamp, "result_ecs")
	ecs_to_schedule = get_ECS_to_schedule(db_credentials["ELFE"],timestamp ,ECS_not_to_schedule)
	
	ecs_consumers = []
	for ecs_id in ecs_to_schedule:
		ecs : ECSToScheduleType = ecs_to_schedule[ecs_id]
		last_consumption = get_last_consumption(db_credentials["EMS"], ecs.zabbix_id) 
		duration_hour = last_consumption / ecs.power_W + 2 #add two hours to be safe, to be put in a config file
		# calculation_params.step_size
		duration_step = ceil(duration_hour * 4) #WARNING, quick and dirty, couples the code to 15min simulation step. To be reworked
		ecs_curve = []
		for i in range(duration_step):
			ecs_curve.append(ecs.power_W)
		possible_starts = [
			midnight_timestamp + ecs.start - 24 * 3600,
			midnight_timestamp + ecs.start,
			midnight_timestamp + ecs.start + 24 * 3600,
		]
		possible_ends = [
			midnight_timestamp + ecs.end - 24 * 3600,
			midnight_timestamp + ecs.end,
			midnight_timestamp + ecs.end + 24 * 3600
		]
		consumer : ECSConsumer
		if (timestamp <= possible_starts[0] or timestamp > possible_starts[0] and timestamp < possible_ends[0]):
			consumer = ECSConsumer(ecs.Id, ecs_curve, possible_starts[0], possible_ends[0], ecs.power_W, ecs.volume_L, ecs.equipment_type)
		elif (timestamp <= possible_starts[1] or (timestamp > possible_starts[1] and timestamp < possible_ends[1])): 
			consumer = ECSConsumer(ecs.Id, ecs_curve, possible_starts[1], possible_ends[1], ecs.power_W, ecs.volume_L, ecs.equipment_type)
		else:
			consumer = ECSConsumer(ecs.Id, ecs_curve, possible_starts[2], possible_ends[2], ecs.power_W, ecs.volume_L, ecs.equipment_type)
		ecs_consumers.append(consumer)
	return (ecs_consumers)

def get_electric_vehicle(calculationParams: CalculationParams, cohorte_id: str) -> Dict[str: VehicleConsumer]:
	vehicle_not_to_schedule = get_equipment_started_last_round(db_credentials["EMS"], calculationParams.begin - calculationParams.step_size, "result")
	vehicle_to_schedule = get_electric_vehicle_to_schedule(db_credentials["ELFE"], cohorte_id, calculationParams.begin, vehicle_not_to_schedule)
	vehicles : Dict[VehicleConsumer] = {}
	for v in vehicle_to_schedule:
		vehicle_consumer : VehicleConsumer = VehicleConsumer(v.Id, v.power_W, v.capa_WH, v.current_charge_left_percent, v.target_charge_percent, calculationParams.begin, v.end_timestamp, v.equipement_type)
		vehicles[v.utilisateur] = vehicle_consumer
	return vehicles

def get_sum_consumer(timestamp : int, calculationParams: CalculationParams) -> List[SumConsumer]:
	"""
	Sum consumers currently are only made of heaters on which we don't have access to the room's heat
	"""
	elfe_heater : List[ELFE_ChauffageNonAsservi] = get_elfe_not_piloted_heater(db_credentials["ELFE"])
	starting_periods : List[datetime] = [get_midnight_date(timestamp - DAY_TIME_SECONDS), get_midnight_date(timestamp), get_midnight_date(timestamp + DAY_TIME_SECONDS)]
	sum_consumers : List[SumConsumer] = []
	for heater in elfe_heater:
		periods : List[Period] = []
		for start in starting_periods:
			periods += heater.get_periods(start)
		for p in periods:
			p.snap_to(calculationParams.time_delta) #snaps period to the current time delta
		periods = get_merged_periods(periods)
		periods = list(filter(lambda x : (x - timestamp).end > 0, periods))
		periods = sorted(periods, key=lambda x : x.start)
		if len(periods) == 0:
			print(f"no periods to schedule for heater {heater.equipement_pilote_ou_mesure_id}")
			continue
		first_period : Period = periods[0].deep_copy()
		first_period_cutted : Period = first_period.deep_copy()
		first_period_cutted.cut(calculationParams.begin, calculationParams.end)
		for p in periods:
			p.cut(calculationParams.begin , calculationParams.end)
		period_filtered : List[Period] = list(filter(lambda x : x.end - x.start > 0, periods))
		if len(period_filtered) == 0:
			print(f"no periods left to schedule for heater {heater.equipement_pilote_ou_mesure_id} after cutting on the simulation params")
			continue
		count : int = 0
		summ : int = 0
		if (first_period_cutted in period_filtered):
			heater_history_query = ("SELECT COUNT(*) as c, SUM(decisions_0) as s FROM result WHERE\
			   first_valid_timestamp > %s AND machine_id = %s GROUP BY machine_id",
			   [first_period.start, heater.equipement_pilote_ou_mesure_id]
			   )
			heater_history_result = fetch(db_credentials["EMS"], heater_history_query)
			try:
				count = heater_history_result[0][0]
				summ  = heater_history_result[0][1]
			except IndexError as e:
				count = 0
				summ = 0
		sum_periods : List[SumPeriod] = []
		for p in period_filtered:
			expected_ratio : int = (100.0 - heater.pourcentage_eco_force) / 100.0
			expected_sum : int =  round( expected_ratio * (count + (p.end - p .start) / calculationParams.step_size))
			expected_sum_left : int = expected_sum - summ
			steps_left : int = round((p.end - p .start) / calculationParams.step_size)
			if (expected_sum_left > steps_left):
				print(f"something went wrong with heater {heater.equipement_pilote_ou_mesure_id} period({p}), reducing expected sum left")
				print(f"ratio {expected_ratio} end {p.end} start {p.start} sum {expected_sum}, left {expected_sum_left}, steps {steps_left}")
				expected_sum_left = steps_left
			sliding_period_steps : int = round(config.heater_eco_sliding_period_s / calculationParams.step_size)
			sliding_period_count : int = steps_left // sliding_period_steps
			sliding_period_consumption_denied : int = ceil(sliding_period_steps * config.heater_eco_sliding_percentage / 100.0)
			sliding_period_min : int = max(0, sliding_period_steps - sliding_period_consumption_denied)
			sliding_period_max : int = sliding_period_steps
			for i in range(sliding_period_count):
				start_time : int = i * calculationParams.step_size
				sum_period : SumPeriod = SumPeriod(p.start + start_time, p.start + start_time + sliding_period_steps * calculationParams.step_size, sliding_period_min, sliding_period_max)
				sum_periods.append(sum_period)
			
			sum_periods.append(SumPeriod(p.start, p.end, expected_sum_left, steps_left))
			count = 0
			summ = 0
		sum_consumer : SumConsumer = SumConsumer(heater.equipement_pilote_ou_mesure_id, heater.puissance_moyenne_eco, heater.puissance_moyenne_confort, sum_periods, heater.equipement_type)
		sum_consumers.append(sum_consumer)
	return sum_consumers

def get_temperature_forecast(timestamp_start : int, timestamp_end : int, timestamp_list : List[int]) -> np.ndarray:
	temperature_query = sql.SQL("SELECT wheather_timestamp, temperature FROM initialweather WHERE wheather_timestamp >= %s AND wheather_timestamp <= %s ORDER BY wheather_timestamp ASC", timestamp_start, timestamp_end)
	temperature_list : List[Tuple[int, int]]= fetch(db_credentials["EMS"], temperature_query)
	forecast : List[int] = []
	for t in timestamp_list:
		current_temperature = 283 # 10 C, default value if no forecast is availible
		distance = 0
		real_point = False
		for timestamp, temperature in temperature_list:
			if real_point == False:
				real_point = True
				current_temperature = temperature
				distance = abs(timestamp - t)
				continue
			if (abs(timestamp - t) < distance):
				current_temperature = temperature
				distance = abs(timestamp - t)
				if (distance == 0):
					break
		forecast.append(current_temperature)
	return forecast

def get_heater_consumer(timestamp : int, calculationParams: CalculationParams) -> List[HeaterConsumer]:
	elfe_heater_query = f"SELECT heater.*, epm.id, epm.equipement_pilote_ou_mesure_type_id \
		FROM {ELFE_database_names['ELFE_ChauffageAsservi']} AS heater\
		INNER JOIN {ELFE_database_names['ELFE_EquipementPilote']} AS epm ON epm.id = heater.equipement_pilote_ou_mesure_id\
		WHERE epm.equipement_pilote_ou_mesure_mode_id = {MODE_PILOTE}"	
	elfe_heater_result = fetch(db_credentials["ELFE"], elfe_heater_query)
	elfe_heater : List[ELFE_ChauffageAsservi] = [ELFE_ChauffageAsservi.create_from_select_output(result[:-2]) for result in elfe_heater_result]
	print("[debug heater]", elfe_heater)
	starting_periods : List[datetime] = [get_midnight_date(timestamp - DAY_TIME_SECONDS), get_midnight_date(timestamp), get_midnight_date(timestamp + DAY_TIME_SECONDS)]
	heater_consumers : List[SumConsumer] = []
	for heater_id in range(len(elfe_heater)):
		heater = elfe_heater[heater_id]
		periods : List[Period] = []
		for start in starting_periods:
			periods += heater.get_periods(start)
		for p in periods:
			p.snap_to(calculationParams.time_delta) #snaps period to the current time delta
			p.cut(calculationParams.begin, calculationParams.end)
		periods = list(filter(lambda x : x.end - x.start > 0, periods))
		periods = list(filter(lambda x : x.end > calculationParams.begin , periods))
		periods = list(filter(lambda x : x.start < calculationParams.end , periods))
		simulation_timestamps : List[int] = calculationParams.get_time_array()
		in_periods : List[bool]  = [False for i in simulation_timestamps]
		target_temperature_low : List[float] = [0.0 for i in simulation_timestamps]
		target_temperature_high : List[float] = [0.0 for i in simulation_timestamps]
		t_low_eco      : int = (heater.temperature_eco - heater.delta_temp_maximale_temp_demandee) / 10 # data is in deciKelvin in the database
		t_high_eco     : int = (heater.temperature_eco + heater.delta_temp_maximale_temp_demandee) / 10 # data is in deciKelvin in the database
		t_low_comfort  : int = (heater.temperature_confort - heater.delta_temp_maximale_temp_demandee) / 10 # data is in deciKelvin in the database
		t_high_comfort : int = (heater.temperature_confort + heater.delta_temp_maximale_temp_demandee) / 10 # data is in deciKelvin in the database
		for i, simulation_timestamp in enumerate(simulation_timestamps):#there might be an optimisation possible
			for p in periods:
				if simulation_timestamp >= p.start and simulation_timestamp < p.end:
					in_periods[i] = True
		for i, in_period in enumerate(in_periods):
			target_temperature_low[i]  = t_low_eco
			target_temperature_high[i] = t_high_eco
			if (in_period):
				target_temperature_low[i]  = t_low_comfort
				target_temperature_high[i] = t_high_comfort
		t_init = 0.0
		initial_state = False
		m_th_query = fetch(db_credentials["EMS"], ("SELECT * FROM ems_modele_thermique where id=%s", [heater.modele_thermique_id]))
		m_th : EMS_Modele_Thermique = EMS_Modele_Thermique.create_from_select_output(m_th_query[0]) 
		T_ext_response = fetch(db_credentials["EMS"], ("SELECT wheather_timestamp, temperature FROM initialweather WHERE wheather_timestamp >= %s ORDER BY wheather_timestamp ASC",[get_round_timestamp()]))
		t_ex = [T_ext_response[0][1],T_ext_response[0][1]] + [T_ext_response[i][1] for i in range(len(calculationParams.get_time_array()))]
		T_ext = np.array(t_ex)
		heater_consumer : HeaterConsumer = HeaterConsumer(heater.equipement_pilote_ou_mesure_id, t_init, initial_state, T_ext, target_temperature_low, target_temperature_high, m_th.R_th, m_th.C_th, heater.puissance, elfe_heater_result[heater_id][-1])
		heater_consumers.append(heater_consumer)
	return heater_consumers

def get_panneaux_photovoltaiques(cohorte_id: str) -> Dict[str: SolarProducer]:
	panneaux = get_elfe_solar_pv(db_credentials["ELFE"], cohorte_id)
	to_return: Dict[str, SolarProducer] = {}
	for p in panneaux:
		current = SolarProducer(id=p.Id, puissance_crete_W=p.puissance_crete_W, orientation=p.orientation)
		to_return[p.utilisateur] = current
	return to_return

def get_utilisateurs(timestamp: int, calculationsParams: CalculationParams, cohorte_id: str = COHORTE_ID) -> List[Utilisateur]:
	utilisateurs = get_elfe_utilisateurs(db_credentials["ELFE"], cohorte_id)
	to_return : Dict[str, Utilisateur] = {u.Id: Utilisateur(u.Id) for u in utilisateurs}
	
	vehicules_electriques = get_electric_vehicle(calculationsParams, cohorte_id)
	for u, v in vehicules_electriques.items():
		to_return[u].add_consumer(v)
	
	panneaux_photovoltaiques = get_panneaux_photovoltaiques(cohorte_id)
	for u, p in panneaux_photovoltaiques.items():
		to_return[u].add_producer(p)

	to_return = {i: u for i, u in to_return.items() if not u.is_consumer_empty()}
	return list(to_return.values())

def get_cohorte_balance() -> List[Tuple[int, float]]:
	config = get_config()
	round_start_timestamp = get_round_timestamp()
	expected_power = fetch(db_credentials["EMS"], ("SELECT * FROM prevision_equilibre WHERE data_timestamp >= %s ;", [round_start_timestamp]))
	expected_power = sorted(expected_power, key=itemgetter(0))
	items_to_add = max(0, config.day_step_count - len(expected_power))
	list_to_add = [(round_start_timestamp + (len(expected_power) + i) * config.delta_time_simulation_s, 0) for i in range(items_to_add)]
	expected_power = expected_power + list_to_add
	cohorte_balance = expected_power[:config.day_step_count]
	return cohorte_balance

def get_production_solaire() -> Dict[int, float]:
	config = get_config()
	round_start_timestamp = get_round_timestamp()
	expected_solar_power = fetch(db_credentials["EMS"], ("SELECT * FROM normal_solar_prevision WHERE data_timestamp >= %s ;", [round_start_timestamp]))
	expected_solar_power = sorted(expected_solar_power, key=itemgetter(0))
	normal_solar_prediction = {round_start_timestamp + i * config.delta_time_simulation_s: 0 for i in range(config.day_step_count)}
	for solar_power_entry in expected_solar_power[:get_config().day_step_count]:
		normal_solar_prediction.update({solar_power_entry[0]:solar_power_entry[1]})
	return normal_solar_prediction

def get_calculation_params(simulation_datas = None) -> CalculationParams:
	timestamp = get_timestamp()
	round_start_timestamp = get_round_timestamp()
	if (simulation_datas == None):
		simulation_datas = get_cohorte_balance()
	sim_params = CalculationParams(
		round_start_timestamp,
		timestamp + config.day_count * config.day_step_count * config.delta_time_simulation_s,
		config.delta_time_simulation_s,
		config.delta_time_simulation_s,
		[[-int(simulation_datas[i][1]) for i in range(config.day_step_count)]]
	)
	return sim_params

if __name__ == "__main__":
	# from datetime import datetime
	# print(get_machines(int(datetime.now().timestamp())))

	# print(get_panneaux_photovoltaiques(COHORTE_ID))
	# print(get_electric_vehicle(get_timestamp(), COHORTE_ID))
	print("pv: ", get_production_solaire())
	print("ch: ", get_cohorte_balance())