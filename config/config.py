from dataclasses import dataclass

@dataclass(init= True, repr=True)
class Config():
	delta_time_simulation_s       : int
	day_step_count                : int
	day_count					  : int
	max_time_to_solve_s           : int
	heater_eco_sliding_percentage : int
	heater_eco_sliding_period_s   : int
	heater_forced_eco_active      : bool
	log_problem_settings_active   : bool
	log_problem_settings_path     : str

def get_config() -> Config:
	return Config(
		delta_time_simulation_s       = 60 * 15, #15 minutes
		day_step_count                = 96, #number of steps for a day at 15mins/steps
		day_count					  = 1,
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