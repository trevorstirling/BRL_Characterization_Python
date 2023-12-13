#########################################################################
# Script to capture spectrum using various spectrum analyzers           #
#                                                                       #
# Author: Trevor Stirling                                               #
# Date: Dec 8, 2023                                                     #
#########################################################################

import sys, os
import numpy as np
import matplotlib.pyplot as plt
from GUI_common_functions import BluePSGButton,enforce_number,get_file_locations_GUI,connect_to_GPIB,plot_spectrum
import PySimpleGUI as psg

symbol_open = '▾'
symbol_closed = '▸'

def GUI(debug=False):
	#Options
	psg.set_options(font=('Tahoma', 16))
	psg.theme('DarkBlue14')
	default_SA = 'AQ6374'
	more_SA_options_open = False
	#Define layout
	if debug:
		print_window = []
	else:
		print_window = [psg.Output(size=(10,5), expand_x=True, expand_y=True, key='output')]
	SA_options = [[BluePSGButton('Peak to Center'), psg.InputText('780', key='wavelength', size=(6,1), enable_events=True), BluePSGButton('Set λ [nm]', key='set_center'), psg.InputText('20', key='span', size=(3,1), enable_events=True), BluePSGButton('Set span [nm]', key='set_span'), BluePSGButton('Repeat')]]
	layout = [[psg.Text('Your Name:'), psg.InputText('', key='User_name', size=(30,1), expand_x=True), psg.Text('(for data saving)')],
	[psg.Text('Device Name:'), psg.InputText('', key='Device_name', size=(30,1), expand_x=True)],
	[psg.Text('Spectrum Analyzer:'), psg.Combo(['A86146B', 'A86142A', 'AQ6317B', 'AQ6374', 'E4407B'], default_value=default_SA, size=(8,1), enable_events=True, readonly=True, key='Spectrum_analyzer'), psg.Text('Channel:'), psg.Combo(['Select Spectrum Analyzer first'], size=(2,1), readonly=True, key='Channel')],
	[psg.Checkbox('Show FWHM', size=(12,1), key='FWHM', default=False),psg.Checkbox('Show SMSR', size=(12,1), key='SMSR', default=False)],
	[BluePSGButton('Sweep'), psg.Push(), psg.Checkbox('Display', size=(8,1), key='Display_fig', default=True), psg.Checkbox('Save', size=(6,1), key='Save_fig', default=True), BluePSGButton('Capture'), BluePSGButton('Exit')], #push adds flexible whitespace
	[psg.Text(symbol_closed, enable_events=True, key='more_SA_options'),psg.Text('More SA Functions')],
	[psg.pin(psg.Column(SA_options,key='SA_options',visible=more_SA_options_open))],
	print_window]
	#Create window
	window = psg.Window('Spectrum Analyzer Capture',layout, resizable=True)
	window.finalize() #need to finalize window before editing it in any way
	update_channels(window, default_SA)
	update_labels(window, default_SA)
	#Poll for events
	while True: 
		event, values = window.read()
		if event == psg.WIN_CLOSED or event == 'Exit':
			break
		elif event == 'set_center':
			set_center(values)
		elif event == 'set_span':
			set_span(values)
		elif event == 'Peak to Center':
			peak_to_center(values)
		elif event == 'Repeat':
			sweep_continuously(values)
		elif event == 'Spectrum_analyzer':
			update_channels(window, values['Spectrum_analyzer'])
			update_labels(window, values['Spectrum_analyzer'])
		elif event == 'Capture':
			Spectrum_Analyzer_Capture(window,values)
		elif event == 'Sweep':
			sweep_SA(window, values)
		#open hidden sections
		elif event == 'more_SA_options':
			more_SA_options_open = not more_SA_options_open
			if more_SA_options_open:
				window['more_SA_options'].update(symbol_open)
			else:
				window['more_SA_options'].update(symbol_closed)
			window['SA_options'].update(visible=more_SA_options_open)
		#data validation
		elif event == 'wavelength' and len(values['wavelength']):
			enforce_number(window,values,event)
		elif event == 'span' and len(values['span']):
			enforce_number(window,values,event)
	window.close()

def update_channels(window, spectrum_analyzer):
	if spectrum_analyzer == 'AQ6317B': 
		window['Channel'].update(values = ['A', 'B', 'C'], value = 'A')
	if spectrum_analyzer == 'A86142A' or spectrum_analyzer == 'A86146B': 
		window['Channel'].update(values = ['A', 'B', 'C', 'D', 'E', 'F'], value = 'A')
	if spectrum_analyzer == 'AQ6374': 
		window['Channel'].update(values = ['A', 'B', 'C', 'D', 'E', 'F', 'G'], value = 'A')
	if spectrum_analyzer == 'E4407B': 
		window['Channel'].update(values = ['1', '2', '3'], value = '1')

