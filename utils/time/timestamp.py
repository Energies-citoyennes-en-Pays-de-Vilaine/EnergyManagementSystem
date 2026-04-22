from datetime import datetime
from config.config import get_config
from math import floor

def get_timestamp() -> int:
	return synchronise(datetime.now().timestamp())

def get_round_timestamp() -> int:
	return get_timestamp() + get_config().delta_time_simulation_s

def synchronise(timestamp: int, delta_s: int = 0) -> int:
	if delta_s == 0:
		delta_s = get_config().delta_time_simulation_s
	return floor(timestamp / delta_s) * delta_s