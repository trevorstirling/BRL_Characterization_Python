#########################################################################
# Script to take an Autocorrelation using a piezo stage and lock-in     #
# amplifier                                                             #
# Data is saved as                                                      #
# device_SamplingRate_PiezoSpeed_NumPoints.txt                          #
#                                                                       #
# Author: Trevor Stirling                                               #
# Date: Aug 23, 2024                                                    #
#########################################################################

#Removed step amplitude option as both 100 Hz and 1700 Hz jogs overwrite to 50 automatically

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import sys, os
import time
from GUI_common_functions import BluePSGButton,enforce_number,enforce_max_min,get_file_locations_GUI,connect_to_Piezo,connect_to_GPIB,plot_autocorrelator
import PySimpleGUI as psg

font = 'Tahoma'
GUI_defaults_dir = os.path.join(os.path.dirname(__file__),"GUI Defaults")
GUI_file = os.path.basename(__file__).replace(" GUI.py",".txt")

def GUI(debug=False):
	#Options
	psg.set_options(font=(font, 16))
	psg.theme('DarkBlue14')
	#Define layout
	if debug:
		print_window = []
	else:
		print_window = [psg.Multiline(size=(10,5), expand_x=True, expand_y=True, key='output', reroute_stdout=True)]
	layout = [[psg.Text('Your Name:'), psg.InputText('', key='User_name', size=(30,1), expand_x=True), psg.Text('(for data saving)')],
	[psg.Text('Device Name:'), psg.InputText('', key='Device_name', size=(30,1), expand_x=True)],
	[psg.Push(),psg.Text('--------------- Lock-in Amplifier Options ---------------',font=('Tahoma', 20)),psg.Push()],
	[psg.Text('Lock-in Amplifier:'), psg.Combo(['SR830'], default_value='SR830', size=(8,1), enable_events=True, readonly=True, key='Lock-in'), psg.Text('Time Constant:'), psg.Combo(['10 μs','30 μs','100 μs','300 μs','1 ms','3 ms','10 ms','30 ms','100 ms','300 ms','1 s','3 s','10 s','30 s','100 s','300 s','1000 s','3000 s','10,000 s','30,000 s'], default_value='30 μs', size=(7,1), readonly=True, key='Time_constant')],
	[psg.Text('Number of Points:'), psg.InputText('16000', key='num_points', size=(8,1), enable_events=True), psg.Text('Sampling Rate:'), psg.Combo(['62.5 mHz','125 mHz','250 mHz','500 mHz','1 Hz','2 Hz','4 Hz','8 Hz','16 Hz','32 Hz','64 Hz','128 Hz','256 Hz','512 Hz'], default_value='512 Hz', size=(8,1), enable_events=True, readonly=True, key='Sampling_rate'), psg.Text("Approx time: "+str(round(16000/512))+"s", key='approx_time')],
	[psg.Push(),psg.Text('--------------- Piezo Options ---------------',font=('Tahoma', 20)),psg.Push()],
	[psg.Text('Piezo:'), psg.Combo(['Newport'], default_value='Newport', size=(8,1), enable_events=True, readonly=True, key='Piezo'), psg.Text('Speed:'), psg.Combo([5,100,666,1700], default_value=100, size=(4,1), readonly=True, key='Piezo_speed'), psg.Text('Hz'),psg.Text('  Channel:'), psg.Combo([1,2,3,4], default_value=1, size=(2,1), readonly=True, key='Piezo_channel'),psg.Text('Axis:'), psg.Combo([1,2], default_value=1, size=(2,1), readonly=True, key='Piezo_axis'),psg.Text("Step Amplitude:", visible=False), psg.InputText('50', key='step_amplitude', size=(3,1), enable_events=True, visible=False), psg.Text('Piezo Port:'), psg.InputText('COM3', key='piezo_port', size=(5,1))],
	[psg.Text('Move before scan:'), psg.InputText('-1500', key='Piezo_start_loc', size=(8,1), enable_events=True), psg.Text('steps'), psg.Checkbox('Return to start', size=(15,1), key='return_to_start', default=True, enable_events=True),psg.Text("Reverse Correction Factor", key='reverse_factor_text', visible=True), psg.InputText('0.8', key='reverse_correction_factor', size=(5,1), enable_events=True, visible=True)],
	[psg.Push(),psg.Text('--------------- Plot Options ---------------',font=('Tahoma', 20)),psg.Push()],
	[psg.Checkbox('Normalize', size=(10,1), key='normalize', default=True), psg.Text('Fit Type'), psg.Combo(['Low Pass', 'Envelope'], default_value='Envelope', size=(8,1), readonly=True, key='fit_type'), psg.Checkbox('Is Calibrated', size=(12,1), key='is_calibrated', default=False, enable_events=True), psg.Text("Calibration Factor", key='calib_factor_text', visible=False), psg.InputText('2.041', key='time_scale_factor', size=(6,1), enable_events=True, visible=False)],
	[BluePSGButton('Monitor Power'), BluePSGButton('Default 1'), BluePSGButton('Default 2'), psg.Push(), psg.Checkbox('Display', size=(8,1), key='Display_fig', default=True), psg.Checkbox('Save', size=(6,1), key='Save_fig', default=True), BluePSGButton('Autocorrelate'), BluePSGButton('Exit')], #push adds flexible whitespace
	print_window]
	#Create window
	window = psg.Window('Autocorrelation',layout, resizable=True)
	window.finalize() #need to finalize window before editing it in any way
	#Set default values
	num_sources = 0
	if os.path.isfile(os.path.join(GUI_defaults_dir,GUI_file)):
		with open(os.path.join(GUI_defaults_dir, GUI_file),"r") as f:
			data = f.read()
			data = data.split("\n")
			for line in data[:-1]:
				key, value = line.split(": ")
				value = value.replace(" u"," μ")
				if value == "True":
					value = True
				elif value == "False":
					value = False
				window[key].update(value=value)
				#Update GUI based on selections
				if key == 'is_calibrated':
					update_is_calibrated(window,value)
				elif key == 'return_to_start':
					update_return_to_start(window,value)
				elif key == 'Sampling_rate':
					sampling_rate = value
				elif key == 'num_points':
					num_points = value
		update_approx_time(window,num_points,sampling_rate)
	#Poll for events
	while True: 
		event, values = window.read()
		if event == psg.WIN_CLOSED or event == 'Exit':
			break
		elif event == 'is_calibrated':
			update_is_calibrated(window,values[event])
		elif event == 'return_to_start':
			update_return_to_start(window,values[event])
		elif event == 'Autocorrelate':
			Autocorrelation(window,values)
		elif event == 'Monitor Power':
			Monitor_power(values)
			plt.style.use('default')
		elif event == 'Default 1':
			window['num_points'].update(value='16000')
			window['Sampling_rate'].update(value='512 Hz')
			window['Piezo_speed'].update(value=100)
			window['is_calibrated'].update(value=True)
			window['calib_factor_text'].update(visible=True)
			window['time_scale_factor'].update(visible=True)
			window['time_scale_factor'].update(value='2.257')
			window['Piezo_start_loc'].update(value='-1500')
			window['reverse_correction_factor'].update(value='0.8')
			_, values = window.read(timeout=1)
			update_approx_time(window,values['num_points'],values['Sampling_rate'])
		elif event == 'Default 2':
			window['num_points'].update(value='16000')
			window['Sampling_rate'].update(value='256 Hz')
			window['Piezo_speed'].update(value=666)
			window['is_calibrated'].update(value=True)
			window['calib_factor_text'].update(visible=True)
			window['time_scale_factor'].update(visible=True)
			window['time_scale_factor'].update(value='0.1686')
			window['Piezo_start_loc'].update(value='-16000')
			window['reverse_correction_factor'].update(value='0.85')
			_, values = window.read(timeout=1)
			update_approx_time(window,values['num_points'],values['Sampling_rate'])
		elif event == 'Sampling_rate':
			update_approx_time(window,values['num_points'],values['Sampling_rate'])
		#data validation
		elif event == 'num_points' and len(values[event]):
			enforce_number(window,values,event,decimal_allowed=False)
			_, values = window.read(timeout=1)
			if len(values[event]):
				enforce_max_min(window,values,event,16383,6)
			_, values = window.read(timeout=1)
			if len(values[event]):
				update_approx_time(window,values['num_points'],values['Sampling_rate'])
		elif event == 'Piezo_start_loc':
			enforce_number(window,values,event,decimal_allowed=False,negative_allowed=True)
		elif event == 'time_scale_factor' and len(values[event]):
			enforce_number(window,values,event)
		elif event == 'reverse_correction_factor' and len(values[event]):
			enforce_number(window,values,event)
		elif event == 'step_amplitude' and len(values[event]):
			enforce_number(window,values,event,decimal_allowed=False,negative_allowed=True)
			_, values = window.read(timeout=1)
			if len(values['num_points']):
				enforce_max_min(window,values,event,50,-50)
	window.close()

