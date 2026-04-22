from database.EMS_db_types import EMSPowerCurveData
from database.query import execute_queries
from learning.zabbix_reader import ZabbixReader
from credentials.db_credentials import db_credentials
from credentials.zabbix_credentials import zabbix_credentials
from datetime import datetime
from learning.curve import get_full_curve_snapped
from predict.persistance import persistance_prediction
import matplotlib.pyplot as plt

CURVE_KEY        = "Equilibre General P=C bis"
CURVE_PERIOD     = 15 * 60
DAY_DURATION     = 24 * 60 * 60
CURVE_DATA_TABLE = "prediction"
zr = ZabbixReader(zabbix_credentials["url"], zabbix_credentials["token"])
zr.get_token()

items = zr.get_items()
item_id = items[CURVE_KEY]
current_timestamp = int(datetime.now().timestamp())
current_timestamp = round(current_timestamp/CURVE_PERIOD) * CURVE_PERIOD
data = zr.readData(item_id, current_timestamp - DAY_DURATION, current_timestamp)
base_timestamp = data["timestamps"][0] - (data["timestamps"][0] % CURVE_PERIOD)
curve = get_full_curve_snapped(data["timestamps"], data["values"], CURVE_PERIOD, current_timestamp - DAY_DURATION)
curve_base_timestamps = [base_timestamp + i * CURVE_PERIOD for i in range(len(curve))]

prediction = persistance_prediction(curve)

data_to_post_to_database = []
for i in range(len(prediction)):
	curve_data = EMSPowerCurveData(curve_base_timestamps[i] + DAY_DURATION, prediction[i])
	data_to_post_to_database.append(curve_data.get_create_or_update_in_table_str(CURVE_DATA_TABLE))

for i in range(len(prediction)):
	curve_data = EMSPowerCurveData(curve_base_timestamps[i] + 2 * DAY_DURATION, prediction[i])
	data_to_post_to_database.append(curve_data.get_create_or_update_in_table_str(CURVE_DATA_TABLE))
	
execute_queries(db_credentials["EMS"], data_to_post_to_database)
print(current_timestamp)