def update_labels(window, spectrum_analyzer):
	if spectrum_analyzer == 'E4407B':
		window['wavelength'].update(value = '1.5')
		window['span'].update(value = '3')
		window['set_center'].update(text = 'Set f [GHz]')
		window['set_span'].update(text = 'Set span [GHz]')
	else:
		window['wavelength'].update(value = '780')
		window['span'].update(value = '20')
		window['set_center'].update(text = 'Set λ [nm]')
		window['set_span'].update(text = 'Set span [nm]')

def set_center(values):
	spectrum_analyzer_inst = connect_to_GPIB(values['Spectrum_analyzer'])
	if not spectrum_analyzer_inst:
		return
	if spectrum_analyzer_inst.isOSA:
		spectrum_analyzer_inst.set_wavelength(values['wavelength'])
	else:
		spectrum_analyzer_inst.set_frequency(float(values['wavelength'])*1e9) #convert GHz to Hz
	spectrum_analyzer_inst.GPIB.control_ren(0)

def peak_to_center(values):
	spectrum_analyzer_inst = connect_to_GPIB(values['Spectrum_analyzer'])
	if not spectrum_analyzer_inst:
		return
	spectrum_analyzer_inst.peak_to_center()
	spectrum_analyzer_inst.GPIB.control_ren(0)

def set_span(values):
	spectrum_analyzer_inst = connect_to_GPIB(values['Spectrum_analyzer'])
	if not spectrum_analyzer_inst:
		return
	if spectrum_analyzer_inst.isOSA:
		spectrum_analyzer_inst.set_span(values['span'])
	else:
		spectrum_analyzer_inst.set_span(float(values['span'])*1e9) #convert GHz to Hz
	spectrum_analyzer_inst.GPIB.control_ren(0)

def sweep_SA(window, values):
	spectrum_analyzer_inst = connect_to_GPIB(values['Spectrum_analyzer'])
	if not spectrum_analyzer_inst:
		return
	print(" Sweeping...")
	window.refresh()
	spectrum_analyzer_inst.sweep(values['Channel'], print_status=False)
	print(" Sweep complete")
	window.refresh()
	spectrum_analyzer_inst.GPIB.control_ren(0)

def sweep_continuously(values):
	spectrum_analyzer_inst = connect_to_GPIB(values['Spectrum_analyzer'])
	if not spectrum_analyzer_inst:
		return
	spectrum_analyzer_inst.sweep_continuous(1)
	spectrum_analyzer_inst.GPIB.control_ren(0)

def Spectrum_Analyzer_Capture(window,values):
	### Get parameters from GUI
	user_name = values['User_name']
	device_name = values['Device_name']
	spectrum_analyzer = values['Spectrum_analyzer']
	spectrum_analyzer_channel = values['Channel']
	show_SMSR = values['SMSR']
	show_FWHM = values['FWHM']
	display_fig = values['Display_fig']
	save_fig = values['Save_fig']
	save_data = save_fig
	### Initialize other parameters
	characterization_directory = os.path.join('..','Data',user_name)
	### Name Output Files
	[csv_location, png_location, device_name] = get_file_locations_GUI(save_data, save_fig, characterization_directory, 'Spectrum', device_name)
	if device_name == '-NULL-':
		return
	### Connect to Lab Equipment
	# Spectrum Analyzer
	spectrum_analyzer_inst = connect_to_GPIB(spectrum_analyzer)
	if not spectrum_analyzer_inst:
		return
	x_is_freq = spectrum_analyzer_inst.isESA
	### Collect data
	if spectrum_analyzer_inst.is_sweeping():
		psg.popup("Spectrum Analyzer is currently sweeping. Stop before capturing.")
		return
	print(" Capturing...")
	window.refresh()
	x_data, power = spectrum_analyzer_inst.capture(spectrum_analyzer_channel,print_status=False)
	print(" Capture complete")
	window.refresh()
	spectrum_analyzer_inst.GPIB.control_ren(0)
	print(" Disconnected from Spectrum Analyzer")
	#Save data to file
	if save_data:
		full_data = np.zeros((len(power), 2))
		full_data[:,0] = x_data
		full_data[:,1] = power
		if x_is_freq:
			np.savetxt(csv_location, full_data , delimiter=',', header='Frequency [GHz], Power [dBm]', comments='')
		else:
			np.savetxt(csv_location, full_data , delimiter=',', header='Wavelength [nm], Power [dBm]', comments='')
		print(" Data saved to",csv_location)
		window.refresh()
	#Plot data
	if display_fig or save_fig:
		fig = plot_spectrum(device_name, x_data, power, x_is_freq=x_is_freq, show_SMSR=show_SMSR, show_FWHM=show_FWHM)[0]
		if save_fig:
			fig.savefig(png_location,bbox_inches='tight')
			print(" Figure saved to",png_location)
			window.refresh()
		if display_fig:
			print(" Displaying figure. Close figure to resume.")
			window.refresh()
			plt.show()
		else:
			plt.close()
	window.refresh()

if __name__ == "__main__":
	if len(sys.argv)-1 == 1 and (sys.argv[1].lower() == 'debug' or sys.argv[1] == '1'):
		GUI(1)
	else:
		GUI()