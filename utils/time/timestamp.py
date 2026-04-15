from datetime import datetime
from config.config import get_config
from math import floor

def get_timestamp() -> int:
	timestamp = synchronise(datetime.now().timestamp())
	return timestamp

def get_round_timestamp() -> int:
	config = get_config()
	return get_timestamp() + config.delta_time_simulation_s

def synchronise(timestamp: int):
	config = get_config()
	return floor(timestamp / config.delta_time_simulation_s) * config.delta_time_simulation_s