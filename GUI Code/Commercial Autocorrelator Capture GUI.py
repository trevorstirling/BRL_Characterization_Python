#########################################################################
# Script to capture Autocorrelation Trace from APE Pulse Check          #
#                                                                       #
# Author: Trevor Stirling                                               #
# Date: July 30, 2024                                                   #
#########################################################################

import sys, os
import numpy as np
import matplotlib.pyplot as plt
from GUI_common_functions import connect_to_GPIB, plot_intensity_autocorrelation, BluePSGButton, get_file_locations_GUI
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
		print_window = [psg.Output(size=(10,5), expand_x=True, expand_y=True, key='output')]
	layout = [[psg.Text('Your Name:'), psg.InputText('', key='User_name', size=(30,1), expand_x=True), psg.Text('(for data saving)')],
	[psg.Text('Device Name:'), psg.InputText('', key='Device_name', size=(30,1), expand_x=True)],
	[psg.Text('Autocorrelator:'), psg.Combo(['PulseScope'], default_value='PulseScope', size=(10,1), enable_events=True, readonly=True, key='Autocorrelator')],
	[psg.Push(), psg.Checkbox('Display', size=(8,1), key='Display_fig', default=True), psg.Checkbox('Save', size=(6,1), key='Save_fig', default=True), BluePSGButton('Capture'), BluePSGButton('Exit')], #push adds flexible whitespace
	print_window]
	#Create window
	window = psg.Window('Intensity Autocorrelation Capture',layout, resizable=True)
	window.finalize() #need to finalize window before editing it in any way
	#Set default values
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
		elif event == 'Capture':
			Intensity_Autocorrelation_Capture(window,values)
	window.close()

def Intensity_Autocorrelation_Capture(window,values):
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
	device_name = values['Device_name']
	autocorrelator = values['Autocorrelator']
	display_fig = values['Display_fig']
	save_fig = values['Save_fig']
	save_data = save_fig
	### Initialize other parameters
	characterization_directory = os.path.join('..','Data',user_name)
	### Name Output Files
	[csv_location, png_location, device_name] = get_file_locations_GUI(save_data, save_fig, characterization_directory, 'Autocorrelation', device_name)
	if device_name == '-NULL-':
		return
	### Connect to Lab Equipment
	# Spectrum Analyzer
	autocorrelator_inst = connect_to_GPIB('PulseScope')
	if not autocorrelator_inst:
		return
	### Collect data
	print(" Capturing...")
	window.refresh()
	time, intensity = autocorrelator_inst.capture_current()
	print(" Capture complete")
	window.refresh()
	autocorrelator_inst.GPIB.control_ren(0)
	print(" Disconnected from Autocorrelator")
	#Save data to file
	if save_data:
		full_data = np.zeros((len(intensity), 2))
		full_data[:,0] = time
		full_data[:,1] = intensity
		np.savetxt(csv_location, full_data , delimiter=',', header='Time [fs], Intensity [A.U.]', comments='')
		print(" Data saved to",csv_location)
		window.refresh()
	### Plot data
	if display_fig or save_fig:
		fig, FWHM = plot_intensity_autocorrelation(device_name+" Intensity Autocorrelation", time, intensity)
		if save_fig:
			fig.savefig(png_location,bbox_inches='tight')
			print(" Figure saved to",png_location)
			# window.Refresh()
		if display_fig:
			plt.subplots_adjust(bottom=0.2)
			print(" Displaying figure. Close figure to resume.")
			# window.Refresh()
			plt.show()
		else:
			plt.close()
	window.refresh()

if __name__ == "__main__":
	if len(sys.argv)-1 == 1 and (sys.argv[1].lower() == 'debug' or sys.argv[1] == '1'):
		GUI(1)
	else:
		GUI()