def update_is_calibrated(window,is_calibrated):
	if is_calibrated:
		window['calib_factor_text'].update(visible=True)
		window['time_scale_factor'].update(visible=True)
	else:
		window['time_scale_factor'].update(visible=False)
		window['calib_factor_text'].update(visible=False)

def update_return_to_start(window,return_to_start):
	if return_to_start:
		window['reverse_factor_text'].update(visible=True)
		window['reverse_correction_factor'].update(visible=True)
	else:
		window['reverse_correction_factor'].update(visible=False)
		window['reverse_factor_text'].update(visible=False)

def Monitor_power(values):
	#initialize parameters
	display_time = 10
	update_time = 0.07 #approx, measured [s]
	Lock_in_amp = values['Lock-in']
	#Main Code
	num_points = round(display_time/update_time)
	Lock_in_inst = connect_to_GPIB(Lock_in_amp)
	if not Lock_in_inst:
		return
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
	animation = FuncAnimation(fig, update_power_monitor, fargs=(Lock_in_inst,x,y,fig,line,start_time), interval=1)
	plt.show()
	Lock_in_inst.GPIB.control_ren(0)

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

def update_approx_time(window,num_points,sampling_rate):
	num_points = int(num_points)
	Lock_in_sampling_rate = sampling_rate
	Lock_in_sampling_rate_units = Lock_in_sampling_rate.split(" ")[1]
	if Lock_in_sampling_rate_units == 'mHz':
		Lock_in_sampling_rate = round(float(Lock_in_sampling_rate.split(" ")[0])*1e-3,3)
	elif Lock_in_sampling_rate_units == 'Hz':
		Lock_in_sampling_rate = int(Lock_in_sampling_rate.split(" ")[0])
	num_sec_total = round(num_points/Lock_in_sampling_rate)
	if num_sec_total > 60*60:
		num_sec = num_sec_total%60
		num_min_total = int((num_sec_total-num_sec)/60)
		num_min = num_min_total%60
		num_hour = int((num_min_total-num_min)/60)
		window['approx_time'].update(value="Approx time: "+str(num_hour)+"h "+str(num_min)+"m "+str(num_sec)+"s")
	elif num_sec_total > 60:
		num_sec = num_sec_total%60
		num_min = int((num_sec_total-num_sec)/60)
		window['approx_time'].update(value="Approx time: "+str(num_min)+"m "+str(num_sec)+"s")
	else:
		window['approx_time'].update(value="Approx time: "+str(num_sec_total)+"s")

