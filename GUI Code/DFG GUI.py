#########################################################################
# Script to capture DFG spectra as a function of wavelength             #
#                                                                       #
# Recommended span = 5nm, resolution = 0.5 nm                           #
#                                                                       #
# Author: Trevor Stirling                                               #
# Date: Dec 13, 2023                                                    #
#########################################################################

# Untested - may need some debugging

import numpy as np
import matplotlib.pyplot as plt
import sys, os
import time
from GUI_common_functions import BluePSGButton,enforce_number,get_file_locations_GUI,connect_to_PM,connect_to_GPIB,plot_spectrum
import PySimpleGUI as psg

font = 'Tahoma'

def GUI(debug=False):
	#Options
	psg.set_options(font=(font, 16))
	psg.theme('DarkBlue14')
	default_laser = 'TSL550'
	default_SA = 'AQ6317B'
	#Define layout
	if debug:
		print_window = []
	else:
		print_window = [psg.Output(size=(10,5), expand_x=True, expand_y=True, key='output')]
	layout = [[psg.Text('Your Name:'), psg.InputText('', key='User_name', size=(30,1), expand_x=True), psg.Text('(for data saving)')],
	[psg.Text('Device Name:'), psg.InputText('', key='Device_name', size=(30,1), expand_x=True)],
	[psg.Text('Laser:'), psg.Combo(['TSL550', 'SWS1501'], default_value=default_laser, size=(8,1), enable_events=True, readonly=True, key='Laser'),psg.Text('Power:'),psg.InputText('1', key='power', size=(3,1), enable_events=True),psg.Text('[mW]')],
	[psg.Text('Start:'),psg.InputText('1570', key='wl_start', size=(6,1), enable_events=True),psg.Text('Step:'),psg.InputText('-3', key='wl_step', size=(6,1), enable_events=True),psg.Text('Stop:'),psg.InputText('1480', key='wl_stop', size=(6,1), enable_events=True),psg.Text('[nm]')],
	[psg.Text('Spectrum Analyzer:'),psg.Combo(['AQ6317B', 'AQ6374'], default_value=default_SA, size=(8,1), enable_events=True, readonly=True, key='Spectrum_analyzer'), psg.Text('Channel:'), psg.Combo(['Select Spectrum Analyzer first'], size=(2,1), readonly=True, key='Channel')],
	[psg.Text('Pump Wavelength:'),psg.InputText('786', key='pump_wavlength', size=(5,1), enable_events=True),psg.Text('[nm]'),psg.Text('Sensitivity:'),psg.Combo(['MID', 'HIGH1', 'HIGH2', 'HIGH3'], default_value='HIGH1', size=(6,1), readonly=True, key='sensitivity')],
	[psg.Checkbox('Show FWHM', size=(12,1), key='FWHM', default=False),psg.Checkbox('Show SMSR', size=(12,1), key='SMSR', default=False)],
	[psg.Push(), psg.Checkbox('Display', size=(8,1), key='Display_fig', default=False), psg.Checkbox('Save', size=(6,1), key='Save_fig', default=True), BluePSGButton('Sweep DFG'), BluePSGButton('Exit')], #push adds flexible whitespace
	print_window]
	#Create window
	window = psg.Window('DFG',layout, resizable=True)
	window.finalize() #need to finalize window before editing it in any way
	update_SA_channel(window, default_SA)
	#Poll for events
	while True: 
		event, values = window.read()
		if event == psg.WIN_CLOSED or event == 'Exit':
			break
		elif event == 'Sweep DFG':
			Sweep_DFG(window,values)
		elif event == 'Spectrum_analyzer':
			update_SA_channel(window, values['Spectrum_analyzer'])
		#data validation
		elif event == 'wl_start'  or event == 'wl_stop' or event == 'power' or event == 'pump_wavlength':
			enforce_number(window,values,event)
		elif event == 'wl_step':
			enforce_number(window,values,event,negative_allowed=True)
	window.close()

