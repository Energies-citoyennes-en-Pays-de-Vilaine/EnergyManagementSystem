from typing import List, Tuple, Dict
from datetime import date, time, timedelta, datetime
from utils.time.timestamp import synchronise
from numpy import round
from config.config import get_config

semaine = {"monday":0, "tuesday":1, "wednesday":2, "thursday":3, "friday":4, "saturday":5, "sunday":6}
DAY_LENGTH = 86400 #secondes par jour
step_size = get_config().delta_time_simulation_s

class Jour:
	periodes	: List[List[time, time]]
	weekday		: int

	def __init__(self, description_string: str, weekday: str):
		self.periodes = []
		for periode in description_string.rstrip().split("- from ")[1:]:
			periode_courante = []
			for horaire in periode.rstrip().split(" to "):   
				periode_courante.append(time.strptime(horaire, '\"%H:%M:%S\"'))
			self.periodes.append(periode_courante)
		self.weekday = semaine[weekday]
	
	def __str__(self):
		return repr(self) + ": " + str(self.periodes)
	
	def __repr__(self):
		return ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"][self.weekday]
		
	def is_heure_creuse(self, step: datetime) -> bool:
		return any(datetime.combine(step.date(), t[0]) <= step <= (datetime.combine(step.date(), t[1]) - timedelta(seconds=1)) for t in self.periodes)
	
	def count_steps(self, start_timestamp: int, end_timestamp: int) -> int:
		jour = datetime.fromtimestamp(start_timestamp).date()
		debut = datetime.fromtimestamp(start_timestamp)
		fin = datetime.fromtimestamp(end_timestamp)
		
		durees = [min(datetime.combine(jour, t[1]), fin) - max(datetime.combine(jour, t[0]), debut) for t in self.periodes]
		periods = [max(0, int(round(duree / timedelta(seconds=step_size), 0))) for duree in durees] #round (up) / int (down) ?
		to_return = sum(periods)
		return to_return
	
	def get_periods(self, start_timestamp: int, end_timestamp: int) -> List[Tuple[int, int]]:
		jour = datetime.fromtimestamp(start_timestamp).date()
		debut = datetime.fromtimestamp(start_timestamp)
		fin = datetime.fromtimestamp(end_timestamp)
		# print(jour, debut, fin)
		to_return = [(max(datetime.combine(jour, t[0]), debut), min(datetime.combine(jour, t[1]) - timedelta(seconds=1), fin)) for t in self.periodes if datetime.combine(jour, t[1]) - timedelta(seconds=1) >= debut and datetime.combine(jour, t[0]) <= fin]
		# print(to_return)
		to_return_timestamps = list(map(lambda x: (synchronise(int(x[0].timestamp())), synchronise(int(x[1].timestamp())) ), to_return))
		# print(f"d:{to_return}\nt:{to_return_timestamps}")
		
		return to_return_timestamps
	

class Calendrier:
	user_id	: int
	jours	: Dict[int: Jour]

	def __init__(self, jours: List[Jour]):
		self.jours = {}
		for j in jours:
			self.jours[j.weekday] = j

	def __str__(self):
		return " ".join(str(j) for j in self.jours.values())
	
	def is_in_calendar(self, step: datetime) -> bool:
		return (step.weekday() in self.jours.keys()) and self.jours[step.weekday()].is_heure_creuse(step)

	def is_in_calendar_timestamp(self, step: int) -> bool:
		return self.is_in_calendar(datetime.fromtimestamp(step))		


