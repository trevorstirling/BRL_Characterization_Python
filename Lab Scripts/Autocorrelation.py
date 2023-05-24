#########################################################################
# Script to take an Autocorrelation using a piezo stage and lock-in		#
# amplifier																#
# -Call with no arguments  Autocorrelation() to display figure only		#
# -Call with one argument Autocorrelation(device_name) to save data and #
#  figure																#
# Data is saved as														#
# device_SamplingRate_PiezoSpeed_NumPoints.txt 							#
#																		#
# Author: Trevor Stirling												#
# Date: March 9, 2023													#
#########################################################################

import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import time
import math
from scipy.optimize import curve_fit
from common_functions import colour,connect_to_PM,connect_to_Piezo,connect_to_GPIB,get_file_locations,plot_autocorrelator,loading_bar

def Autocorrelation(device_name):
	##########################################
	####         Define Variables         ####
	##########################################
	characterization_directory = os.path.join('..','Data')
	display_before_save = True #True/False
	normalize_autocorrelation = True #True/False
	### Lock-in Amplifier - SR830
	Lock_in_amp = 'SR830'
	Lock_in_time_constant = 30e-6 #Should be less than the chopping speed (10 kHz = 100 us)
	Lock_in_sampling_rate = 512 #[Hz]
	### Piezo Stage - Newport
	Piezo_stage = 'Newport'
	Piezo_port = 'COM3'
	Piezo_channel = 1
	Piezo_axis = 1
	start_point = 0
	scan_speed = 1700 # Plus or minus 5, 100, 666, or 1700
	num_points = 16000 # Max 16000 (lock-in buffer size)
	step_amplitude = 35
	reverse_correction_factor = 0 # 0 will stop return to initial position
	#Claibrate x axis if scan parameters have been used before
	if Lock_in_sampling_rate == 512 and scan_speed == 100 and step_amplitude == 35:
		time_scale_factor = 2.146 #March 9, 2023
	elif Lock_in_sampling_rate == 512 and scan_speed == 1700 and step_amplitude == 35:
		time_scale_factor = 0.087 #March 7, 2023
	else:
		time_scale_factor = 'Uncalibrated' # Will suggest time_scale_factor to use in future runs assuming a 110 fs pulse width
	##########################################
	####            Main Code             ####
	##########################################
	if device_name == "Test":
		display_fig = True
		save_fig = False
		save_data = False
	else:
		display_fig = display_before_save
		save_fig = True
		save_data = True
	if time_scale_factor == 'Uncalibrated':
		is_calibrated = False
	elif type(time_scale_factor) == int or type(time_scale_factor) == float:
		is_calibrated = True
	else:
		raise Exception(colour.red+colour.alert+" time_scale_factor must be a number or 'Uncalibrated'"+colour.end)
	if num_points > 16383:
		raise Exception(colour.red+colour.alert+" Requested more data points than SR830 buffer contains, keep below 16000"+colour.end)
	if Lock_in_time_constant > 100e-6:
		raise Exception(colour.red+colour.alert+" The lock-in time constant should be less than the chopping speed (10 kHz = 100 us)"+colour.end)
	### Connect to Lab Equipment
	# Lock-in Amplifier
	if Lock_in_amp == 'SR830':
		Lock_in_inst = connect_to_GPIB(Lock_in_amp)
	else:
		raise Exception(colour.red+" "+Lock_in_amp," is not set up as a lock-in amplifier"+colour.end)
	Lock_in_inst.set_time_constant(Lock_in_time_constant)
	# Piezo
	Piezo_inst = connect_to_Piezo(Piezo_port,Piezo_channel,Piezo_axis)
	### Run Scan
	# Initialize Lock-in Amplifier
	Lock_in_inst.empty_buffer()
	Lock_in_inst.set_sampling_rate(Lock_in_sampling_rate)
	# Move stage to starting position
	Piezo_inst.zero_position()
	Piezo_inst.set_step_amplitude(step_amplitude)
	Piezo_inst.set_step_amplitude(-1*step_amplitude)
	print(" Moving to start position "+str(start_point))
	Piezo_inst.move_relative(start_point)
	Piezo_inst.wait_for_complete(30000)
	# Start data collection
	print(" Performing Autocorrelation:")
	Piezo_inst.start_jog(scan_speed)
	Lock_in_inst.start_buffer_collection()
	buffer_size = 0
	loading_bar(0)
	while buffer_size < num_points:
		time.sleep(0.1)
		buffer_size = Lock_in_inst.read_buffer_size()
		if buffer_size < num_points:
			loading_bar(buffer_size/num_points)
		else:
			loading_bar(1)
	# Return stage to initial position
	Piezo_inst.stop_motion()
	num_steps_moved = Piezo_inst.get_position()
	if reverse_correction_factor != 0:
		print(" Returning to (the best guess of) the initial position")
		Piezo_inst.move_relative(-1*reverse_correction_factor*(num_steps_moved-start_point)-start_point) #Labview used a correction factor here
	print(" Reading Data from SR830")
	intensity = Lock_in_inst.read_from_buffer(num_points)
	Piezo_inst.wait_for_complete(60000)
	x_axis = [i for i in range(num_points)]
	### Name Output Files
	scan_name = device_name+"_"+str(Lock_in_sampling_rate)+"Hz_"+str(scan_speed)+"Hz_"+str(num_points)+"pts"
	[csv_location, png_location, scan_name] = get_file_locations(save_data, save_fig, characterization_directory, 'Autocorrelation', scan_name)
	### Save data to file
	if save_data:
		full_data = np.zeros((len(x_axis), 2))
		full_data[:,0] = x_axis
		full_data[:,1] = intensity
		np.savetxt(csv_location, full_data, delimiter=',', header='Time (unscaled) [A.U.], Intensity [V]', comments='')
		print(" Data saved to",csv_location)
	### Plot data
	if display_fig or save_fig:
		if time_scale_factor != 'Uncalibrated':
			x_axis = [i/time_scale_factor for i in x_axis]
		fig, FWHM = plot_autocorrelator(device_name, x_axis, intensity, x_axis_calibrated=is_calibrated, normalize=normalize_autocorrelation)
		if save_fig:
			fig.savefig(png_location,bbox_inches='tight')
			print(" Figure saved to",png_location)
		if display_fig:
			plt.subplots_adjust(bottom=0.2)
			print(" Displaying figure. Close figure to resume.")
			plt.show()
		else:
			plt.close()
	Piezo_inst.disconnect()
	if time_scale_factor == 'Uncalibrated':
		print(" If this is a calibration run with a 110 fs pulse, use time_scale_factor = "+"{:.3f}".format(FWHM/110))
	print(" Disconnected from instruments")

if __name__ == "__main__":
	if len(sys.argv)-1 == 0:
		#No input
		Autocorrelation("Test")
	elif len(sys.argv)-1 == 1:
		#One input (device_name)
		Autocorrelation(sys.argv[1])
	else:
		raise Exception(colour.red+" Autocorrelation needs either zero or one argument"+colour.end)
