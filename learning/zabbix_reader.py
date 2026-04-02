import requests
from datetime import datetime, timedelta
import json
import numpy as np
import re
import matplotlib.pyplot as plt
from zabbix_utils import ZabbixAPI, Getter
from typing import Dict, List

class ZabbixReader():
	api : ZabbixAPI

	def __init__(self, url: str, token: str) -> None:
		self.api = ZabbixAPI(url = url, token = token)

	def get_items_full(self):
		data = self.api.item.get(output = ["itemids", "name"])
		items = {}
		for d in data:
			items[d["name"]] = int(d["itemid"])
		return items
	
	def get_items(self):
		data = self.api.item.get(output = ["itemids", "name"])
		items = {}
		for d in data:
			if (re.search("[ADF]{1}\\d{1,3}", d["name"][:4]) != None or re.search("Equi", d["name"][:4]) != None ):
				items[d["name"]] = int(d["itemid"])
		return items
	
	def get_unit(self, itemId: int) -> str:
		data = self.api.item.get(output = ["units"], itemids = itemId)
		return data[0]["units"]
	
	def get_items_by_tag(self, tag: str):
		data = self.api.item.get(output = ["itemid", "name"], tags = [{"tag" : "appareil", "value": tag}])
		items = {d["name"]: d["itemid"] for d in data}
		return items
	
	def get_last_data_for_items(self, items: List[int]):
		data = self.api.item.get(output = ["itemids", "name", "lastvalue", "lastclock"], itemids = items)
		to_return = []
		for item in data:
			to_return.append({
				"name": item["name"],
				"itemid" : int(item["itemid"]),
				"last_value" : float(item["lastvalue"]),
				"last_timestamp" : int(item["lastclock"]),
			})
		return to_return
	
	def readData(self, clientID: int , time_from: int, time_till: int) -> Dict[str, List[int]]:
		data = self.api.history.get(itemids = clientID,
							  		history = 0,
									time_from = time_from, 
									time_till = time_till,
									sortfield = "clock",
									sortorder = "ASC")
		toReturn = { 
			"timestamps"  : [],
			"values"      : []
			}
		for d in data:
			toReturn["timestamps"].append(int(d["clock"]))
			toReturn["values"].append(float(d["value"]))
		return toReturn
	
	def readAllData(self, clientID: int) -> Dict[str, List[int]]:		
		data = self.api.history.get(itemids = clientID,
							history = 0,
							sortfield = "clock",
							sortorder = "DESC",
							limit = 100000)
		toReturn = { 
			"timestamps"  : [],
			"values"      : []
			}
		for d in data:
			toReturn["timestamps"].append(int(d["clock"]))
			toReturn["values"].append(float(d["value"]))
		return toReturn
	
if __name__ == "__main__":
	z = ZabbixReader("192.168.30.100", "0770ce62ae3ee2be453c153b42fe702690b796d3f3106994eb0fccba06474aef")
	# print(z.get_items_full())
	# print(z.get_items())
	# print(z.get_unit(42918))
	# print(z.get_items_by_tag("ECS"))
	# print(z.get_last_data_for_items([42918]))
	# print(z.readData(42918, int(datetime.now().timestamp()), int((datetime.now() + timedelta(2)).timestamp())))
	# print(z.readAllData(42918))