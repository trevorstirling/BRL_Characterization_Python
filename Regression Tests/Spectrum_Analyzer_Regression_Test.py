#########################################################################
# Script to test spectrum analyzer code works properly                  #
#                                                                       #
# Author: Trevor Stirling                                               #
# Date: Sept 26, 2023                                                   #
#########################################################################

import sys
import time
import numpy as np
from common_functions import colour,connect_to_GPIB

def Spectrum_Analyzer_Regression_Test(spectrum_analyzer):
	### Connect to Spectrum Analyzer
	spectrum_analyzer_inst = connect_to_GPIB(spectrum_analyzer)
	#spectrum_analyzer_inst.initialize()
	test_count = 0
	pass_count = 0
	if spectrum_analyzer_inst.isOSA:
		test_channel = 'A'
	else:
		test_channel = '1'
	##########################################
	####           Start Tests            ####
	##########################################
	#Reference Level Test
	test_count += 1
	value_1_set = 10
	value_2_set = -30
	spectrum_analyzer_inst.set_ref_level(value_1_set)
	value_1 = spectrum_analyzer_inst.read_value('Reference Level')
	spectrum_analyzer_inst.set_ref_level(value_2_set)
	value_2 = spectrum_analyzer_inst.read_value('Reference Level')
	if round(value_1) == value_1_set and round(value_2) == value_2_set:
		print(colour.green+" Reference Level Test: PASSED"+colour.end)
		pass_count += 1
	else:
		print(colour.red+" Reference Level Test results "+str(value_1)+", "+str(value_2)+colour.end)
		print(colour.red+" Reference Level Test: FAILED"+colour.end)
	#Span Test
	test_count += 1
	if spectrum_analyzer_inst.isOSA:
		value_1_set = 20
		value_2_set = 6
	else:
		value_1_set = 1e9
		value_2_set = 10e9
	spectrum_analyzer_inst.set_span(value_1_set)
	value_1 = spectrum_analyzer_inst.read_value('Span')
	spectrum_analyzer_inst.set_span(value_2_set)
	value_2 = spectrum_analyzer_inst.read_value('Span')
	if round(value_1) == value_1_set and round(value_2) == value_2_set:
		print(colour.green+" Span Test: PASSED"+colour.end)
		pass_count += 1
	else:
		print(colour.red+" Span Test results "+str(value_1)+", "+str(value_2)+colour.end)
		print(colour.red+" Span Test: FAILED"+colour.end)
	if spectrum_analyzer_inst.isOSA:
		#Wavelength Test
		test_count += 1
		value_1_set = 1672
		value_2_set = 780
		spectrum_analyzer_inst.set_wavelength(value_1_set)
		value_1 = spectrum_analyzer_inst.read_value('Wavelength')
		spectrum_analyzer_inst.set_wavelength(value_2_set)
		value_2 = spectrum_analyzer_inst.read_value('Wavelength')
		if round(value_1) == value_1_set and round(value_2) == value_2_set:
			print(colour.green+" Wavelength Test: PASSED"+colour.end)
			pass_count += 1
		else:
			print(colour.red+" Wavelength Test results "+str(value_1)+", "+str(value_2)+colour.end)
			print(colour.red+" Wavelength Test: FAILED"+colour.end)
	else:
		#Frequency Test
		test_count += 1
		value_1_set = 10e9
		value_2_set = 14e9
		spectrum_analyzer_inst.set_frequency(value_1_set)
		value_1 = spectrum_analyzer_inst.read_value('Frequency')
		spectrum_analyzer_inst.set_frequency(value_2_set)
		value_2 = spectrum_analyzer_inst.read_value('Frequency')
		if round(value_1) == value_1_set and round(value_2) == value_2_set:
			print(colour.green+" Frequency Test: PASSED"+colour.end)
			pass_count += 1
		else:
			print(colour.red+" Frequency Test results "+str(value_1)+", "+str(value_2)+colour.end)
			print(colour.red+" Frequency Test: FAILED"+colour.end)
	#Y Scale Test
	test_count += 1
	value_1_set = 2
	value_2_set = 10
	spectrum_analyzer_inst.set_y_scale(value_1_set)
	value_1 = spectrum_analyzer_inst.read_value('Y Scale')
	spectrum_analyzer_inst.set_y_scale(value_2_set)
	value_2 = spectrum_analyzer_inst.read_value('Y Scale')
	if round(value_1) == value_1_set and round(value_2) == value_2_set:
		print(colour.green+" Y Scale Test: PASSED"+colour.end)
		pass_count += 1
	else:
		print(colour.red+" Y Scale Test results "+str(value_1)+", "+str(value_2)+colour.end)
		print(colour.red+" Y Scale Test: FAILED"+colour.end)
	#Resolution Bandwidth Test
	test_count += 1
	if spectrum_analyzer_inst.isOSA:
		value_1_set = 1.0
		value_2_set = 0.1
	else:
		value_1_set = 3e6
		value_2_set = 100e3
	spectrum_analyzer_inst.set_rbw(value_1_set)
	value_1 = spectrum_analyzer_inst.read_value('RBW')
	spectrum_analyzer_inst.set_rbw(value_2_set)
	value_2 = spectrum_analyzer_inst.read_value('RBW')
	if round(value_1,1) == round(value_1_set,1) and round(value_2,1) == round(value_2_set,1):
		print(colour.green+" Resolution Bandwidth Test: PASSED"+colour.end)
		pass_count += 1
	else:
		print(colour.red+" Resolution Bandwidth Test results "+str(value_1)+", "+str(value_2)+colour.end)
		print(colour.red+" Resolution Bandwidth Test: FAILED"+colour.end)
	test_count += 1
	if spectrum_analyzer == 'AQ6317B' or spectrum_analyzer == 'AQ6374':
		#Sensitivity Test - for AQ6317B or AQ6374 only
		value_1_set = 'HIGH1'
		value_2_set = 'MID'
		spectrum_analyzer_inst.set_sensitivity(value_1_set)
		value_1 = spectrum_analyzer_inst.read_value('Sensitivity')
		spectrum_analyzer_inst.set_sensitivity(value_2_set)
		value_2 = spectrum_analyzer_inst.read_value('Sensitivity')
		if value_1 == value_1_set and value_2 == value_2_set:
			print(colour.green+" Sensitivity Test: PASSED"+colour.end)
			pass_count += 1
		else:
			print(colour.red+" Sensitivity Test results "+str(value_1)+", "+str(value_2)+colour.end)
			print(colour.red+" Sensitivity Test: FAILED"+colour.end)
	else:
		#VBW Test
		if spectrum_analyzer_inst.isOSA:
			value_1_set = 10
			value_2_set = 2000
		else:
			value_1_set = 1000
			value_2_set = 3e6
		spectrum_analyzer_inst.set_vbw(value_1_set)
		value_1 = spectrum_analyzer_inst.read_value('VBW')
		spectrum_analyzer_inst.set_vbw(value_2_set)
		value_2 = spectrum_analyzer_inst.read_value('VBW')
		if value_1 == value_1_set and value_2 == value_2_set:
			print(colour.green+" VBW Test: PASSED"+colour.end)
			pass_count += 1
		else:
			print(colour.red+" VBW Test results "+str(value_1)+", "+str(value_2)+colour.end)
			print(colour.red+" VBW Test: FAILED"+colour.end)
	#Sweep Test
	test_count += 1
	start_time = time.time()
	spectrum_analyzer_inst.sweep(test_channel)
	sweep_time = time.time()-start_time #[s]
	value_1 = spectrum_analyzer_inst.is_sweeping()
	spectrum_analyzer_inst.sweep_continuous(1)
	value_2 = spectrum_analyzer_inst.is_sweeping()
	time.sleep(sweep_time*1.5)
	value_3 = spectrum_analyzer_inst.is_sweeping()
	spectrum_analyzer_inst.sweep_continuous(0)
	spectrum_analyzer_inst.wait_for_sweeping()
	if value_1 == False and value_2 == True and value_3 == True:
		print(colour.green+" Sweep Test: PASSED"+colour.end)
		pass_count += 1
	else:
		print(colour.red+" Sweep Test results "+str(value_1)+", "+str(value_2)+", "+str(value_3)+colour.end)
		print(colour.red+" Sweep Test: FAILED"+colour.end)
	#Capture Test
	test_count += 1
	[x_data, power] = spectrum_analyzer_inst.capture(test_channel)
	if spectrum_analyzer_inst.isOSA:
		if max(x_data) >= 600 and max(x_data) <= 1750 and max(power) <= 20 and max(power) >= -210:
			print(colour.green+" Capture Test: PASSED"+colour.end)
			pass_count += 1
		else:
			print(colour.red+" Capture Test results "+str(max(x_data))+", "+str(max(power))+colour.end)
			print(colour.red+" Capture Test: FAILED"+colour.end)
	else:
		if max(x_data) >= 9e-6 and max(x_data) <= 26.5 and max(power) <=55 and max(power) >= -150:
			print(colour.green+" Capture Test: PASSED"+colour.end)
			pass_count += 1
		else:
			print(colour.red+" Capture Test results "+str(max(x_data))+", "+str(max(power))+colour.end)
			print(colour.red+" Capture Test: FAILED"+colour.end)
	#Peak To Center Test
	test_count += 1
	if spectrum_analyzer_inst.isOSA:
		spectrum_analyzer_inst.set_rbw(0.1)
		actual_peak = x_data[np.argmax(power)] #relies on capture test run previously
	else:
		spectrum_analyzer_inst.set_rbw(100e3)
		actual_peak = x_data[np.argmax(power)]*1e9 #relies on capture test run previously
	if spectrum_analyzer_inst.isOSA:
		spectrum_analyzer_inst.set_wavelength(actual_peak+1)
		value_1 = spectrum_analyzer_inst.read_value('Wavelength')
		spectrum_analyzer_inst.peak_to_center()
		value_2 = spectrum_analyzer_inst.read_value('Wavelength')
		if round(value_1,1) == round(actual_peak+1,1) and round(value_2,1) == round(actual_peak,1):
			print(colour.green+" Peak To Center Test: PASSED"+colour.end)
			pass_count += 1
		else:
			print(colour.red+" Peak To Center Test results "+str(value_1)+", "+str(value_2)+colour.end)
			print(colour.red+" Peak To Center Test: FAILED"+colour.end)
	else:
		spectrum_analyzer_inst.set_frequency(actual_peak+0.1e9)
		value_1 = spectrum_analyzer_inst.read_value('Frequency')
		spectrum_analyzer_inst.peak_to_center()
		value_2 = spectrum_analyzer_inst.read_value('Frequency')
		if round(value_1/1e9,1) == round((actual_peak+0.1e9)/1e9,1) and round(value_2/1e9,1) == round(actual_peak/1e9,1):
			print(colour.green+" Peak To Center Test: PASSED"+colour.end)
			pass_count += 1
		else:
			print(colour.red+" Peak To Center Test results "+str(value_1)+", "+str(value_2)+colour.end)
			print(colour.red+" Peak To Center Test: FAILED"+colour.end)
	
	### Disconnect
	print(" Disconnected from Spectrum Analyzer")
	if pass_count == test_count:
		print(colour.green+" Passed all tests"+colour.end)
	else:
		print(colour.red+" Passed "+str(pass_count)+"/"+str(test_count)+" tests"+colour.end)
	
if __name__ == "__main__":
	if len(sys.argv)-1 == 2:
		#Two inputs (spectrum_analyzer)
		Spectrum_Analyzer_Regression_Test(sys.argv[1])
	else:
		raise Exception(colour.red+colour.alert+" Spectrum_Analyzer_Regression_Test needs one arguments (device name)"+colour.end)
