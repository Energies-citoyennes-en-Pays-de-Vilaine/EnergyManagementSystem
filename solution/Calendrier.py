from typing import List, Tuple, Dict
from datetime import date, time, timedelta, datetime

semaine = {"monday":0, "tuesday":1, "wednesday":2, "thursday":3, "friday":4, "saturday":5, "sunday":6}

class Jour:
	heures_creuses	: List[List[time, time]]
	weekday			: int

	def __init__(self, description_string: str, weekday: str):
		self.heures_creuses = []
		for periode in description_string.rstrip().split("- from ")[1:]:
			periode_courante = []
			for horaire in periode.rstrip().split(" to "):   
				periode_courante.append(time.strptime(horaire, '\"%H:%M:%S\"'))
			self.heures_creuses.append(periode_courante)
		self.weekday = semaine[weekday]
	
	def __str__(self):
		return repr(self) + ": " + str(self.heures_creuses)
	
	def __repr__(self):
		return ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"][self.weekday]
	
	# def get_periodes(self, date : date) -> List[Tuple[datetime, datetime]]: 
	# 	return [(datetime.combine(date, t[0]), datetime.combine(date, t[1]) + timedelta(seconds=1)) for t in self.heures_creuses]
	
	def is_heure_creuse(self, step: datetime) -> bool:
		return any(datetime.combine(step.date(), t[0]) <= step <= (datetime.combine(step.date(), t[1]) + timedelta(seconds=1)) for t in self.heures_creuses)

class Calendrier:
	user_id	: int
	jours	: Dict[int: Jour]

	def __init__(self, jours: List[Jour]):
		self.jours = {}
		for j in jours:
			self.jours[j.weekday] = j

	def __str__(self):
		return " ".join(str(j) for j in self.jours.values())
	
	def is_heure_creuse(self, step: datetime) -> bool:
		return (step.weekday() in self.jours.keys()) and self.jours[step.weekday()].is_heure_creuse(step)
	
if __name__ == "__main__":
	jours = []
	# jours.append(Jour(' - from "12:00:00" to "14:00:00" - from "22:00:00" to "23:59:59"', "monday"))
	# jours.append(Jour(' - from "12:00:00" to "14:00:00" - from "22:00:00" to "23:59:59"', "tuesday"))
	# jours.append(Jour(' - from "12:00:00" to "14:00:00" - from "22:00:00" to "23:59:59"', "wednesday"))
	# jours.append(Jour(' - from "12:00:00" to "14:00:00" - from "22:00:00" to "23:59:59"', "thursday"))
	# jours.append(Jour(' - from "12:00:00" to "14:00:00" - from "22:00:00" to "23:59:59"', "friday"))
	# jours.append(Jour('- from "00:00:00" to "23:59:59"', "saturday"))
	# jours.append(Jour('- from "00:00:00" to "23:59:59"', "sunday"))

	c = Calendrier(jours)
	# print(c)

	print(c.is_heure_creuse(datetime.combine(date=datetime.now().date(), time=time(hour=23, minute=59, second=59))))