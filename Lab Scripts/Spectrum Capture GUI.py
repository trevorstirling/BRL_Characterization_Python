#########################################################################
# Script to capture spectrum using various spectrum analyzers           #
# GUI added by Eman Shayeb                                              #
#                                                                       #
# Author: Trevor Stirling                                               #
# Date: Sept 12, 2023                                                   #
#########################################################################

import os
import numpy as np
import matplotlib.pyplot as plt
from common_functions import connect_to_GPIB,get_file_locations,plot_spectrum,BluePSGButton
import PySimpleGUI as psg

symbol_open = '▾'
symbol_closed = '▸'

def GUI():
	#Options
	psg.set_options(font=('Tahoma', 16))
	psg.theme('DarkBlue14')
	default_SA = 'AQ6374'
	more_SA_options_open = False
	#Define layout
	SA_options = [[BluePSGButton('Peak to Center'), psg.InputText('780', key='wavelength', size=(5,1), enable_events=True), BluePSGButton('Set λ [nm]'), psg.InputText('20', key='span', size=(3,1), enable_events=True), BluePSGButton('Set span [nm]'), BluePSGButton('Repeat')]]
	layout = [[psg.Text('Device Name:'), psg.InputText('', key='Device_name', size=(30,1), expand_x=True)],
	[psg.Text('Spectrum Analyzer:'), psg.Combo(['A86146B', 'A86142A', 'AQ6317B', 'AQ6374', 'E4407B'], default_value=default_SA, size=(8,1), enable_events=True, readonly=True, key='Spectrum_analyzer'), psg.Text('Channel:'), psg.Combo(['Select Spectrum Analyzer first'], size=(2,1), readonly=True, key='Channel')],
	[psg.Checkbox('Show FWHM', size=(10,1), key='FWHM', default=False),psg.Checkbox('Show SMSR', size=(10,1), key='SMSR', default=False)],
	[BluePSGButton('Sweep'), psg.Push(), psg.Checkbox('Display', size=(8,1), key='Display_fig', default=True), psg.Checkbox('Save', size=(6,1), key='Save_fig', default=True), BluePSGButton('Capture'), BluePSGButton('Exit')], #push adds flexible whitespace
	[psg.Text(symbol_closed, enable_events=True, key='more_SA_options'),psg.Text('More SA Functions')],
	[psg.pin(psg.Column(SA_options,key='SA_options',visible=more_SA_options_open))],
	[psg.Output(size=(10,5), expand_x=True, expand_y=True)]]
	#Create window
	window = psg.Window('Spectrum Analyzer Capture',layout, resizable=True)
	window.finalize() #need to finalize window before editing it in any way
	update_channels(window, default_SA)
	#Poll for events
	while True: 
		event, values = window.read()
		if event == psg.WIN_CLOSED or event == 'Exit':
			break
		elif event == 'Set λ [nm]':
			set_wavelength(values)
		elif event == 'Set span [nm]':
			set_span(values)
		elif event == 'Peak to Center':
			peak_to_center(values)
		elif event == 'Repeat':
			sweep_continuously(values)
		elif event == 'Spectrum_analyzer':
			update_channels(window, values['Spectrum_analyzer'])
		elif event == 'Capture':
			Spectrum_Analyzer_Capture(values)
		elif event == 'Sweep':
			sweep_SA(values)
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
			if values['wavelength'][-1] not in ('.0123456789'):
				value = values['wavelength'][:-1]
				window['wavelength'].update(value)
			elif '.' in values['wavelength'][:-1] and values['wavelength'][-1] == '.':
				value = values['wavelength'][:-1]
				window['wavelength'].update(value)
		elif event == 'span' and len(values['span']):
			if values['span'][-1] not in ('.0123456789'):
				value = values['span'][:-1]
				window['span'].update(value)
			elif '.' in values['span'][:-1] and values['span'][-1] == '.':
				value = values['span'][:-1]
				window['span'].update(value)
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

def set_wavelength(values):
	spectrum_analyzer_inst = connect_to_GPIB(values['Spectrum_analyzer'])
	spectrum_analyzer_inst.set_wavelength(values['wavelength'])

def peak_to_center(values):
	spectrum_analyzer_inst = connect_to_GPIB(values['Spectrum_analyzer'])
	spectrum_analyzer_inst.peak_to_center()

def set_span(values):
	spectrum_analyzer_inst = connect_to_GPIB(values['Spectrum_analyzer'])
	spectrum_analyzer_inst.set_span(values['span'])

def sweep_SA(values):
	spectrum_analyzer_inst = connect_to_GPIB(values['Spectrum_analyzer'])
	spectrum_analyzer_inst.sweep(values['Channel'])

def sweep_continuously(values):
	spectrum_analyzer_inst = connect_to_GPIB(values['Spectrum_analyzer'])
	spectrum_analyzer_inst.sweep_continuous(1)

def Spectrum_Analyzer_Capture(values):
	### Get parameters from GUI
	device_name = values['Device_name']
	spectrum_analyzer = values['Spectrum_analyzer']
	spectrum_analyzer_channel = values['Channel']
	show_SMSR = values['SMSR']
	show_FWHM = values['FWHM']
	display_fig = values['Display_fig']
	save_fig = values['Save_fig']
	save_data = save_fig
	### Initialize other parameters
	characterization_directory = os.path.join('..','Data')
	if spectrum_analyzer == 'E4407B':
		spectrum_analyzer_type = 'ESA'
	else:
		spectrum_analyzer_type = 'OSA'
	### Name Output Files
	[csv_location, png_location, device_name] = get_file_locations(save_data, save_fig, characterization_directory, 'Spectrum', device_name)
	### Connect to Lab Equipment
	# Spectrum Analyzer
	spectrum_analyzer_inst = connect_to_GPIB(spectrum_analyzer)
	### Collect data
	if spectrum_analyzer_inst.is_sweeping():
		psg.popup("Spectrum Analyzer is currently sweeping. Stop before capturing.")
		return
	x_data, power = spectrum_analyzer_inst.capture(spectrum_analyzer_channel)
	#Save data to file
	if save_data:
		full_data = np.zeros((len(power), 2))
		full_data[:,0] = x_data
		full_data[:,1] = power
		if spectrum_analyzer_type == 'ESA':
			np.savetxt(csv_location, full_data , delimiter=',', header='Frequency [GHz], Power [dBm]', comments='')
		else:
			np.savetxt(csv_location, full_data , delimiter=',', header='Wavelength [nm], Power [dBm]', comments='')
		print(" Data saved to",csv_location)
	#Plot data
	if display_fig or save_fig:
		if spectrum_analyzer_type == 'ESA':
			fig = plot_spectrum(device_name, x_data, power, x_is_freq=True, show_SMSR=show_SMSR, show_FWHM=show_FWHM)[0]
		else:
			fig = plot_spectrum(device_name, x_data, power, show_SMSR=show_SMSR, show_FWHM=show_FWHM)[0]
		if save_fig:
			fig.savefig(png_location,bbox_inches='tight')
			print(" Figure saved to",png_location)
		if display_fig:
			print(" Displaying figure. Close figure to resume.")
			plt.show()
		else:
			plt.close()
	print(" Disconnected from Spectrum Analyzer")

if __name__ == "__main__":
   GUI()