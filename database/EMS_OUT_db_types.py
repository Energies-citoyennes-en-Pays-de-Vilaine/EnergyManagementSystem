from dataclasses import dataclass
from typing import Union, List
from database.annotations import PrimaryAutoInt, DBAnnotation, serializableThroughDatabase, create_DB_Annotation
@serializableThroughDatabase
@dataclass(init=True, repr=True)
class EMSRunInfo():
	timestamp                : PrimaryAutoInt
	run_time_ms              : int
	consumer_count           : int
	conso_min_hour_timestamp : int
	conso_min_hour           : int
	conso_max_hour_timestamp : int
	conso_max_hour           : int
	cohorte					 : str
    
