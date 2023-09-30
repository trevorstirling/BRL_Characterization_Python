#########################################################################
# Script to monitor power from Newport Power Meter                      #
#                                                                       #
# Author: Trevor Stirling                                               #
# Date: Sept 29, 2023                                                   #
#########################################################################

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import sys
import time
from GUI_common_functions import BluePSGButton,enforce_number,connect_to_GPIB,connect_to_PM
import PySimpleGUI as psg

def GUI(debug=False):
	#Options
	psg.set_options(font=('Tahoma', 16))
	psg.theme('DarkBlue14')
	#Define layout
	if debug:
		print_window = []
	else:
		print_window = [psg.Output(size=(10,5), expand_x=True, expand_y=True, key='output')]
	layout = [[psg.Text('Power Meter:'), psg.Combo(['Newport', 'SR830', 'K2520'], default_value='Newport', size=(8,1), enable_events=True, readonly=True, key='Power_meter'), psg.Text('Channel:', key='channel_text'), psg.Combo(['A','B'], default_value='A', size=(2,1), readonly=True, key='Channel', visible=True), psg.Text('Range:'), psg.Combo(['W', 'mW', 'μW', 'nW', 'pW'], default_value='mW', size=(4,1), enable_events=True, readonly=True, key='Range'), ],
	[psg.Text('Display Time [s]:'), psg.InputText('10', key='display_time', size=(4,1), enable_events=True), psg.Text('Update Time [s]:'), psg.InputText('0.07', key='update_time', size=(4,1), enable_events=True)],
	[psg.Push(),BluePSGButton('Start'), BluePSGButton('Exit')],
	print_window]
	#Create window
	window = psg.Window('Power Monitor',layout, resizable=True)
	window.finalize() #need to finalize window before editing it in any way
	#Poll for events
	while True: 
		event, values = window.read()
		if event == psg.WIN_CLOSED or event == 'Exit':
			break
		elif event == 'Power_meter':
			update_channels(window, values['Power_meter'])
		elif event == 'Start':
			Power_Monitor(window,values)
		#data validation
		elif event == 'display_time':
			enforce_number(window,values,event)
		elif event == 'update_time':
			enforce_number(window,values,event)
	window.close()

def update_channels(window, power_meter):
	if power_meter == 'Newport': 
		window['channel_text'].update(visible=True)
		window['Channel'].update(values = ['A', 'B'], value = 'A', visible=True)
		window['Range'].update(values = ['W', 'mW', 'μW', 'nW', 'pW'], value = 'mW')
	elif power_meter == 'K2520':
		window['Range'].update(values = ['W', 'mW', 'μW', 'nW', 'pW'], value = 'mW')
		window['Channel'].update(visible=False)
		window['channel_text'].update(visible=False)
	elif power_meter == 'SR830':
		window['Range'].update(values = ['V', 'mV', 'μV', 'nV', 'pV'], value = 'mV')
		window['Channel'].update(visible=False)
		window['channel_text'].update(visible=False)

def Power_Monitor(window,values):
	### Get parameters from GUI
	Power_meter = values['Power_meter']
	Power_meter_channel = values['Channel']
	power_range = values['Range']
	display_time = float(values['display_time'])
	update_time = float(values['update_time'])
	if len(power_range)==1:
		scale = 1
	else:
		prefix = power_range[0]
		if prefix == 'm':
			scale = 1e-3
		elif prefix == 'μ':
			scale = 1e-6
		elif prefix == 'n':
			scale = 1e-9
		elif prefix == 'p':
			scale = 1e-12
	# Power Meter
	if Power_meter == 'Newport':
		from GUI_Interfaces import Newport_PM_Interface
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
	num_points = round(display_time/update_time)
	x = [(i-num_points+1)*update_time for i in range(num_points)]
	y = [float('NaN') for i in x]
	#initialize plot
	plt.style.use('dark_background')
	fig = plt.figure()
	plt.xlabel('Time [s]')
	plt.ylabel('Power ['+power_range+']')
	line = plt.plot(x, y)[0]
	#Update plot
	start_time = time.time()
	animation = FuncAnimation(fig, update, fargs=(PM_inst,x,y,fig,line,start_time,scale), interval=1)
	plt.show()

def update(frame,PM_inst,x,y,fig,line,start_time,scale):
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

if __name__ == "__main__":
	if len(sys.argv)-1 == 1 and sys.argv[1].lower() == 'debug':
		GUI(1)
	else:
		GUI()