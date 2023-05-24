#########################################################################
# Script to take LIV (luminosity and voltage as a function of current)	#
# using up to five current/voltage sources (various models)				#
# -Call with no arguments  LIV() to display LIV only					#
# -Call with one argument LIV(device_name) to save data and figure		#
# Data is saved as														#
# device_source5value_source4value_source3value_source2value.txt 		#
#																		#
# Author: Trevor Stirling												#
# Date: April 19, 2023													#
#########################################################################

#TODO: Test K2520 power meter with other source (see commented out code below)

import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import time
import math
from common_functions import colour,connect_to_PM,connect_to_GPIB,get_file_locations,loading_bar

def Current_Sample(device_name):
	display_fig = True
	save_fig = True
	save_data = True
	##########################################
	####         Define Variables         ####
	##########################################
	total_time = 10 #Total time to sample [s]
	time_spacing = 0.1 #Time between samples (roughly) [s]
	Source_1 = 'B2902A'
	Source_1_mode = 'Voltage' #'Current' or 'Voltage'
	Source_1_channel = 1 #1-16, 'A' or 'B', for two channel sources only (ignored for one channel)
	Source_value = -0.5 #[mA] or [V]
	waveform_1 = "DC" #pulsed or DC
	pulse_delay_1 = 20e-6 #delay between pulses [s] (pulsed mode only)
	pulse_width_1 = 1e-6 #width of pulses [s] (pulsed mode only)
	protection_voltage_1 = 4 #[V]
	protection_current_1 = 0.1 #[A]
	##########################################
	####            Main Code             ####
	##########################################
	characterization_directory = os.path.join('..','Data')
	Source_1_mode = Source_1_mode.capitalize()
	Source_inst_1 = connect_to_GPIB(Source_1,[Source_1_mode,Source_1_channel,protection_voltage_1,protection_current_1,waveform_1,pulse_delay_1,pulse_width_1])
	### Convert from mA to A
	if Source_1_mode == 'Current':
		Source_value = Source_value*1e-3
	### Turn on source
	Source_inst_1.safe_turn_on(Source_value)
	Source_inst_1.set_output('ON')
	### Collect data
	current_list = []
	time_list = []
	start_time = time.time()
	elapsed_time = 0
	loading_bar(0)
	while elapsed_time<total_time:
		elapsed_time = time.time()-start_time
		current_now = Source_inst_1.read_value('Current')
		time_list.append(elapsed_time)
		current_list.append(current_now)
		if elapsed_time<total_time:
			loading_bar(elapsed_time/total_time)
		else:
			loading_bar(1)
		time.sleep(time_spacing) #Might need to play with this to get accurate delay, need to subtract some to account for loop code
	average_current = sum(current_list)/len(current_list)
	[csv_location, png_location, device_name] = get_file_locations(save_data, save_fig, characterization_directory, 'Current Sample', device_name)
	### Save data to file
	if save_data:
		full_data = np.zeros((len(time_list), 2))
		full_data[:,0] = time_list
		full_data[:,1] = current_list
		np.savetxt(csv_location, full_data, delimiter=',', header='Time [s], Current [A]', comments='')
		print(" Data saved to",csv_location)
	### Plot data
	if display_fig or save_fig:
		fig,ax = plt.subplots()
		plt.title(str(device_name))
		ax.set_ylabel('Current [A]')
		ax.set_xlabel('Time [s]\n\nAverage current = '+"{:.1f}".format(average_current))
		ax.plot(time_list, current_list)
		if save_fig:
			fig.savefig(png_location,bbox_inches='tight')
			print(" Figure saved to",png_location)
		if display_fig:
			print(" Displaying figure. Close figure to resume.")
			plt.show()
		else:
			plt.close()
	print(" Disconnected from instruments")

if __name__ == "__main__":
	if len(sys.argv)-1 == 0:
		#No input
		Current_Sample("Test")
	elif len(sys.argv)-1 == 1:
		#One input (device_name)
		Current_Sample(sys.argv[1])
	else:
		raise Exception(colour.red+" Current_Sample needs either zero or one argument"+colour.end)
