import numpy as np
from typing import List
import matplotlib.pyplot as plt
from typing import Union
class Curve():
	delta_T          : int # delta time int seconds
	points           : np.ndarray
	origin_points    : np.ndarray
	origin_timestamp : np.ndarray
	timestamp        : int

	def __init__(self, delta_T: int, points:np.ndarray, origin_points: List[np.ndarray], origin_timestamp: List[np.ndarray], timestamp : int) -> None:
		self.delta_T = delta_T
		self.points = np.array(points, dtype=np.float64)
		self.origin_points = origin_points
		self.origin_timestamp = origin_timestamp
		self.timestamp = timestamp

	def cut_last_points(self, count):
		origin_points = []
		origin_timestamps = []
		for i in range(len(self.origin_points)):
			if (self.origin_timestamp[i] >= self.timestamp and self.origin_timestamp[i] <  self.timestamp + (len(self.points) - count + 1) * self.delta_T):
				origin_points.append(self.origin_points[i])
				origin_timestamps.append(self.origin_timestamp[i])
		return Curve(self.delta_T, np.array(self.points[:-count]), np.array(origin_points), np.array(origin_timestamps), self.timestamp)
	
	def plot_curve(self, fig : plt.figure, full=False):
		if fig == None:
			fig = plt
		timestamps = []
		values = []
		for i in range(len(self.points)):
			timestamps.append(self.timestamp + i * self.delta_T)
			timestamps.append(self.timestamp + (i + 1) * self.delta_T)
			values.append(self.points[i])
			values.append(self.points[i])
		fig.plot(timestamps, values)
		if full is True:
			fig.plot(self.origin_timestamp, self.origin_points)
			
def get_full_curve(times: List[int], data: List[int], period : int, base_index : int):
	#we assume the list is ordered by time ascending
	current_list = []
	current_time_list = []
	current_curve = []
	if base_index >= len(times):
		return None
	base_time = times[base_index]
	for i in range(base_index, len(times)):
		if int((times[i] - base_time) / period) > len(current_curve):
			toAdd = 0.0
			toAddDelta = 0.0
			for j in range(len(current_list) - 1):
				toAdd += current_list[j] * (current_time_list[j + 1] - current_time_list[j])
				toAddDelta += (current_time_list[j + 1] - current_time_list[j])
			if (toAddDelta != 0):
				toAdd /= toAddDelta
				current_curve.append(toAdd)
			current_list = []
			current_time_list = []
		current_list.append(data[i])
		current_time_list.append(times[i])
	if (len(current_list) != 0):
		toAdd = 0.0
		toAddDelta = 0.0
		for j in range(len(current_list) - 1):
			toAdd += current_list[j] * (current_time_list[j + 1] - current_time_list[j])
			toAddDelta += current_time_list[j + 1] - current_time_list[j]
		if toAddDelta != 0:
			toAdd /= toAddDelta
			current_curve.append(toAdd)
	return np.array(current_curve, dtype = np.float64)

def get_full_curve_snapped(times: List[int], data: List[int], period : int, base_time : int):
	#we assume the list is ordered by time ascending
	last_known_value = data[0]
	values = []
	i = 0
	while(times[i] < base_time):
		i += 1
		last_known_value = data[i]
	next_period = base_time + period
	last_time = base_time
	current_value = 0
	while (i < len(times)):
		if (times[i] < next_period):
			current_value += last_known_value * (times[i] - last_time)
			last_known_value = data[i]
			last_time = times[i]
		else:
			current_value += last_known_value * (next_period - last_time)
			values.append(current_value / period)
			last_time = next_period
			next_period += period
			current_value = last_known_value * (times[i] - last_time)
			last_known_value = data[i]
			last_time = times[i]
		i += 1
	return np.array(values)
	
def get_curve_starting_at(index, times : List[int], data : List[float], threshold_end : float, period: int, required_low_period_count : int = 0) -> Union[Curve, None] : 
	curve = get_full_curve(times, data, period, index)
	if curve is None:
		return None
	count_period = 0
	for i in range(len(curve)):
		if curve[i] < threshold_end:
			count_period += 1
		else:
			count_period = 0
		if (count_period > required_low_period_count):
			return Curve(period, curve[:i], data[index:], times[index:], times[index])
	return None

def fetch_past_time(times, time, index) -> Union[int, None]:
	for i in range(index, len(times)):
		if (times[i] > time):
			return i
	return None
	

def make_curves(times : List[int], data: List[float], threshold_begin : float, threshold_end : float, period: int, required_low_period_count : int = 0) -> List[Curve]:
	i = 0
	toReturn = []
	start_time = []
	initialCurve = get_curve_starting_at(0, times, data, threshold_end, period, required_low_period_count)
	if initialCurve == None:
		return []
	i = fetch_past_time(times, times[0] + period * len(initialCurve.points), 0)
	if i == None:
		return []
	while (i < len(times)):
		if data[i] > threshold_begin:
			curve = get_curve_starting_at(i, times, data, threshold_end, period, required_low_period_count)
			if curve != None:
				if required_low_period_count != 0:
					toReturn.append(curve.cut_last_points(required_low_period_count))
				else: 
					toReturn.append(curve)
				i = fetch_past_time(times, times[i] + period * len(curve.points), i)
			else:
				i = i + 1
			if i == None:
				return toReturn
		else:
			i = i + 1

	return toReturn