def Autocorrelation(window,values):
	#Save current settings to default file
	if not os.path.isdir(GUI_defaults_dir):
		os.makedirs(GUI_defaults_dir)
		print(" Created new directory:", GUI_defaults_dir)
		window.Refresh()
	with open(os.path.join(GUI_defaults_dir, GUI_file),"w") as f:
		for field, value in values.items():
			if field != "output":
				f.write(field+": "+str(value).replace("μ","u")+"\n")
	### Get parameters from GUI
	user_name = values['User_name']
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
	fit_type = values['fit_type']
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
	characterization_directory = os.path.join('..','Data',user_name)
	if Lock_in_time_constant > 100e-6:
		response = psg.popup_yes_no("The lock-in time constant should be less than the chopping speed (10 kHz = 100 μs). Do you want to continue?",title="Warning")
		if response == "Yes":
		   pass
		if response == "No":
		   return
	if fit_type == 'Envelope':
		fit_type = 'envelope'
	else:
		fit_type = 'low_pass'
	### Prepare loading bar window
	loading_layout = [[psg.Text('Autocorrelation Progress: 0%',key='progress_text')],
	[psg.ProgressBar(num_points, orientation='h', size=(20, 20), expand_x=True, key='progress_bar')],
    [psg.Push(), psg.Cancel()]]
	### Name Output Files
	scan_name = device_name+"_"+str(Lock_in_sampling_rate)+"Hz_"+str(scan_speed)+"Hz_"+str(num_points)+"pts"
	[csv_location, png_location, scan_name] = get_file_locations_GUI(save_data, save_fig, characterization_directory, 'Autocorrelation', scan_name)
	if scan_name == '-NULL-':
		return
	### Connect to Lab Equipment
	# Lock-in Amplifier
	Lock_in_inst = connect_to_GPIB(Lock_in_amp)
	window.Refresh()
	if not Lock_in_inst:
		return
	Lock_in_inst.set_time_constant(Lock_in_time_constant)
	# Piezo
	Piezo_inst = connect_to_Piezo(Piezo_port,Piezo_channel,Piezo_axis)
	if not Piezo_inst:
		return
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
	piezo_start_loc = Piezo_inst.get_position()
	# Start data collection
	print(" Performing Autocorrelation...")
	window.Refresh()
	Piezo_inst.start_jog(scan_speed)
	Lock_in_inst.start_buffer_collection()
	buffer_size = 0
	loading_window = psg.Window("Autocorrelation Progress", loading_layout)
	loading_window.finalize()
	while buffer_size < num_points:
		time.sleep(0.1)
		buffer_size = Lock_in_inst.read_buffer_size()
		if buffer_size < num_points:
			#psg.one_line_progress_meter('Autocorrelation Progress', buffer_size, num_points, orientation='horizontal')
			loading_window['progress_bar'].UpdateBar(buffer_size)
			loading_window['progress_text'].update(value='Autocorrelation Progress: '+str(round(buffer_size/num_points*100,1))+'%')
		else:
			#psg.one_line_progress_meter('Autocorrelation Progress', num_points, num_points, orientation='horizontal')
			loading_window['progress_bar'].UpdateBar(num_points)
			loading_window['progress_text'].update(value='Autocorrelation Progress: 100%')
	loading_window.close()
	# Return stage to initial position
	Piezo_inst.stop_motion()
	piezo_end_loc = Piezo_inst.get_position()
	if return_to_start:
		print(" Returning to (the best guess of) the initial position")
		window.Refresh()
		Piezo_inst.move_relative(-1*reverse_correction_factor*(piezo_end_loc-piezo_start_loc)-piezo_start_loc) #Labview used a correction factor here
	print(" Reading Data from SR830")
	window.Refresh()
	intensity = Lock_in_inst.read_from_buffer(num_points)
	Piezo_inst.wait_for_complete(60000)
	Piezo_inst.disconnect()
	Lock_in_inst.GPIB.control_ren(0)
	print(" Disconnected from instruments")
	window.Refresh()
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
		fig, FWHM = plot_autocorrelator(device_name, x_axis, intensity, x_axis_calibrated=is_calibrated, normalize=normalize_autocorrelation, fit_type=fit_type)
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
	if not is_calibrated:
		print(" If this is a calibration run with a 94 fs pulse, use time_scale_factor = "+"{:.3f}".format(FWHM/94))
		window.Refresh()
	window.Refresh()

if __name__ == "__main__":
	if len(sys.argv)-1 == 1 and (sys.argv[1].lower() == 'debug' or sys.argv[1] == '1'):
		GUI(1)
	else:
		GUI()