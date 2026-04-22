
from credentials.db_credentials import db_credentials
from dataclasses import dataclass
import typing
from typing import Union, Dict
from database.query import execute_queries, fetch
from database.EMS_db_types import  EMSResult, EMSPowerCurveData, EMSEnergyWeather
from database.EMS_OUT_db_types import EMSRunInfo
def create_tables(credentials: Dict[str: str]) -> None:
	schema = credentials["schema"] if "schema" in credentials.keys() else ""		
	tables_queries = [
		EMSResult.get_create_table_str("result", schema),
		EMSEnergyWeather.get_create_table_str("p_c_with_flexible_consumption", schema),
		EMSRunInfo.get_create_table_str("ems_run_info", schema)
	]
	if schema != "":
		tables_queries = [
			(f" CREATE SCHEMA {schema};"),
			(f" ALTER SCHEMA {schema} OWNER TO {credentials["user"]}"),
			# (f" USE SCHEMA {credentials["database"]}.{schema};")
			] + tables_queries
	# print(tables_queries)
	execute_queries(credentials, tables_queries)

			
if __name__ == '__main__':
	create_tables(db_credentials["EMS_SORTIE"])