#########################################################################
# Script to capture spectrum using various spectrum analyzers			#
# -Call with no arguments  Spectrum_Analyzer_Capture() to display only	#
# -Call with one argument Spectrum_Analyzer_Capture(device_name) to		#
#  save data and figure													#
#																		#
# Author: Trevor Stirling												#
# Date: July 6, 2023													#
#########################################################################

import os
import numpy as np
import matplotlib.pyplot as plt
import sys
from common_functions import colour,connect_to_GPIB,get_file_locations,plot_spectrum

def Spectrum_Analyzer_Capture(device_name):
	##########################################
	####         Define Variables         ####
	##########################################
	characterization_directory = os.path.join('..','Data')
	### Spectrum Analyzer - A86146B, A86142A, AQ6317B, AQ6374, or E4407B
	spectrum_analyzer = 'A86142A'
	spectrum_analyzer_channel = 'A' #A-C for AQ6317B, A-F for A8614x, A-G for AQ6374, or 1-3 for E4407B
	### Sweep Parameters
	sweep_before_capture = False
	##########################################
	####            Main Code             ####
	##########################################
	if device_name == "Test":
		display_fig = True
		save_fig = False
		save_data = False
	else:
		display_fig = False #True/False
		save_fig = True
		save_data = True
	if spectrum_analyzer == 'E4407B':
		spectrum_analyzer_type = 'ESA'
	else:
		spectrum_analyzer_type = 'OSA'
	### Name Output Files
	[csv_location, png_location, device_name] = get_file_locations(save_data, save_fig, characterization_directory, 'Spectrum', device_name)
	### Connect to Lab Equipment
	# Spectrum Analyzer
	spectrum_analyzer_inst = connect_to_GPIB(spectrum_analyzer)
	### Sweep (if desired) and collect data
	if sweep_before_capture:
		spectrum_analyzer_inst.sweep(spectrum_analyzer_channel)
	if spectrum_analyzer_inst.is_sweeping():
		raise Exception(colour.red+" Spectrum Analyzer is currently sweeping. Stop before capturing"+colour.end)
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
			fig = plot_spectrum(device_name, x_data, power,x_is_freq=True)[0]
		else:
			fig = plot_spectrum(device_name, x_data, power)[0]
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
	if len(sys.argv)-1 == 0:
		#No input
		Spectrum_Analyzer_Capture("Test")
	elif len(sys.argv)-1 == 1:
		#One input (device_name)
		Spectrum_Analyzer_Capture(sys.argv[1])
	else:
		raise Exception(colour.red+" Spectrum_Analyzer_Capture needs either zero or one argument"+colour.end)
