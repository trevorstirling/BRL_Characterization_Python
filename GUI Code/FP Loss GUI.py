#########################################################################
# Script to measure transmission as a function of wavelength            #
# Extracts loss using Fabry Perot theory                                #
#                                                                       #
# Recommended to turn coherence control off on the laser                #
#                                                                       #
# Author: Trevor Stirling                                               #
# Date: July 24, 2024                                                   #
#########################################################################

import numpy as np
import matplotlib.pyplot as plt
import sys, os
import time
from GUI_common_functions import BluePSGButton,enforce_number,get_file_locations_GUI,connect_to_PM,connect_to_GPIB,plot_FP_Loss
import PySimpleGUI as psg

font = 'Tahoma'
GUI_defaults_dir = os.path.join(os.path.dirname(__file__),"GUI Defaults")
GUI_file = os.path.basename(__file__).replace(" GUI.py",".txt")

def GUI(debug=False):
	#Options
	psg.set_options(font=(font, 16))
	psg.theme('DarkBlue14')
	default_laser = 'TSL550'
	#Define layout
	if debug:
		print_window = []
	else:
		print_window = [psg.Output(size=(10,5), expand_x=True, expand_y=True, key='output')]
	layout = [[psg.Text('Your Name:'), psg.InputText('', key='User_name', size=(30,1), expand_x=True), psg.Text('(for data saving)')],
	[psg.Text('Device Name:'), psg.InputText('', key='Device_name', size=(30,1), expand_x=True)],
	[psg.Text('Laser:'), psg.Combo(['TSL550', 'SWS1501'], default_value=default_laser, size=(8,1), enable_events=True, readonly=True, key='Laser'),psg.Text('Power:'),psg.InputText('1', key='power', size=(3,1), enable_events=True),psg.Text('[mW]')],
	[psg.Text('Start:'),psg.InputText('1545', key='wl_start', size=(6,1), enable_events=True),psg.Text('Step:'),psg.InputText('0.005', key='wl_step', size=(6,1), enable_events=True),psg.Text('Stop:'),psg.InputText('1555', key='wl_stop', size=(6,1), enable_events=True),psg.Text('[nm]')],
	[psg.Text('Power Meter:'), psg.Combo(['Newport'], default_value='Newport', size=(7,1), enable_events=True, readonly=True, key='Power_meter'), psg.Text('Channel:'), psg.Combo(['A','B'], default_value='A', size=(2,1), readonly=True, key='PM_Channel')],
	#[psg.Checkbox('Show FWHM', size=(12,1), key='FWHM', default=False),psg.Checkbox('Show SMSR', size=(12,1), key='SMSR', default=False)],
	[psg.Push(), psg.Checkbox('Display', size=(8,1), key='Display_fig', default=True), psg.Checkbox('Save', size=(6,1), key='Save_fig', default=True), BluePSGButton('Measure'), BluePSGButton('Exit')], #push adds flexible whitespace
	print_window]
	#Create window
	window = psg.Window('FP Loss',layout, resizable=True)
	window.finalize() #need to finalize window before editing it in any way
	#Set default values
	num_sources = 0
	if os.path.isfile(os.path.join(GUI_defaults_dir,GUI_file)):
		with open(os.path.join(GUI_defaults_dir, GUI_file),"r") as f:
			data = f.read()
			data = data.split("\n")
			for line in data[:-1]:
				key, value = line.split(": ")
				if value == "True":
					value = True
				elif value == "False":
					value = False
				window[key].update(value=value)
	#Poll for events
	while True: 
		event, values = window.read()
		if event == psg.WIN_CLOSED or event == 'Exit':
			break
		elif event == 'Measure':
			FP_Loss(window,values)
		#data validation
		elif event == 'wl_start'  or event == 'wl_stop' or event == 'power':
			enforce_number(window,values,event)
		elif event == 'wl_step':
			enforce_number(window,values,event,negative_allowed=True)
	window.close()

