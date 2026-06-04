from utils.time.timestamp import get_round_timestamp
from learning.zabbix_reader import ZabbixReader
from credentials.zabbix_credentials import zabbix_credentials
from database.EMS_db_types import EMSNormalPowerCurveData
from credentials.db_credentials import db_credentials
from database.query import execute_queries, fetch
from database.ELFE_db_types import ELFE_database_names
import sys
from psycopg2 import sql

def get_zabbix_previsions(zabbix_key: str, table_name: str, time_from: int) -> None:
    """
    Copie les données de Zabbix dans la table *table_name* du schema public de l'EMS

    :param zabbix_key: Clé Zabbix des données temporelles
    :type zabbix_key: str
    :param table_name: Nom de la table de l'EMS à remplir
    :type table_name: str
    """
    zr = ZabbixReader(zabbix_credentials["url"], zabbix_credentials["token"])
    data = zr.readDataKey(key = zabbix_key, time_from = time_from)
    data_to_post_to_database = [EMSNormalPowerCurveData(t, v).get_create_or_update_in_table_str(table_name) for t, v in zip(data["timestamps"], data["values"])]
    execute_queries(db_credentials["EMS"], data_to_post_to_database)

def get_zabbix_previsions_show(zabbix_key: str, time_from: int) -> None:
    zr = ZabbixReader(zabbix_credentials["url"], zabbix_credentials["token"])
    data = zr.readDataKey(key = zabbix_key, time_from = time_from)
    print(data)

def get_zabbix_key_by_cohorte(cohorte_id: str) -> str:
    query = (sql.SQL("""SELECT cu.prevision_id
				  		FROM {0} AS cu
				  		WHERE cu.id = %s"""
				  ).format(
					  sql.Identifier(ELFE_database_names['ELFE_Cohorte']),
				  ),
				  [cohorte_id])
    result = fetch(db_credentials["ELFE"], query)
    return result[0][0]

if __name__ == "__main__":
    # cohorte_id = sys.argv[1]
    equilibre_key = get_zabbix_key_by_cohorte(sys.argv[1])
    get_zabbix_previsions(equilibre_key, "prevision_equilibre", get_round_timestamp())
    get_zabbix_previsions("Prevision_Prod_Enda_PV_normale", "normal_solar_prevision", get_round_timestamp())
    # get_zabbix_previsions_show(equilibre_key, get_round_timestamp())
