from dataclasses import dataclass

@dataclass(init= True, repr=True)
class Config():
	delta_time_simulation_s       : int
	step_count					  : int
	max_time_to_solve_s           : int
	heater_eco_sliding_percentage : int
	heater_eco_sliding_period_s   : int
	heater_forced_eco_active      : bool
	log_problem_settings_active   : bool
	log_problem_settings_path     : str

	def __init__(self, delta_time_simulation_s, day_count_d, max_time_to_solve_s, heater_eco_sliding_percentage, heater_eco_sliding_period_s, heater_forced_eco_active, log_problem_settings_active, log_problem_settings_path):
		self.delta_time_simulation_s 		= delta_time_simulation_s
		self.step_count 					= day_count_d * (24 * 3600) // self.delta_time_simulation_s
		self.max_time_to_solve_s 			= max_time_to_solve_s
		self.heater_eco_sliding_percentage	= heater_eco_sliding_percentage
		self.heater_eco_sliding_period_s	= heater_eco_sliding_period_s
		self.heater_forced_eco_active 		= heater_forced_eco_active
		self.log_problem_settings_active	= log_problem_settings_active
		self.log_problem_settings_path 		= log_problem_settings_path

def get_config() -> Config:
	return Config(
		day_count_d					  = 2,
		delta_time_simulation_s       = 60 * 15, #15 minutes
		max_time_to_solve_s           = 60 * 10, #ten minutes to solve, 5 minutes for the interactions with the database
		heater_eco_sliding_percentage = 25,
		heater_eco_sliding_period_s   = 60 * 60,
		heater_forced_eco_active      = True,
		log_problem_settings_active   = True,
		log_problem_settings_path     = "data/run_conditions"
	)

@dataclass(init=True, repr=True)
class MachineLearnerConfig():
	default_thresh_begin    : int = 40
	default_thresh_end      : int = 40
	default_period          : int = 15*60
	default_period_count    : int = 1
	delta_time_acquisition  : int = 3 * 24 * 60 * 60
	machine_table_name      : str = "machine"
	machine_cycle_name      : str = "cycle"
	machine_cycle_data_name : str = "cycledata"