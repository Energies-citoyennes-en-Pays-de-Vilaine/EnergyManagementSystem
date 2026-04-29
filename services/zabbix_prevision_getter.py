from utils.time.timestamp import get_round_timestamp
from learning.zabbix_reader import ZabbixReader
from credentials.zabbix_credentials import zabbix_credentials
from database.EMS_db_types import EMSNormalPowerCurveData
from credentials.db_credentials import db_credentials
from database.query import execute_queries

def get_zabbix_previsions(zabbix_key: str, table_name: str) -> None:
    """
    Copie les données de Zabbix dans la table *table_name* du schema public de l'EMS

    :param zabbix_key: Clé Zabbix des données temporelles
    :type zabbix_key: str
    :param table_name: Nom de la table de l'EMS à remplir
    :type table_name: str
    """
    zr = ZabbixReader(zabbix_credentials["url"], zabbix_credentials["token"])
    data = zr.readDataKey(key = zabbix_key, time_from = get_round_timestamp())
    data_to_post_to_database = [EMSNormalPowerCurveData(t, v).get_create_or_update_in_table_str(table_name) for t, v in zip(data["timestamps"], data["values"])]
    execute_queries(db_credentials["EMS"], data_to_post_to_database)

def get_zabbix_previsions_show(zabbix_key: str) -> None:
    zr = ZabbixReader(zabbix_credentials["url"], zabbix_credentials["token"])
    data = zr.readDataKey(key = zabbix_key, time_from = get_round_timestamp())
    print(data)

get_zabbix_previsions("Prevision_equilibre", "prevision_equilibre")
get_zabbix_previsions("Prevision_Prod_Enda_BGW_normale", "normal_solar_prevision")
# get_zabbix_previsions_show("Prevision_Prod_Enda_BGW_normale")
