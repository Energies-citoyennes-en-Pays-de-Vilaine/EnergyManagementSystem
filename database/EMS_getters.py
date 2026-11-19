from typing import List
from dataclasses import dataclass
from psycopg2 import sql
from database.query import fetch
from typing import Dict, Tuple
from database.EMS_db_types import EMS_database_names
from datetime import datetime, timedelta
from credentials.db_credentials import db_credentials

def get_equipment_started_last_round(db_credentials: Dict[str: str], timestamp: int, table_name: str) -> List[int]:
	query_formatted = sql.SQL("SELECT machine_id FROM {} WHERE first_valid_timestamp=%s AND decisions_0=1").format(sql.Identifier(table_name))
	result = fetch(db_credentials, (query_formatted, [timestamp]))
	return [int(i[0]) for i in result]

@dataclass
class previous_ECS_decision:
	first_valid_timestamp : int
	machine_id : int
	result_type : int
	machine_type : int
	decisions : List[int]

def get_previous_ECS_decisions(timestamp: int, step_size: int) -> List[previous_ECS_decision]:
	query_formatted = sql.SQL("SELECT * from result_ecs AS ecs WHERE first_valid_timestamp>=%s AND decisions_0=1")
	result = fetch(db_credentials["EMS"], (query_formatted, [timestamp - 24*3600]))
	#id first_valid_timestamp machine_id result_type machine_type duration decision_[0...191]
	to_return = []
	for r in result:
		start = r[1]
		duration_steps = r[5]
		if start + duration_steps * step_size >= timestamp:
			offset = (timestamp - start) // step_size
			to_return.append(previous_ECS_decision(start, r[2], r[3], r[4], r[6+offset: 6+duration_steps]))
	return to_return

def get_heater_launches(credentials: Dict[str: str], timestamp: int) -> Dict[int, List[int]]:
	start_timestamp = (datetime.fromtimestamp(timestamp) - timedelta(days=1)).timestamp()
	query_formatted = (sql.SQL("""	SELECT first_valid_timestamp, result.machine_id,
						   			FROM {0} AS result
						   			WHERE first_valid_timestamp>=%s
						   			AND machine_type=%s
						   			AND decisions_0=1""").format(
							   sql.Identifier(EMS_database_names['EMS_Result']),
							   ),
							   [start_timestamp, 151])
	result = fetch(credentials, query_formatted)
	to_return = {}
	if result != None:
		for timestamp, id in result:
			if int(id) not in to_return.keys():
				to_return[int(id)] = [int(timestamp)]
			else:
				to_return[int(id)].append(int(timestamp))
	return to_return

def get_cycle_filename_for_machine(credentials: Dict[str: str], cycle_name: str, zabbix_id: int) -> str:
	print(zabbix_id)
	csv_cycle = fetch(credentials, (f" SELECT cd.csv FROM machine AS m"
									+f" INNER JOIN cycle AS c ON c.id_machine = m.id_machine"
									+f" INNER JOIN cycledata AS cd ON cd.id_cycle_data = c.id_cycle_data "
									+f" WHERE m.id_machine_elfe=%s AND c.name=%s",
									[zabbix_id, cycle_name]))
	try: 
		csv_cycle = csv_cycle[0]
	except IndexError:
		csv_cycle = "default.csv"
		print("not found in database", zabbix_id)
	return csv_cycle

def get_last_consumption(credentials: Dict[str: str], zabbix_id : int) -> int:
	last_consumption_result = fetch(credentials, ("SELECT last_energy FROM ems_ecs WHERE elfe_zabbix_id=%s", [zabbix_id]))
	last_consumption = 0
	try:
		last_consumption = last_consumption_result[0][0]
	except KeyError:
		print("no last consumption known for consumer with id (key)", zabbix_id)
	except IndexError:
		print("no last consumption known for consumer with id (index)", zabbix_id)
	return last_consumption

if __name__ == "__main__":
	print("\n".join(map(str, get_previous_ECS_decisions(int(datetime.now().timestamp() // 900) * 900, 900))))
	print("\n".join(map(str, get_previous_ECS_decisions(900 + int(datetime.now().timestamp() // 900) * 900, 900))))
	print("\n".join(map(str, get_previous_ECS_decisions(1800 + int(datetime.now().timestamp() // 900) * 900, 900))))
