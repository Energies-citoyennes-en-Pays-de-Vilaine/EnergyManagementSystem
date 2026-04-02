from typing import List
from dataclasses import dataclass
from psycopg2 import sql
from database.query import fetch
from typing import Dict

def get_equipment_started_last_round(db_credentials: Dict[str: str], timestamp: int, table_name: str) -> List[int]:
	query_formatted = sql.SQL("SELECT machine_id FROM {} WHERE first_valid_timestamp=%s AND decisions_0=1").format(sql.Identifier(table_name))
	result = fetch(db_credentials, (query_formatted, [timestamp]))
	return [int(i[0]) for i in result]


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

def get_consumer_activation_ratio_starting_at(credentials, consumer_id, first_valid_timestamp):
	pass