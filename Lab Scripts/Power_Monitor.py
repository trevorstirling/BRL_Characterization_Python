import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from random import randrange
import sys
import time
from common_functions import colour, connect_to_PM, connect_to_GPIB

power_range = 'mW' #W, mW, uW, nW, pW
Power_meter_channel = 'A' #A or B, for two channel Newport only (ignored for one channel)

def main(display_time,update_time,Power_meter):
	num_points = round(display_time/update_time)
	# Power Meter
	if Power_meter == 'Newport':
		from Interfaces import Newport_PM_Interface
		PM_inst = connect_to_PM(Power_meter_channel)
	elif Power_meter == 'K2520':
		input(colour.yellow+" The K2520 must be enabled to act as a power meter. It will be biased to 0 mA. Press any key to continue..."+colour.end)
		PM_inst = connect_to_GPIB(Power_meter,["Current",1,4,0.1,"DC",20e-5,1e-6])
		PM_inst.set_value(0)
		PM_inst.set_output('ON')
	elif Power_meter == 'SR830':
		PM_inst = connect_to_GPIB(Power_meter)
	else:
		raise Exception(colour.red+" "+Power_meter," is not set up as a power meter"+colour.end)
	#initialize vectors
	x = [(i-num_points+1)*update_time for i in range(num_points)]
	y = [float('NaN') for i in x]
	#initialize plot
	plt.style.use('dark_background')
	fig = plt.figure()
	plt.xlabel('Time [s]')
	if Power_meter == 'SR830':
		plt.ylabel('Power ['+power_range.replace("W","V")+']')
	else:
		plt.ylabel('Power ['+power_range+']')
	line = plt.plot(x, y)[0]
	#Update plot
	start_time = time.time()
	animation = FuncAnimation(fig, update, fargs=(PM_inst,x,y,fig,line,start_time), interval=1)
	plt.show()

def update(frame,PM_inst,x,y,fig,line,start_time):
	#read power
	power = PM_inst.read_power() #[W] or [V]
	elapsed_time = time.time()-start_time
	#update vectors
	x.append(elapsed_time)
	x.pop(0)
	y.append(power/scale)
	y.pop(0)
	#update plot
	line.set_data(x, y)
	fig.gca().relim()
	fig.gca().autoscale_view()

if power_range.lower() == 'mw':
	scale = 1e-3
elif power_range.lower() == 'uw':
	scale = 1e-6
elif power_range.lower() == 'nw':
	scale = 1e-9
elif power_range.lower() == 'pw':
	scale = 1e-12
elif power_range.lower() == 'w':
	scale = 1
else:
	raise Exception(colour.red+" range must be W, mW, uW, nW, or pW"+colour.end)

if __name__ == "__main__":
	display_time = 10
	update_time = 0.07 #approx, measured [s]
	Power_meter = "Newport"
	if len(sys.argv)-1 == 0:
		pass
	elif len(sys.argv)-1 == 1:
		Power_meter = sys.argv[1]
	elif len(sys.argv)-1 == 2:
		Power_meter = sys.argv[1]
		display_time = float(sys.argv[2])
	elif len(sys.argv)-1 == 3:
		Power_meter = sys.argv[1]
		display_time = float(sys.argv[2])
		update_time = float(sys.argv[3])
	else:
		raise Exception(colour.red+" main() needs either zero, one, or two arguments"+colour.end)
	main(display_time,update_time,Power_meter)
