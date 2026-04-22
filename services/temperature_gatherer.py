from learning.zabbix_reader import ZabbixReader
from database.EMS_db_types import EMSDeviceTemperatureData
from database.query import execute_queries
from credentials.zabbix_credentials import zabbix_credentials
from credentials.db_credentials import db_credentials
CENTI_CELSIUS_TO_CENTI_KELVIN = 27315
TEMPERATURE_TABLE = "devicetemperaturedata"
zr = ZabbixReader(zabbix_credentials["url"], zabbix_credentials["token"])
zr.get_token()
items = zr.get_items()
filtered_items = {}
for key in items:
	try:
		key = key.replace("_", " ")
		if key.split(" ")[1] == "temp":
			filtered_items[key] = items[key]
	except IndexError as err:
		print (err, key)

items_ids = [filtered_items[key] for key in filtered_items]

data = zr.get_last_data_for_items(items_ids)
temperatures_to_post = []
for item in data:
	if (int(item["last_timestamp"]) != 0):
		temperatures_to_post.append(EMSDeviceTemperatureData(int(item["itemid"]), int(item["last_timestamp"]), int(float(item["last_value"]) * 100 + CENTI_CELSIUS_TO_CENTI_KELVIN)))
queries = []
for temperature in temperatures_to_post:
	queries.append(temperature.get_create_or_update_in_table_str(TEMPERATURE_TABLE))
execute_queries(db_credentials["EMS"], queries)