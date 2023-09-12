#########################################################################
# Script to take an Autocorrelation using a piezo stage and lock-in     #
# amplifier                                                             #
# GUI added by Eman Shayeb                                              #
# Data is saved as                                                      #
# device_SamplingRate_PiezoSpeed_NumPoints.txt                          #
#                                                                       #
# Author: Trevor Stirling                                               #
# Date: Sept 12, 2023                                                   #
#########################################################################

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import sys
import os
import time
from common_functions import colour,connect_to_Piezo,connect_to_GPIB,get_file_locations,plot_autocorrelator,loading_bar,BluePSGButton
import PySimpleGUI as psg

def GUI():
	#Options
	psg.set_options(font=('Tahoma', 16))
	psg.theme('DarkBlue14')
	#Define layout
	layout = [[psg.Text('Device Name:'), psg.InputText('', key='Device_name', size=(30,1), expand_x=True)],
	[psg.Push(),psg.Text('--------------- Lock-in Amplifier Options ---------------',font=('Tahoma', 20)),psg.Push()],
	[psg.Text('Lock-in Amplifier:'), psg.Combo(['SR830'], default_value='SR830', size=(8,1), enable_events=True, readonly=True, key='Lock-in'), psg.Text('Time Constant:'), psg.Combo(['10 μs','30 μs','100 μs','300 μs','1 ms','3 ms','10 ms','30 ms','100 ms','300 ms','1 s','3 s','10 s','30 s','100 s','300 s','1000 s','3000 s','10,000 s','30,000 s'], default_value='30 μs', size=(7,1), readonly=True, key='Time_constant'), psg.Text('Sampling Rate:'), psg.Combo(['62.5 mHz','125 mHz','250 mHz','500 mHz','1 Hz','2 Hz','4 Hz','8 Hz','16 Hz','32 Hz','64 Hz','128 Hz','256 Hz','512 Hz'], default_value='512 Hz', size=(8,1), readonly=True, key='Sampling_rate')],
	[psg.Push(),psg.Text('--------------- Piezo Options ---------------',font=('Tahoma', 20)),psg.Push()],
	[psg.Text('Piezo:'), psg.Combo(['Newport'], default_value='Newport', size=(8,1), enable_events=True, readonly=True, key='Piezo'), psg.Text('Speed:'), psg.Combo([5,100,666,1700], default_value=100, size=(4,1), readonly=True, key='Piezo_speed'), psg.Text('Hz'),psg.Text('  Channel:'), psg.Combo([1,2,3,4], default_value=1, size=(2,1), readonly=True, key='Piezo_channel'),psg.Text('Axis:'), psg.Combo([1,2], default_value=1, size=(2,1), readonly=True, key='Piezo_axis'),psg.Text("Step Amplitude"), psg.InputText('35', key='step_amplitude', size=(3,1), enable_events=True)],
	[psg.Text('Piezo Port:'), psg.InputText('COM3', key='piezo_port', size=(5,1)), psg.Checkbox('Return to start (Experimental)', size=(26,1), key='return_to_start', default=False, enable_events=True),psg.Text("Reverse Correction Factor", key='reverse_factor_text', visible=False), psg.InputText('1', key='reverse_correction_factor', size=(6,1), enable_events=True, visible=False)],
	[psg.Push(),psg.Text('--------------- Scan Range Options ---------------',font=('Tahoma', 20)),psg.Push()],
	[psg.Text('Number of Points:'), psg.InputText('16000', key='num_points', size=(8,1), enable_events=True), psg.Text('Move before scan:'), psg.InputText('-5000', key='Piezo_start_loc', size=(8,1), enable_events=True), psg.Text('steps')],
	[psg.Push(),psg.Text('--------------- Plot Options ---------------',font=('Tahoma', 20)),psg.Push()],
	[psg.Checkbox('Normalize', size=(10,1), key='normalize', default=True),psg.Checkbox('Is Calibrated', size=(12,1), key='is_calibrated', default=False, enable_events=True), psg.Text("Calibration Factor", key='calib_factor_text', visible=False), psg.InputText('1.965', key='time_scale_factor', size=(6,1), enable_events=True, visible=False)],
	[BluePSGButton('Monitor Power'), psg.Push(), psg.Checkbox('Display', size=(8,1), key='Display_fig', default=True), psg.Checkbox('Save', size=(6,1), key='Save_fig', default=True), BluePSGButton('Autocorrelate'), BluePSGButton('Exit')], #push adds flexible whitespace
	[psg.Output(size=(10,5), expand_x=True, expand_y=True, key='output')]]
	#Create window
	window = psg.Window('Autocorrelation',layout, resizable=True)
	window.finalize() #need to finalize window before editing it in any way
	#Poll for events
	while True: 
		event, values = window.read()
		if event == psg.WIN_CLOSED or event == 'Exit':
			break
		elif event == 'is_calibrated':
			if values['is_calibrated']:
				window['calib_factor_text'].update(visible=True)
				window['time_scale_factor'].update(visible=True)
			else:
				window['time_scale_factor'].update(visible=False)
				window['calib_factor_text'].update(visible=False)
		elif event == 'return_to_start':
			if values['return_to_start']:
				window['reverse_factor_text'].update(visible=True)
				window['reverse_correction_factor'].update(visible=True)
			else:
				window['reverse_correction_factor'].update(visible=False)
				window['reverse_factor_text'].update(visible=False)
		elif event == 'Spectrum_analyzer':
			pass
		elif event == 'Autocorrelate':
			Autocorrelation(window,values)
		elif event == 'Monitor Power':
			Monitor_power(values)
			plt.style.use('default')
		#data validation
		elif event == 'num_points' and len(values['num_points']):
			if values['num_points'][-1] not in ('0123456789'):
				value = values['num_points'][:-1]
				window['num_points'].update(value)
			else:
				value = values['num_points']
			if len(value):
				try:
					value = int(value)
					if value > 16383:
						window['num_points'].update(16383)
				except:
					window['num_points'].update(0)
		elif event == 'Piezo_start_loc':
			if len(values['Piezo_start_loc'])>1 and values['Piezo_start_loc'][-1] not in ('0123456789'):
				value = values['Piezo_start_loc'][:-1]
				window['Piezo_start_loc'].update(value) 
			elif len(values['Piezo_start_loc'])>0 and values['Piezo_start_loc'][-1] not in ('-0123456789'):
				value = values['Piezo_start_loc'][:-1]
				window['Piezo_start_loc'].update(value)
		elif event == 'time_scale_factor' and len(values['time_scale_factor']):
			if values['time_scale_factor'][-1] not in ('.0123456789'):
				value = values['time_scale_factor'][:-1]
				window['time_scale_factor'].update(value)
			elif '.' in values['time_scale_factor'][:-1] and values['time_scale_factor'][-1] == '.':
				value = values['time_scale_factor'][:-1]
				window['time_scale_factor'].update(value)
		elif event == 'reverse_correction_factor' and len(values['reverse_correction_factor']):
			if values['reverse_correction_factor'][-1] not in ('.0123456789'):
				value = values['reverse_correction_factor'][:-1]
				window['reverse_correction_factor'].update(value)
			elif '.' in values['reverse_correction_factor'][:-1] and values['reverse_correction_factor'][-1] == '.':
				value = values['reverse_correction_factor'][:-1]
				window['reverse_correction_factor'].update(value)
		elif event == 'step_amplitude' and len(values['step_amplitude']):
			if len(values['step_amplitude'])>1 and values['step_amplitude'][-1] not in ('0123456789'):
				value = values['step_amplitude'][:-1]
				window['step_amplitude'].update(value)
			elif len(values['step_amplitude'])>0 and values['step_amplitude'][-1] not in ('-0123456789'):
				value = values['step_amplitude'][:-1]
				window['step_amplitude'].update(value)
			else:
				value = values['step_amplitude']
			if len(value) and value != '-':
				try:
					value = int(value)
					if value > 50:
						window['step_amplitude'].update(50)
					elif value < -50:
						window['step_amplitude'].update(-50)
				except:
					window['step_amplitude'].update(0)
	window.close()

