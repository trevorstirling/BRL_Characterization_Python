#########################################################################
# Script to take LIV (luminosity and voltage as a function of current)	#
# using up to five current/voltage sources (various models)				#
# -Call with no arguments  LIV() to display LIV only					#
# -Call with one argument LIV(device_name) to save data and figure		#
# Data is saved as														#
# device_source5value_source4value_source3value_source2value.txt 		#
#																		#
# Author: Trevor Stirling												#
# Date: July 6, 2023													#
#########################################################################

#TODO: Test K2520 power meter with other source (see commented out code below)
#	   Two detector LIV causing issues - Newport PM replies power = '' - I think this was an issue with the USB cable and is now fixed?

import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import time
import math
from common_functions import colour,connect_to_PM,connect_to_GPIB,get_file_locations,plot_LIV

def LIV(device_name):
	##########################################
	####         Define Variables         ####
	##########################################
	characterization_directory = os.path.join('..','Data')
	display_before_save = True #True/False
	#Plot as current density
	plot_current_density = True
	ask_user_for_device_dimensions = 'Width_Only' #True/False/Width_Only For current density calculation
	K2520_internal_sweep = True #Much faster, only turn off for debugging
	device_length = 0.5 #length of device [mm], ignored if plot_current_density = False or ask_user_for_device_dimensions = True
	injection_width = 4.1 #average via width [um], ignored if plot_current_density = False ask_user_for_device_dimensions = True
	### Power Meter - K2520, or Newport
	Power_meter = 'K2520'
	Power_meter_channel_1 = 'A' #A or B, for two channel Newport only (ignored for one channel)
	Power_meter_channel_2 = 'OFF' #A, B, or OFF for two channel Newport only (ignored for one channel)
	### Channel 1 Source - OFF, K2520, K2604B, B2902A, or LDC3908
	Source_1 = 'K2520'
	Source_1_mode = 'Current' #'Current' or 'Voltage'
	Source_1_channel = 1 #1-16, 'A' or 'B', for two channel sources only (ignored for one channel)
	Source_start_1 = 1 #[mA] or [V]
	Source_step_1 = 1 #[mA] or [V]
	Source_stop_1 = 150 #[mA] or [V]
	waveform_1 = "pulsed" #pulsed or DC
	pulse_delay_1 = 160e-6 #delay between pulses [s] (pulsed mode only)
	pulse_width_1 = 8e-6 #width of pulses [s] (pulsed mode only)
	protection_voltage_1 = 4 #[V]
	protection_current_1 = 0.1 #[A]
	### Channel 2 Source - OFF, K2520, K2604B, B2902A, or LDC3908
	Source_2 = 'OFF'
	Source_2_mode = 'Voltage' #'Current' or 'Voltage'
	Source_2_channel = 2 #1-16, 'A' or 'B', for two channel sources only (ignored for one channel)
	Source_start_2 = -0.6 #[mA] or [V]
	Source_step_2 = -0.1 #[mA] or [V]
	Source_stop_2 = -4 #[mA] or [V]
	waveform_2 = "DC" #pulsed or DC
	pulse_delay_2 = 20e-6 #delay between pulses [s] (pulsed mode only)
	pulse_width_2 = 1e-6 #width of pulses [s] (pulsed mode only)
	protection_voltage_2 = 4 #[V]
	protection_current_2 = 0.1 #[A]
	### Channel 3 Source - OFF, K2520, K2604B, B2902A, or LDC3908
	Source_3 = 'OFF'
	Source_3_mode = 'Current' #'Current' or 'Voltage'
	Source_3_channel = 2 #1-16, 'A' or 'B', for two channel sources only (ignored for one channel)
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
	Source_4_channel = 1 #1-16, 'A' or 'B', for two channel sources only (ignored for one channel)
	Source_start_4 = -1 #[mA] or [V]
	Source_step_4 = -1 #[mA] or [V]
	Source_stop_4 = -2 #[mA] or [V]
	waveform_4 = "DC" #pulsed or DC
	pulse_delay_4 = 20e-6 #delay between pulses [s] (pulsed mode only)
	pulse_width_4 = 1e-6 #width of pulses [s] (pulsed mode only)
	protection_voltage_4 = 4 #[V]
	protection_current_4 = 0.1 #[A]
	### Channel 5 Source - OFF, K2520, K2604B, B2902A, or LDC3908
	Source_5 = 'OFF'
	Source_5_mode = 'Current' #'Current' or 'Voltage'
	Source_5_channel = 2 #1-16, 'A' or 'B', for two channel sources only (ignored for one channel)
	Source_start_5 = 10 #[mA] or [V]
	Source_step_5 = 10 #[mA] or [V]
	Source_stop_5 = 20 #[mA] or [V]
	waveform_5 = "DC" #pulsed or DC
	pulse_delay_5 = 20e-6 #delay between pulses [s] (pulsed mode only)
	pulse_width_5 = 1e-6 #width of pulses [s] (pulsed mode only)
	protection_voltage_5 = 4 #[V]
	protection_current_5 = 0.1 #[A]
	### Enable/disable pausing for mode profile measurement - only works with Newport detector
	pausing_enabled = False #if enabled, will pause whenever source 1 is set to a multiple of pause_interval
	pause_interval = 10 #[mA] or [V]
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
	if waveform_1 == 'pulsed':
		device_name += '_pulsed'
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
	# Power Meter
	two_facet_LIV = False
	if Power_meter == 'K2520':
		# if Source_1 == 'K2520':
		# 	PM_inst = Source_inst_1
		# elif Source_2 == 'K2520':
		# 	PM_inst = Source_inst_2
		# elif Source_3 == 'K2520':
		# 	PM_inst = Source_inst_3
		# elif Source_4 == 'K2520':
		# 	PM_inst = Source_inst_4
		# elif Source_5 == 'K2520':
		# 	PM_inst = Source_inst_5
		# else:
		# 	input(colour.yellow+" The K2520 must be enabled to act as a power meter. As it is not being used as a source, it will be biased to 0 mA. Press any key to continue..."+colour.end)
		#	PM_inst = connect_to_GPIB(Power_meter,["Current",1,4,0.1,"DC",20e-5,1e-6])
		#	PM_inst.set_value(0)
		#	PM_inst.set_output('ON')
		if Source_1 != 'K2520':
			raise Exception(colour.red+" The K2520 power meter can only be used with the K2520 source as source #1 (not the "+Source_1+")"+colour.end)
		else:
			PM_inst = Source_inst_1
	elif Power_meter == 'Newport':
		if waveform_1.lower() == 'pulsed':
			raise Exception(colour.red+" The K2520 power meter must be used for pulsed mode"+colour.end)
		from Interfaces import Newport_PM_Interface
		PM_inst = connect_to_PM(Power_meter_channel_1)
		if Power_meter_channel_2 == 'A' or Power_meter_channel_2 == 'B':
			two_facet_LIV = True
	else:
		raise Exception(colour.red+" "+Power_meter," is not set up as a power meter"+colour.end)
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
	if ask_user_for_device_dimensions==True:
		device_length = float(input(colour.yellow+" Enter the device length in mm:"+colour.end))
		injection_width = float(input(colour.yellow+" Enter the device width in um:"+colour.end))
	elif ask_user_for_device_dimensions == 'Width_Only':
		injection_width = float(input(colour.yellow+" Enter the device width in um:"+colour.end))
	current_area = device_length/10*injection_width/10000
	### Sweep values and collect data
	sweep_num = 0
	if Source_1_mode != 'Current':
		raise Exception(colour.red+" Source #1 must be in current mode"+colour.end)
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
	num_sweeps = len(Source_input_list_2)*len(Source_input_list_3)*len(Source_input_list_4)*len(Source_input_list_5)
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
					### Inner sweep
					sweep_num += 1
					print(" Source #1 sweeping "+str(sweep_num)+"/"+str(num_sweeps)+"...")
					# Delay to let currents stabilize
					time.sleep(0.1)
					if Power_meter == 'K2520' and K2520_internal_sweep and Source_1 == 'K2520':
						Source_input_list_1, voltage_list, power_list = Source_inst_1.sweep_current(Source_start_1, Source_step_1, Source_stop_1)
						if waveform_1.capitalize() == 'Pulsed':
							Source_inst_1.enable_init_continuous() #set continuous initiating again after sweep
						### Remove data points where detector clipped
						if max(power_list)>1.5e38:
							last_point = power_list.index(next(i for i in power_list if i>1.5e38))
							if last_point == 0:
								raise Exception(colour.red+" Detector was maxed out from the first data point"+colour.end)
							Source_input_list_1 = Source_input_list_1[:last_point] #[A]
							voltage_list = voltage_list[:last_point] #[V]
							power_list = power_list[:last_point] #[A]
						power_list_2 = False
					else:
						Source_input_list_1 = [x for x in np.arange(Source_start_1,Source_stop_1+Source_step_1/2,Source_step_1)] #[A]
						voltage_list = [0]*len(Source_input_list_1) #[V]
						power_list = [0]*len(Source_input_list_1) #[W]
						if two_facet_LIV:
							power_list_2 = [0]*len(Source_input_list_1) #[W]
						else:
							power_list_2 = False
						for i in range(len(Source_input_list_1)):
							if i > 0:
								Source_inst_1.set_value(Source_input_list_1[i])
							else:
								Source_inst_1.safe_turn_on(Source_input_list_1[i])
							if i == 0:
								Source_inst_1.set_output('ON')
							#delay for power meter to stabilize
							time.sleep(0.2)
							voltage_list[i] = Source_inst_1.read_value('Voltage')
							power_list[i] = PM_inst.read_power()
							if two_facet_LIV:
								PM_inst.set_channel(Power_meter_channel_2)
								time.sleep(0.1)
								power_list_2[i] = PM_inst.read_power()
								PM_inst.set_channel(Power_meter_channel_1)
								time.sleep(0.1)
							if i>0 and round(Source_input_list_1[i]*1e3)%pause_interval == 0:
								if pausing_enabled:
									input(colour.green+" "+str(round(Source_input_list_1[i]*1e3))+" mA: Pausing for mode profile capture. Press any key to continue..."+colour.end)
						Source_inst_1.safe_turn_off()

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
					[csv_location, png_location, scan_name] = get_file_locations(save_data, save_fig, characterization_directory, 'LIV', scan_name)
					### Save data to file
					if save_data:
						if two_facet_LIV:
							full_data = np.zeros((len(Source_input_list_1), 4))
							full_data[:,3] = power_list_2
						else:
							full_data = np.zeros((len(Source_input_list_1), 3))
						full_data[:,0] = Source_input_list_1
						full_data[:,1] = voltage_list
						full_data[:,2] = power_list
						if two_facet_LIV:
							np.savetxt(csv_location, full_data, delimiter=',', header='Current [A], Voltage [V], Power Right [W], Power Left [W]', comments='')
						else:
							np.savetxt(csv_location, full_data, delimiter=',', header='Current [A], Voltage [V], Power [W]', comments='')
						print(" Data saved to",csv_location)
					### Plot data
					if display_fig or save_fig:
						fig = plot_LIV(scan_name, power_list, Source_input_list_1, voltage_list, plot_current_density=plot_current_density, current_area=current_area, power2=power_list_2)[0]
						if save_fig:
							fig.savefig(png_location,bbox_inches='tight')
							print(" Figure saved to",png_location)
						if display_fig:
							print(" Displaying figure. Close figure to resume.")
							plt.show()
						else:
							plt.close()
					print("")
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
		LIV("Test")
	elif len(sys.argv)-1 == 1:
		#One input (device_name)
		LIV(sys.argv[1])
	else:
		raise Exception(colour.red+" LIV needs either zero or one argument"+colour.end)
