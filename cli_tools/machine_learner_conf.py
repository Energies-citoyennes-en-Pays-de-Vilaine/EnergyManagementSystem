
from learning.zabbix_reader import ZabbixReader
from credentials.zabbix_credentials import zabbix_credentials
from credentials.db_credentials import db_credentials
from database.query import fetch
from database.EMS_db_types import EMSMachineData
from datetime import datetime
from learning.curve import Curve, make_curves
import matplotlib.pyplot as plt
from sys import argv
from config.config import MachineLearnerConfig
zr = ZabbixReader(zabbix_credentials["url"], zabbix_credentials["token"])
PLOT_GRID = True
def plot_bounds_for_curve(figure, curve:Curve, values):
	max_value = max(values)
	min_value = min(values)
	if (figure == None):
		figure = plt
	figure.plot([curve.timestamp] * 2, [min_value, max_value], 'r', linewidth=0.9)
	figure.plot([curve.timestamp + len(curve.points) * curve.delta_T] * 2, [min_value, max_value], 'r',  linewidth=0.9)

def plot_bounds_for_machine(figure, machine : EMSMachineData, timestamps):
	max_timestamp = max(timestamps)
	min_timestamp = min(timestamps)
	if figure is None:
		figure = plt
	x_axis = [min_timestamp, max_timestamp]
	figure.plot(x_axis, [machine.threshold_begin] * 2 , 'r', linewidth=0.9)
	figure.plot(x_axis, [machine.threshold_end  ] * 2, 'g', linewidth=0.9)

if __name__ == "__main__":
	current_timestamp = int(datetime.now().timestamp())
	current_machine = None
	if (len(argv) < 3):
		known_machines = fetch(db_credentials["EMS"], ("SELECT * FROM machine WHERE machine.id_machine_elfe=%s", [int(argv[1])]))
		known_machines = [EMSMachineData.create_from_select_output(machine) for machine in known_machines]
		if len(known_machines) != 0:
			current_machine = known_machines[0]
	if current_machine == None:
		machine_learner_config = MachineLearnerConfig()
		threshold_begin = machine_learner_config.default_thresh_begin if len(argv) < 3 else int(argv[2])
		threshold_end   = machine_learner_config.default_thresh_end   if len(argv) < 4 else int(argv[3])
		period_count    = machine_learner_config.default_period_count if len(argv) < 5 else int(argv[4])
		period          = machine_learner_config.default_period       if len(argv) < 6 else int(argv[5])
		current_machine = EMSMachineData(0, int(argv[1]), threshold_begin, threshold_end, period, period_count, Id_type=0)
	data = zr.readData(int(argv[1]), current_timestamp - 3 * 24*60*60, current_timestamp)
	curves = make_curves([int(d) for d in data["timestamps"]], data["values"], current_machine.threshold_begin, current_machine.threshold_end, current_machine.period, current_machine.period_count)
	plt.figure("all curves")
	plt.plot([int(d) for d in data["timestamps"]], data["values"])
	for curve in curves:
		curve.plot_curve(plt, True)
		if PLOT_GRID is True:
			plot_bounds_for_curve(None, curve, data["values"])
	if PLOT_GRID is True:
		print("test0")
		plot_bounds_for_machine(plt, current_machine, [int(d) for d in data["timestamps"]])
	if (len(curves) != 0):
		(figure, axes) = plt.subplots(len(curves), 1)
		figure.canvas.manager.set_window_title("acquired curve by first timestamp")
		if len(curves) == 1:
			axes = [axes]
		for i in range(len(curves)):
			curves[i].plot_curve(axes[i], True)
			if PLOT_GRID is True:
				plot_bounds_for_machine(axes[i], current_machine, curves[i].origin_timestamp.tolist())
	plt.show()