def Monitor_power(values):
	#initialize parameters
	display_time = 10
	update_time = 0.07 #approx, measured [s]
	Lock_in_amp = values['Lock-in']
	#Main Code
	num_points = round(display_time/update_time)
	PM_inst = connect_to_GPIB(Lock_in_amp)
	#initialize vectors
	x = [(i-num_points+1)*update_time for i in range(num_points)]
	y = [float('NaN') for i in x]
	#initialize plot
	plt.style.use('dark_background')
	fig = plt.figure()
	plt.xlabel('Time [s]')
	plt.ylabel('Power [mV]')
	line = plt.plot(x, y)[0]
	#Update plot
	start_time = time.time()
	animation = FuncAnimation(fig, update_power_monitor, fargs=(PM_inst,x,y,fig,line,start_time), interval=1)
	plt.show()

def update_power_monitor(frame,PM_inst,x,y,fig,line,start_time):
	#read power
	power = PM_inst.read_power() #[W] or [V]
	elapsed_time = time.time()-start_time
	#update vectors
	x.append(elapsed_time)
	x.pop(0)
	y.append(power/1e-3) #convert to mV
	y.pop(0)
	#update plot
	line.set_data(x, y)
	fig.gca().relim()
	fig.gca().autoscale_view()

def Autocorrelation(window,values):
	### Get parameters from GUI
	device_name = values['Device_name']
	Lock_in_amp = values['Lock-in']
	Lock_in_time_constant = values['Time_constant']
	Lock_in_sampling_rate = values['Sampling_rate']
	Piezo_stage = values['Piezo']
	scan_speed = values['Piezo_speed']
	Piezo_channel = values['Piezo_channel']
	Piezo_axis = values['Piezo_axis']
	step_amplitude = int(values['step_amplitude'])
	Piezo_port = values['piezo_port']
	return_to_start = values['return_to_start']
	reverse_correction_factor = float(values['reverse_correction_factor'])
	start_point = int(values['Piezo_start_loc'])
	num_points = int(values['num_points'])
	normalize_autocorrelation = values['normalize']
	is_calibrated = values['is_calibrated']
	time_scale_factor = float(values['time_scale_factor'])
	display_fig = values['Display_fig']
	save_fig = values['Save_fig']
	save_data = save_fig
	#format parameters with units
	Lock_in_time_constant_units = Lock_in_time_constant.split(" ")[1]
	if Lock_in_time_constant_units == 'μs':
		Lock_in_time_constant = int(Lock_in_time_constant.split(" ")[0])*1e-6
	elif Lock_in_time_constant_units == 'ms':
		Lock_in_time_constant = int(Lock_in_time_constant.split(" ")[0])*1e-3
	elif Lock_in_time_constant_units == 's':
		Lock_in_time_constant = int(Lock_in_time_constant.split(" ")[0])
	Lock_in_time_constant = round(Lock_in_time_constant,6)
	Lock_in_sampling_rate_units = Lock_in_sampling_rate.split(" ")[1]
	if Lock_in_sampling_rate_units == 'mHz':
		Lock_in_sampling_rate = round(float(Lock_in_sampling_rate.split(" ")[0])*1e-3,3)
	elif Lock_in_sampling_rate_units == 'Hz':
		Lock_in_sampling_rate = int(Lock_in_sampling_rate.split(" ")[0])
	### Initialize other parameters
	characterization_directory = os.path.join('..','Data')
	if Lock_in_time_constant > 100e-6:
		response = psg.popup_yes_no("The lock-in time constant should be less than the chopping speed (10 kHz = 100 μs). Do you want to continue?",title="Warning")
		if response == "Yes":
		   pass
		if response == "No":
		   return
	### Name Output Files
	scan_name = device_name+"_"+str(Lock_in_sampling_rate)+"Hz_"+str(scan_speed)+"Hz_"+str(num_points)+"pts"
	[csv_location, png_location, scan_name] = get_file_locations(save_data, save_fig, characterization_directory, 'Autocorrelation', scan_name)
	### Connect to Lab Equipment
	# Lock-in Amplifier
	Lock_in_inst = connect_to_GPIB(Lock_in_amp)
	window.Refresh()
	Lock_in_inst.set_time_constant(Lock_in_time_constant)
	# Piezo
	Piezo_inst = connect_to_Piezo(Piezo_port,Piezo_channel,Piezo_axis)
	window.Refresh()
	### Run Scan
	# Initialize Lock-in Amplifier
	Lock_in_inst.empty_buffer()
	Lock_in_inst.set_sampling_rate(Lock_in_sampling_rate)
	# Move stage to starting position
	Piezo_inst.zero_position()
	Piezo_inst.set_step_amplitude(step_amplitude)
	Piezo_inst.set_step_amplitude(-1*step_amplitude)
	print(" Moving to start position "+str(start_point))
	window.Refresh()
	Piezo_inst.move_relative(start_point)
	Piezo_inst.wait_for_complete(30000)
	# Start data collection
	print(" Performing Autocorrelation...")
	window.Refresh()
	Piezo_inst.start_jog(scan_speed)
	Lock_in_inst.start_buffer_collection()
	buffer_size = 0
	#loading_bar(0)
	#window.Refresh()
	while buffer_size < num_points:
		time.sleep(0.1)
		buffer_size = Lock_in_inst.read_buffer_size()
		if buffer_size < num_points:
			psg.one_line_progress_meter('Autocorrelation Progress', buffer_size, num_points, orientation='horizontal')
			#loading_bar(buffer_size/num_points)
			#window.Refresh()
		else:
			psg.one_line_progress_meter('Autocorrelation Progress', num_points, num_points, orientation='horizontal')
			#loading_bar(1)
			#window.Refresh()
	# Return stage to initial position
	Piezo_inst.stop_motion()
	num_steps_moved = Piezo_inst.get_position()
	if return_to_start:
		print(" Returning to (the best guess of) the initial position")
		window.Refresh()
		Piezo_inst.move_relative(-1*reverse_correction_factor*(num_steps_moved-start_point)-start_point) #Labview used a correction factor here
	print(" Reading Data from SR830")
	window.Refresh()
	intensity = Lock_in_inst.read_from_buffer(num_points)
	Piezo_inst.wait_for_complete(60000)
	x_axis = [i for i in range(num_points)]
	### Save data to file
	if save_data:
		full_data = np.zeros((len(x_axis), 2))
		full_data[:,0] = x_axis
		full_data[:,1] = intensity
		np.savetxt(csv_location, full_data, delimiter=',', header='Time (unscaled) [A.U.], Intensity [V]', comments='')
		print(" Data saved to",csv_location)
		window.Refresh()
	### Plot data
	if display_fig or save_fig:
		if is_calibrated:
			x_axis = [i/time_scale_factor for i in x_axis]
		fig, FWHM = plot_autocorrelator(device_name, x_axis, intensity, x_axis_calibrated=is_calibrated, normalize=normalize_autocorrelation)
		if save_fig:
			fig.savefig(png_location,bbox_inches='tight')
			print(" Figure saved to",png_location)
			window.Refresh()
		if display_fig:
			plt.subplots_adjust(bottom=0.2)
			print(" Displaying figure. Close figure to resume.")
			window.Refresh()
			plt.show()
		else:
			plt.close()
	Piezo_inst.disconnect()
	if not is_calibrated:
		print(" If this is a calibration run with a 110 fs pulse, use time_scale_factor = "+"{:.3f}".format(FWHM/110))
		window.Refresh()
	print(" Disconnected from instruments")
	window.Refresh()

if __name__ == "__main__":
	GUI()