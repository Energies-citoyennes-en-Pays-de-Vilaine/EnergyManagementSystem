from datetime import datetime
from learning.zabbix_reader import ZabbixReader
import numpy as np
import matplotlib.pyplot as plt
from credentials.zabbix_credentials import zabbix_credentials

zr = ZabbixReader(zabbix_credentials["url"], zabbix_credentials["token"])
items = zr.get_items()
i = 0
for item in items:
	print(i, item, items[item])
	i = i +1
print(len(items))
#key = 9#42883#47#64#15
keyName = "Equilibre General P=C bis"
key=list(items.keys()).index(keyName)
print(list(items.keys())[key])
def average(data, period) :
	current_date = int(data["timestamps"][-1])
	current_count = 0
	current_sum = 0
	toReturn = {"timestamps" : [], "values" : []}
	for i in reversed(range(len(data["timestamps"]))):
		if (int(data["timestamps"][i]) > current_date + period):
			toReturn["timestamps"].append(int(current_date))
			toReturn["values"].append(current_sum / current_count)
			current_count = 0
			current_sum = 0
			current_date = int(data["timestamps"][i])
		current_sum += data["values"][i]
		current_count += 1
	if (current_count != 0):
		toReturn["timestamps"].append(current_date)
		toReturn["values"].append(current_sum / current_count)
	return toReturn

current_timestamp = int(datetime.now().timestamp())
data = zr.readData(items[list(items.keys())[key]], current_timestamp - 1*24*60*60, current_timestamp)
data2 = average(data, 15*60)
plt.plot([int(d) for d in data["timestamps"]], data["values"])
plt.plot(data2["timestamps"], np.array(data2["values"]))
plt.show()

"""for key in list(items.keys()):
	try:
		data = zr.readAllData(items[key])
		with open("data/" + key, "w") as outp:
			for i in reversed(range(len(data["timestamps"]))):
				print(data["timestamps"][i], data["values"][i], sep=" ", file=outp)
	except:
		continue"""