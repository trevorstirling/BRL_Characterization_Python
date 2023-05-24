#########################################################################
# Script to take spectrum at different current values using	various lab	#
# equipment																#
# -Call with no arguments Spectrum_Analyzer_Capture_Current_Sweep() 	#
#  to display only														#
# -Call with one argument												#
#  Spectrum_Analyzer_Capture_Current_Sweep(device_name) to save data	#
#  and figure															#
#																		#
# Author: Trevor Stirling												#
# Date: Feb 18, 2022													#
#########################################################################

import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import time
import math
from datetime import date
from common_functions import colour,connect_to_GPIB,get_file_locations,plot_spectrum

def Spectrum_Analyzer_Capture_Source_Sweep(device_name):
	##########################################
	####         Define Variables         ####
	##########################################
	characterization_directory = os.path.join('..','Data')
	adjust_center = True #move peak to center after each scan (before next scan)
	show_SMSR = False
	show_FWHM = False
	### Spectrum Analyzer - A86146B, AQ6317B, or E4407B
	spectrum_analyzer = 'AQ6317B'
	spectrum_analyzer_channel = 'A' #A-C for AQ6317B, A-F for A86146B, or 1-3 for E4407B
	### Channel 1 Source - K2520, K2604B, B2902A, or LDC3908
	Source_1 = 'B2902A'
	Source_1_mode = 'Current' #'Current' or 'Voltage'
	Source_1_channel = 1 #1-8, 'A' or 'B', for two channel sources only (ignored for one channel)
	Source_start_1 = 90 #[mA] or [V]
	Source_step_1 = 10 #[mA] or [V]
	Source_stop_1 = 150 #[mA] or [V]
	waveform_1 = "DC" #pulsed or DC
	pulse_delay_1 = 20e-6 #delay between pulses [s] (pulsed mode only)
	pulse_width_1 = 1e-6 #width of pulses [s] (pulsed mode only)
	protection_voltage_1 = 4 #[V]
	protection_current_1 = 0.1 #[A]
	### Channel 2 Source - K2520, K2604B, B2902A, or LDC3908
	Source_2 = 'K2604B'
	Source_2_mode = 'Voltage' #'Current' or 'Voltage'
	Source_2_channel = 1 #1-8, 'A' or 'B', for two channel sources only (ignored for one channel)
	Source_start_2 = 0 #[mA] or [V]
	Source_step_2 = -0.2 #[mA] or [V]
	Source_stop_2 = -2 #[mA] or [V]
	waveform_2 = "DC" #pulsed or DC
	pulse_delay_2 = 20e-6 #delay between pulses [s] (pulsed mode only)
	pulse_width_2 = 1e-6 #width of pulses [s] (pulsed mode only)
	protection_voltage_2 = 4 #[V]
	protection_current_2 = 0.1 #[A]
	### Channel 3 Source - K2520, K2604B, B2902A, or LDC3908
	Source_3 = 'OFF'
	Source_3_mode = 'Current' #'Current' or 'Voltage'
	Source_3_channel = 2 #1-8, 'A' or 'B', for two channel sources only (ignored for one channel)
	Source_start_3 = 10 #[mA] or [V]
	Source_step_3 = 10 #[mA] or [V]
	Source_stop_3 = 20 #[mA] or [V]
	waveform_3 = "DC" #pulsed or DC
	pulse_delay_3 = 20e-6 #delay between pulses [s] (pulsed mode only)
	pulse_width_3 = 1e-6 #width of pulses [s] (pulsed mode only)
	protection_voltage_3 = 4 #[V]
	protection_current_3 = 0.1 #[A]
	### Channel 4 Source - OFF, K2520, K2604B, or B2902A
	Source_4 = 'OFF'
	Source_4_mode = 'Voltage' #'Current' or 'Voltage'
	Source_4_channel = 1 #1-8, 'A' or 'B', for two channel sources only (ignored for one channel)
	Source_start_4 = -1 #[mA] or [V]
	Source_step_4 = -1 #[mA] or [V]
	Source_stop_4 = -2 #[mA] or [V]
	waveform_4 = "DC" #pulsed or DC
	pulse_delay_4 = 20e-6 #delay between pulses [s] (pulsed mode only)
	pulse_width_4 = 1e-6 #width of pulses [s] (pulsed mode only)
	protection_voltage_4 = 4 #[V]
	protection_current_4 = 0.1 #[A]
	### Channel 5 Source - K2520, K2604B, B2902A, or LDC3908
	Source_5 = 'OFF'
	Source_5_mode = 'Current' #'Current' or 'Voltage'
	Source_5_channel = 2 #1-8, 'A' or 'B', for two channel sources only (ignored for one channel)
	Source_start_5 = 10 #[mA] or [V]
	Source_step_5 = 10 #[mA] or [V]
	Source_stop_5 = 20 #[mA] or [V]
	waveform_5 = "DC" #pulsed or DC
	pulse_delay_5 = 20e-6 #delay between pulses [s] (pulsed mode only)
	pulse_width_5 = 1e-6 #width of pulses [s] (pulsed mode only)
	protection_voltage_5 = 4 #[V]
	protection_current_5 = 0.1 #[A]
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
	### Connect to Lab Equipment
	Source_1_mode = Source_1_mode.capitalize()
	Source_2_mode = Source_2_mode.capitalize()
	Source_3_mode = Source_3_mode.capitalize()
	Source_4_mode = Source_4_mode.capitalize()
	Source_5_mode = Source_5_mode.capitalize()
	# Sources
	Source_inst_1 = connect_to_GPIB(Source_1,[Source_1_mode,Source_1_channel,protection_voltage_1,protection_current_1,waveform_1,pulse_delay_1,pulse_width_1])
	Source_inst_2 = connect_to_GPIB(Source_2,[Source_2_mode,Source_2_channel,protection_voltage_2,protection_current_1,waveform_2,pulse_delay_2,pulse_width_2])
	Source_inst_3 = connect_to_GPIB(Source_3,[Source_3_mode,Source_3_channel,protection_voltage_3,protection_current_1,waveform_3,pulse_delay_3,pulse_width_3])
	Source_inst_4 = connect_to_GPIB(Source_4,[Source_4_mode,Source_4_channel,protection_voltage_4,protection_current_1,waveform_4,pulse_delay_4,pulse_width_4])
	Source_inst_5 = connect_to_GPIB(Source_5,[Source_5_mode,Source_5_channel,protection_voltage_5,protection_current_1,waveform_5,pulse_delay_5,pulse_width_5])
	# Spectrum Analyzer
	spectrum_analyzer_inst = connect_to_GPIB(spectrum_analyzer)
	### Convert from mA to A
	if Source_1_mode == 'Current':
		Source_step_1 = Source_step_1*1e-3
		Source_start_1 = Source_start_1*1e-3
		Source_stop_1 = Source_stop_1*1e-3
	if Source_2_mode == 'Current':
		Source_step_2 = Source_step_2*1e-3
		Source_start_2 = Source_start_2*1e-3
		Source_stop_2 = Source_stop_2*1e-3
	if Source_3_mode == 'Current':
		Source_step_3 = Source_step_3*1e-3
		Source_start_3 = Source_start_3*1e-3
		Source_stop_3 = Source_stop_3*1e-3
	if Source_4_mode == 'Current':
		Source_step_4 = Source_step_4*1e-3
		Source_start_4 = Source_start_4*1e-3
		Source_stop_4 = Source_stop_4*1e-3
	if Source_5_mode == 'Current':
		Source_step_5 = Source_step_5*1e-3
		Source_start_5 = Source_start_5*1e-3
		Source_stop_5 = Source_stop_5*1e-3
	### Sweep current and collect data
	sweep_num = 0
	if Source_1.lower() == 'off':
		raise Exception(colour.red+" Source #1 must be enabled"+colour.end)
	Source_input_list_1 = [x for x in np.arange(Source_start_1,Source_stop_1+Source_step_1/2,Source_step_1)]
	if Source_2.lower() == 'off':
		Source_input_list_2 = [0]
	else:
		Source_input_list_2 = [x for x in np.arange(Source_start_2,Source_stop_2+Source_step_2/2,Source_step_2)]
	if Source_3.lower() == 'off':
		Source_input_list_3 = [0]
	else:
		Source_input_list_3 = [x for x in np.arange(Source_start_3,Source_stop_3+Source_step_3/2,Source_step_3)]
	if Source_4.lower() == 'off':
		Source_input_list_4 = [0]
	else:
		Source_input_list_4 = [x for x in np.arange(Source_start_4,Source_stop_4+Source_step_4/2,Source_step_4)]
	if Source_5.lower() == 'off':
		Source_input_list_5 = [0]
	else:
		Source_input_list_5 = [x for x in np.arange(Source_start_5,Source_stop_5+Source_step_5/2,Source_step_5)]
	num_sweeps = len(Source_input_list_1)*len(Source_input_list_2)*len(Source_input_list_3)*len(Source_input_list_4)*len(Source_input_list_5)
	for i5 in range(len(Source_input_list_5)):
		if Source_5.lower() != 'off':
			if i5 > 0:
				Source_inst_5.set_value(Source_input_list_5[i5])
			else:
				Source_inst_5.safe_turn_on(Source_input_list_5[i5])
			if Source_5_mode == 'Current':
				print(" Source #5 = "+str(round(Source_input_list_5[i5]*1e3))+" mA")
			else:
				print(" Source #5 = "+str(round(Source_input_list_5[i5]*10)/10)+" V")
		for i4 in range(len(Source_input_list_4)):
			if Source_4.lower() != 'off':
				if i4 > 0:
					Source_inst_4.set_value(Source_input_list_4[i4])
				else:
					Source_inst_4.safe_turn_on(Source_input_list_4[i4])
				if Source_4_mode == 'Current':
					print(" Source #4 = "+str(round(Source_input_list_4[i4]*1e3))+" mA")
				else:
					print(" Source #4 = "+str(round(Source_input_list_4[i4]*10)/10)+" V")
			for i3 in range(len(Source_input_list_3)):
				if Source_3.lower() != 'off':
					if i3 > 0:
						Source_inst_3.set_value(Source_input_list_3[i3])
					else:
						Source_inst_3.safe_turn_on(Source_input_list_3[i3])
					if Source_3_mode == 'Current':
						print(" Source #3 = "+str(round(Source_input_list_3[i3]*1e3))+" mA")
					else:
						print(" Source #3 = "+str(round(Source_input_list_3[i3]*10)/10)+" V")
				for i2 in range(len(Source_input_list_2)):
					if Source_2.lower() != 'off':
						if i2 > 0:
							Source_inst_2.set_value(Source_input_list_2[i2])
						else:
							Source_inst_2.safe_turn_on(Source_input_list_2[i2])
						if Source_2_mode == 'Current':
							print(" Source #2 = "+str(round(Source_input_list_2[i2]*1e3))+" mA")
						else:
							print(" Source #2 = "+str(round(Source_input_list_2[i2]*10)/10)+" V")
					for i1 in range(len(Source_input_list_1)):
						if Source_1_mode == 'Current':
							print(" Source #1 = "+str(round(Source_input_list_1[i1]*1e3))+" mA")
						else:
							print(" Source #1 = "+str(round(Source_input_list_1[i1]*10)/10)+" V")
						if i1 > 0:
							Source_inst_1.set_value(Source_input_list_1[i1])
						else:
							Source_inst_1.safe_turn_on(Source_input_list_1[i1])
						# Delay to let sources stabilize
						time.sleep(0.1)
						### Collect Spectrum
						sweep_num += 1
						print(" Spectrum Analyzer sweeping "+str(sweep_num)+"/"+str(num_sweeps)+"...")
						spectrum_analyzer_inst.sweep(spectrum_analyzer_channel)
						x_data, power = spectrum_analyzer_inst.capture(spectrum_analyzer_channel)
						if adjust_center and max(power)>-50:
							spectrum_analyzer_inst.peak_to_center()
						### Name Output Files
						scan_name = device_name
						if Source_5.lower() != 'off':
							if Source_5_mode == 'Current':
								scan_name += '_'+str(round(Source_input_list_5[i5]*1e3))+'mA'
							elif Source_5_mode == 'Voltage':
								scan_name += '_'+str(round(Source_input_list_5[i5]*10)/10)+'V'
						if Source_4.lower() != 'off':
							if Source_4_mode == 'Current':
								scan_name += '_'+str(round(Source_input_list_4[i4]*1e3))+'mA'
							elif Source_4_mode == 'Voltage':
								scan_name += '_'+str(round(Source_input_list_4[i4]*10)/10)+'V'
						if Source_3.lower() != 'off':
							if Source_3_mode == 'Current':
								scan_name += '_'+str(round(Source_input_list_3[i3]*1e3))+'mA'
							elif Source_3_mode == 'Voltage':
								scan_name += '_'+str(round(Source_input_list_3[i3]*10)/10)+'V'
						if Source_2.lower() != 'off':
							if Source_2_mode == 'Current':
								scan_name += '_'+str(round(Source_input_list_2[i2]*1e3))+'mA'
							elif Source_2_mode == 'Voltage':
								scan_name += '_'+str(round(Source_input_list_2[i2]*10)/10)+'V'
						if Source_1.lower() != 'off':
							if Source_1_mode == 'Current':
								scan_name += '_'+str(round(Source_input_list_1[i1]*1e3))+'mA'
							elif Source_1_mode == 'Voltage':
								scan_name += '_'+str(round(Source_input_list_1[i1]*10)/10)+'V'
						[csv_location, png_location, scan_name] = get_file_locations(save_data, save_fig, characterization_directory, 'Spectrum', scan_name)
						#Save data
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
								fig = plot_spectrum(scan_name, x_data, power,x_is_freq=True, show_SMSR=show_SMSR, show_FWHM=show_FWHM)[0]
							else:
								fig = plot_spectrum(scan_name, x_data, power, show_SMSR=show_SMSR, show_FWHM=show_FWHM)[0]
							if save_fig:
								fig.savefig(png_location,bbox_inches='tight')
								print(" Figure saved to",png_location)
							if display_fig:
								print(" Displaying figure. Close figure to resume.")
								plt.show()
							else:
								plt.close()
						print("")
					Source_inst_1.safe_turn_off()
				if Source_2.lower() != 'off':
					Source_inst_2.safe_turn_off()
			if Source_3.lower() != 'off':
				Source_inst_3.safe_turn_off()
		if Source_4.lower() != 'off':
			Source_inst_4.safe_turn_off()
	if Source_5.lower() != 'off':
		Source_inst_5.safe_turn_off()
	print(" Disconnected from instruments")
	
if __name__ == "__main__":
	if len(sys.argv)-1 == 0:
		#No input
		Spectrum_Analyzer_Capture_Source_Sweep("Test")
	elif len(sys.argv)-1 == 1:
		#One input (device_name)
		Spectrum_Analyzer_Capture_Source_Sweep(sys.argv[1])
	else:
		raise Exception(colour.red+" Spectrum_Analyzer_Capture_Source_Sweep needs either zero or one argument"+colour.end)