class Calendrier_confort(Calendrier):
	def __init__(self, jours: List[Jour]):
		super().__init__(jours)
		self.is_confort_timestamp = self.is_in_calendar_timestamp

	def get_past_confort_hours(self, timestamp: int) -> int:
		timestamps = [timestamp - DAY_LENGTH, int(datetime.combine(datetime.fromtimestamp(timestamp).date(), time(0, 0, 0)).timestamp()), timestamp]
		return self._get_confort_hours(timestamps)
	
	def get_futur_confort_hours(self, timestamp: int) -> int:
		midnight_timestamp = int(datetime.combine(datetime.fromtimestamp(timestamp).date(), time(0, 0, 0)).timestamp())
		timestamps = [timestamp, midnight_timestamp + DAY_LENGTH, midnight_timestamp + 2 * DAY_LENGTH, timestamp + 2 * DAY_LENGTH]
		if timestamps[-1] == timestamps[-2]:
			timestamps = timestamps[:-1]
		return self._get_confort_hours(timestamps)
	
	def _get_confort_hours(self, timestamps: List[int]) -> int:
		weekday_from_timestamp = lambda timestamp: datetime.fromtimestamp(timestamp).weekday()
		bornes = [weekday_from_timestamp(timestamps[0]), weekday_from_timestamp(timestamps[-1])] 
		if bornes[1] < bornes[0]:
			bornes[1] += 7
		jours : List[Jour] = [self.jours[d % 7] for d in range(bornes[0], bornes[1] + 1)]
		horaires : List[int] = [jour.count_steps(start_timestamp, end_timestamp - 1) for jour, start_timestamp, end_timestamp in zip(jours, timestamps[:-1], timestamps[1:])]
		to_return = sum(horaires)
		return to_return
	
	def get_confort_periods(self, timestamp: int) -> List[List[int]]:
		midnight_timestamp = int(datetime.combine(datetime.fromtimestamp(timestamp).date(), time(0, 0, 0)).timestamp())
		timestamps = [midnight_timestamp - DAY_LENGTH, midnight_timestamp, midnight_timestamp + DAY_LENGTH, midnight_timestamp + 2 * DAY_LENGTH, timestamp + 3 * DAY_LENGTH]
		begin_timestamp, end_timestamp = timestamp - step_size * 2, timestamp + DAY_LENGTH * 2
		timestamps = [begin_timestamp] + [t for t in timestamps if begin_timestamp < t < end_timestamp] + [end_timestamp]
		# print(timestamps)

		weekday_from_timestamp = lambda weekday_timestamp: datetime.fromtimestamp(weekday_timestamp).weekday()
		bornes = [weekday_from_timestamp(timestamps[0]), weekday_from_timestamp(timestamps[-1])]
		if bornes[1] < bornes[0]:
			bornes[1] += 7
		jours : List[Jour] = [self.jours[d % 7] for d in range(bornes[0], bornes[1] + 1)]
		periodes : List[Tuple[int, int]] = []
		for jour, start_timestamp, stop_timestamp in zip(jours, timestamps[:-1], timestamps[1:]):
			list_period = jour.get_periods(start_timestamp, stop_timestamp - 1)
			# print(f" {jour.weekday}_{start_timestamp}-{end_timestamp}\n {list_period}")
			periodes.extend(list_period)
		#Fusion de periodes adjacentes
		nb_periodes = len(periodes)
		counter = 0
		while counter < nb_periodes - 1:
			if periodes[counter + 1][0] - periodes[counter][1] <= step_size:
				periodes[counter] = (periodes[counter][0], periodes[counter + 1][1])
				periodes.pop(counter + 1)
				nb_periodes -= 1
			else:
				counter += 1
		to_return = [[t for t in range(p[0], p[1]+1, step_size)] for p in periodes]
		return to_return

class Calendrier_HPHC(Calendrier):
	def __init__(self, jours):
		super().__init__(jours)
		self.is_heure_creuse = self.is_in_calendar

if __name__ == "__main__":
	jours = []
	jours.append(Jour(' - from "12:00:00" to "14:00:00" - from "22:00:00" to "23:59:59"', "monday"))
	jours.append(Jour(' - from "12:00:00" to "14:00:00" - from "22:00:00" to "23:59:59"', "tuesday"))
	jours.append(Jour(' - from "12:00:00" to "14:00:00" - from "15:00:00" to "15:30:00" - from "22:00:00" to "23:59:59"', "wednesday"))
	jours.append(Jour(' - from "12:00:00" to "14:00:00" - from "15:00:00" to "15:29:59"- from "22:00:00" to "23:59:59"', "thursday"))
	jours.append(Jour(' - from "12:00:00" to "14:00:00" - from "22:00:00" to "23:59:59"', "friday"))
	jours.append(Jour('- from "00:00:00" to "23:59:59"', "saturday"))
	jours.append(Jour('- from "00:00:00" to "23:59:59"', "sunday"))

	# c = Calendrier(jours)
	c = Calendrier_confort(jours)
	# print(c)
	# now_periods = c.get_confort_periods(synchronise(int(datetime.now().timestamp())))
	# print(list(map(to_timestamp, now_periods)))
	start = datetime(2026, 11, 4, 14, 0, 0)
	# start = datetime(2026, 11, 4, 16, 0, 0)
	# start = datetime(2026, 11, 5, 16, 0, 0)
	for i in range(synchronise(start.timestamp()), synchronise((start + timedelta(days=1)).timestamp()+1), 900):
		a=c.get_confort_periods(i)
	# WE_periods = c.get_confort_periods(int(datetime.combine(date(day=31, month=10, year=2026), time(0,0,0)).timestamp()))
	# print(list(map(lambda x: (datetime.fromtimestamp(x[0]), datetime.fromtimestamp(x[1])), WE_periods)))
	
	# print(c.is_heure_creuse(datetime.combine(date=datetime.now().date(), time=time(hour=14, minute=00, second=00))))