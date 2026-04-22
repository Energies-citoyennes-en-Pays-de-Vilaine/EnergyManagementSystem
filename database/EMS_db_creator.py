from credentials.db_credentials import db_credentials
from dataclasses import dataclass
import typing
from typing import Union
from database.query import execute_queries, fetch
from database.EMS_db_types import EMSMachineData, EMSCycle, EMSCycleData ,InitialWheatherForecast, HistoricalInitialWheatherForecast, EMSDeviceTemperatureData, EMSPowerCurveData, EMSResult, EMS_ECS, EMSResultEcs, EMS_Modele_Thermique
def create_tables(credentials):
	tables_queries = [
		EMSCycleData.get_create_table_str("cycledata"),
		["INSERT INTO cycledata(id_cycle_data, start_time, csv, duree, moved_timestamp) Values(%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING;", (0,0,"default.csv", 4, 0)],
		EMSCycle.get_create_table_str("cycle"),
		EMSMachineData.get_create_table_str("machine"),
		InitialWheatherForecast.get_create_table_str("initialweather"),
		HistoricalInitialWheatherForecast.get_create_table_str("historyinitialweather"),
		EMSDeviceTemperatureData.get_create_table_str("devicetemperaturedata"),
		EMSPowerCurveData.get_create_table_str("normal_solar_prevision"),
		EMSPowerCurveData.get_create_table_str("prevision_equilibre"),
		EMSResult.get_create_table_str("result"),
		EMSResultEcs.get_create_table_str("result_ecs"),
		EMS_ECS.get_create_table_str("ems_ecs"),
		EMS_Modele_Thermique.get_create_table_str("ems_modele_thermique")
	]
	execute_queries(credentials, tables_queries)


	#default values
	tables_queries = []
	bad_isolation_RTH  = 6 / ( 13_500_000 / (365 * 24))
	med_isolation_RTH  = 6 / ( 11_500_000 / (365 * 24))
	good_isolation_RTH = 6 / ( 9_350_000 / (365 * 24 ))

	bad_isolation_CTH =  12 * 60 * 60 * 13_500_000 / (365 * 24) / 20
	med_isolation_CTH =  12 * 60 * 60 * 11_500_000 / (365 * 24) / 20
	good_isolation_CTH = 12 * 60 * 60 * 9_350_000 / (365 * 24) / 20

	bad_isolation_mth  = EMS_Modele_Thermique(0, bad_isolation_RTH, bad_isolation_CTH)
	med_isolation_mth  = EMS_Modele_Thermique(1, med_isolation_RTH, med_isolation_CTH)
	good_isolation_mth = EMS_Modele_Thermique(2, good_isolation_RTH, good_isolation_CTH)
	tables_queries.append(bad_isolation_mth.get_create_or_update_in_table_str("ems_modele_thermique"))
	tables_queries.append(med_isolation_mth.get_create_or_update_in_table_str("ems_modele_thermique"))
	tables_queries.append(good_isolation_mth.get_create_or_update_in_table_str("ems_modele_thermique"))
	execute_queries(credentials, tables_queries)
if __name__ == '__main__':
	create_tables(db_credentials["EMS"])