def update_SA_channel(window, spectrum_analyzer):
	if spectrum_analyzer == 'AQ6317B': 
		window['Channel'].update(values = ['A', 'B', 'C'], value = 'A')
	if spectrum_analyzer == 'A86142A' or spectrum_analyzer == 'A86146B': 
		window['Channel'].update(values = ['A', 'B', 'C', 'D', 'E', 'F'], value = 'A')
	if spectrum_analyzer == 'AQ6374': 
		window['Channel'].update(values = ['A', 'B', 'C', 'D', 'E', 'F', 'G'], value = 'A')
	if spectrum_analyzer == 'E4407B': 
		window['Channel'].update(values = ['1', '2', '3'], value = '1')

def Sweep_DFG(window,values):
	set_PM_parameters = True
	### Get parameters from GUI
	user_name = values['User_name']
	device_name = values['Device_name']
	display_fig = values['Display_fig']
	save_fig = values['Save_fig']
	save_data = save_fig
	Laser = values['Laser']
	wavelength_start = float(values['wl_start'])
	wavelength_step = float(values['wl_step'])
	wavelength_stop = float(values['wl_stop'])
	laser_power = float(values['power'])
	spectrum_analyzer = values['Spectrum_analyzer']
	spectrum_analyzer_channel = values['Channel']
	wavelength_pump = float(values['pump_wavlength'])
	sensitivity = values['sensitivity']
	show_SMSR = values['SMSR']
	show_FWHM = values['FWHM']
	### Initialize other parameters
	characterization_directory = os.path.join('..','Data',user_name)
	### Connect to Lab Equipment
	Laser_inst = connect_to_GPIB(Laser)
	#window.Refresh()
	spectrum_analyzer_inst = connect_to_GPIB(spectrum_analyzer)
	if not spectrum_analyzer_inst:
		return
	window.Refresh()
	### Sweep values and collect data
	wavlength_list = [x for x in np.arange(wavelength_start,wavelength_stop+wavelength_step/2,wavelength_step)] #[nm]
	num_sweeps = len(wavlength_list)*2
	sweep_num = 0
	for i in range(len(wavlength_list)):
		Laser_inst.set_wavelength(wavlength_list[i])
		print(wavlength_list[i])
		if i == 0:
			Laser_inst.set_power(laser_power)
			Laser_inst.set_output('ON')
			time.sleep(1)
		for scan_name in [device_name+'_'+str(wavlength_list[i])+'_Signal',device_name+'_'+str(wavlength_list[i])+'_Idler']:
			if scan_name[-6:] == 'Signal':
				spectrum_analyzer_inst.set_sensitivity(sensitivity)
				spectrum_analyzer_inst.set_wavelength(wavlength_list[i])
			elif scan_name[-5:] == 'Idler':
				spectrum_analyzer_inst.set_sensitivity('HIGH1')
				spectrum_analyzer_inst.set_wavelength(1/(1/wavelength_pump-1/wavlength_list[i]))
				spectrum_analyzer_inst.sweep(spectrum_analyzer_channel)
				spectrum_analyzer_inst.peak_to_center()
				spectrum_analyzer_inst.set_sensitivity(sensitivity)
			### Collect Spectrum
			sweep_num += 1
			print(" Spectrum Analyzer sweeping "+str(sweep_num)+"/"+str(num_sweeps)+"...")
			print(" Sweeping...")
			window.refresh()
			spectrum_analyzer_inst.sweep(spectrum_analyzer_channel, print_status=False)
			print(" Sweep complete")
			print(" Capturing...")
			window.refresh()
			x_data, power = spectrum_analyzer_inst.capture(spectrum_analyzer_channel, print_status=False)
			print(" Capture complete")
			window.refresh()
			### Name Output Files
			[csv_location, png_location, scan_name] = get_file_locations_GUI(save_data, save_fig, characterization_directory, 'Spectrum', scan_name)
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
				fig = plot_spectrum(scan_name, x_data, power, show_SMSR=show_SMSR, show_FWHM=show_FWHM)[0]
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
	Laser_inst.set_output('OFF')
	Laser_inst.GPIB.control_ren(0)
	print(" Disconnected from instruments")
	

if __name__ == "__main__":
	if len(sys.argv)-1 == 1 and (sys.argv[1].lower() == 'debug' or sys.argv[1] == '1'):
		GUI(1)
	else:
		GUI()