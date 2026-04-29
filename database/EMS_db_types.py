from dataclasses import dataclass
from typing import Union, List
from database.annotations import PrimaryAutoInt, DBAnnotation, serializableThroughDatabase, create_DB_Annotation

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class EMSMachineData():
	Id_machine      : PrimaryAutoInt
	Id_machine_elfe : int
	threshold_begin : int
	threshold_end   : int
	period          : int
	period_count    : int
	Id_type         : int

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class EMSCycle():
	Id_cycle      : PrimaryAutoInt
	Id_machine    : int
	Id_cycle_data : int
	name          : str

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class EMSCycleData():
	Id_cycle_data   : PrimaryAutoInt
	start_time      : int
	csv             : str
	duree           : int
	moved_timestamp : int


@serializableThroughDatabase
@dataclass(init=True, repr=True)
class InitialWheatherForecast():
	wheather_timestamp : Union[int, create_DB_Annotation(is_primary=True)]
	temperature        : int
	wind_speed         : int
	gust_speed         : int
	wind_direction     : int
	sun_hours          : Union[int, create_DB_Annotation(is_nullable=True), None] = None
	def get_clone_at_timestamp(self, timestamp : int):
		return InitialWheatherForecast(timestamp, self.temperature, self.wind_speed, self.gust_speed, self.wind_direction, self.sun_hours)

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class HistoricalInitialWheatherForecast():
	Id_forecast_data   : PrimaryAutoInt
	forecast_timestamp : int
	wheather_timestamp : int
	temperature        : int
	wind_speed         : int
	gust_speed         : int
	wind_direction     : int
	sun_hours          : Union[int, create_DB_Annotation(is_nullable=True), None] = None

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class EMSDeviceTemperatureData():
	Id_elfe                    : Union[int, create_DB_Annotation(is_primary=True)]
	data_timestamp             : int
	temperature                : int 

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class EMSPowerCurveData():
	data_timestamp             : Union[int, create_DB_Annotation(is_primary=True)]
	power                      : int

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class EMSNormalPowerCurveData():
	data_timestamp             : Union[int, create_DB_Annotation(is_primary=True)]
	power                      : float

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class EMSEnergyWeather():
	data_timestamp        		: Union[int, create_DB_Annotation(is_primary=True)]
	power          				: float
	cohorte						: int

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class EMSResult():
	Id                        : PrimaryAutoInt
	first_valid_timestamp     : int
	machine_id                : int
	result_type               : int
	machine_type              : int
	decisions                 : Union[int, create_DB_Annotation(is_db_list=True, db_element_count=96), List[int]]

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class EMSResultEcs():
	Id                        : PrimaryAutoInt
	first_valid_timestamp     : int
	machine_id                : int
	result_type               : int
	machine_type              : int
	duration                  : int
	decisions                 : Union[int, create_DB_Annotation(is_db_list=True, db_element_count=96), List[int]]

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class EMS_ECS():
	elfe_zabbix_id : Union[int, create_DB_Annotation(is_primary=True)]# carefull this is the zabbix ID
	last_energy    : int#last day's consumption, will be acquired through ECS_acquisition every day

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class EMS_Modele_Thermique():
	Id : PrimaryAutoInt
	R_th : float
	C_th : int