def FP_Loss(window,values):
	set_PM_parameters = True
	#Save current settings to default file
	if not os.path.isdir(GUI_defaults_dir):
		os.makedirs(GUI_defaults_dir)
		print(" Created new directory:", GUI_defaults_dir)
		window.Refresh()
	with open(os.path.join(GUI_defaults_dir, GUI_file),"w") as f:
		for field, value in values.items():
			f.write(field+": "+str(value)+"\n")
	### Get parameters from GUI
	user_name = values['User_name']
	scan_name = values['Device_name']
	display_fig = values['Display_fig']
	save_fig = values['Save_fig']
	save_data = save_fig
	Laser = values['Laser']
	wavelength_start = float(values['wl_start'])
	wavelength_step = float(values['wl_step'])
	wavelength_stop = float(values['wl_stop'])
	laser_power = float(values['power'])
	Power_meter = values['Power_meter']
	Power_meter_channel = values['PM_Channel']
	### Initialize other parameters
	characterization_directory = os.path.join('..','Data',user_name)
	### Connect to Lab Equipment
	Laser_inst = connect_to_GPIB(Laser)
	window.Refresh()
	if Power_meter == 'Newport':
		from GUI_Interfaces import Newport_PM_Interface
		PM_inst = connect_to_PM(Power_meter_channel)
		if not PM_inst:
			return
		if set_PM_parameters:
			PM_inst.set_filtering(3)
			PM_inst.set_analogfilter(4)
			PM_inst.set_digitalfilter(100)
			PM_inst.set_wavelength(round((wavelength_start+wavelength_stop)/2))
		window.Refresh()
	else:
		psg.popup(Power_meter+" is not set up as a power meter")
	### Sweep values and collect data
	wavlength_list = [x for x in np.arange(wavelength_start,wavelength_stop+wavelength_step/2,wavelength_step)] #[nm]
	num_points = len(wavlength_list)
	power_list = [0]*num_points #[W]
	### Prepare loading bar window
	loading_layout = [[psg.Text('Scan Progress: 0%',key='progress_text')],
	[psg.ProgressBar(num_points, orientation='h', size=(20, 20), expand_x=True, key='progress_bar')],
	[psg.Push(), psg.Cancel()]]
	loading_window = psg.Window("Scan Progress", loading_layout)
	loading_window.finalize()
	for i in range(num_points):
		Laser_inst.set_wavelength(wavlength_list[i])
		if i == 0:
			Laser_inst.set_power(laser_power)
			Laser_inst.set_output('ON')
			time.sleep(1)
		#delay for power meter to stabilize
		time.sleep(0.2)
		power_list[i] = PM_inst.read_power()
		loading_window['progress_bar'].UpdateBar(i+1)
		loading_window['progress_text'].update(value='Scan Progress: '+str(round((i+1)/num_points*100,1))+'%')
		if power_list[i] == '-NULL-':
			return
	loading_window.close()
	Laser_inst.set_output('OFF')
	Laser_inst.GPIB.control_ren(0)
	print(" Disconnected from instruments")
	### Name Output Files
	[csv_location, png_location, scan_name] = get_file_locations_GUI(save_data, save_fig, characterization_directory, 'FP Loss', scan_name)
	if scan_name == '-NULL-':
		return
	### Save data to file
	if save_data:
		full_data = np.zeros((len(wavlength_list), 2))
		full_data[:,0] = wavlength_list
		full_data[:,1] = power_list
		np.savetxt(csv_location, full_data, delimiter=',', header='Wavelength [nm], Power [W]', comments='')
		print(" Data saved to",csv_location)
		window.Refresh()
	### Plot data
	if display_fig or save_fig:
		fig = plot_FP_Loss(scan_name, power_list, wavlength_list)[0]
		if save_fig:
			fig.savefig(png_location,bbox_inches='tight')
			print(" Figure saved to",png_location)
			window.Refresh()
		if display_fig:
			print(" Displaying figure. Close figure to resume.")
			window.Refresh()
			plt.show()
		else:
			plt.close()

if __name__ == "__main__":
	if len(sys.argv)-1 == 1 and (sys.argv[1].lower() == 'debug' or sys.argv[1] == '1'):
		GUI(1)
	else:
		GUI()