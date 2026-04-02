from datetime import datetime
from config.config import Config, get_config

def get_timestamp() -> int:
	config = get_config()
	timestamp = round(datetime.now().timestamp() / config.delta_time_simulation_s) * config.delta_time_simulation_s
	return timestamp

def get_round_timestamp() -> int:
	config = get_config()
	timestamp = get_timestamp()
	return timestamp + config.delta_time_simulation_s