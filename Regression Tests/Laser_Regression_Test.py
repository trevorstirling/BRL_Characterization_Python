#########################################################################
# Script to test laser code works properly								#
#																		#
# Author: Trevor Stirling												#
# Date: Nov 14, 2022													#
#########################################################################

import sys
from common_functions import colour,connect_to_GPIB

def Spectrum_Analyzer_Regression_Test(laser):
	input(colour.yellow+colour.alert+" WARNING: This will enable the laser with a maximum power of 3 mA. Ensure the laser output is blocked, then press any key to continue..."+colour.end)
	### Connect to Spectrum Analyzer
	laser_inst = connect_to_GPIB(laser)
	test_count = 0
	pass_count = 0
	##########################################
	####           Start Tests            ####
	##########################################
	#Power Test
	test_count += 1
	value_1_set = 1
	value_2_set = 3
	laser_inst.set_power(value_1_set)
	laser_inst.set_output('ON')
	value_1 = laser_inst.read_value('Power')
	laser_inst.set_power(value_2_set)
	value_2 = laser_inst.read_value('Power')
	laser_inst.set_output('OFF')
	if round(value_1) == value_1_set and round(value_2) == value_2_set:
		print(colour.green+" Power Test: PASSED"+colour.end)
		pass_count += 1
	else:
		print(colour.red+" Power Test: FAILED"+colour.end)
	#Wavelength Test
	test_count += 1
	value_1_set = 1540
	value_2_set = 1560
	laser_inst.set_wavelength(value_1_set)
	value_1 = laser_inst.read_value('Wavelength')
	laser_inst.set_wavelength(value_2_set)
	value_2 = laser_inst.read_value('Wavelength')
	if round(value_1) == value_1_set and round(value_2) == value_2_set:
		print(colour.green+" Wavelength Test: PASSED"+colour.end)
		pass_count += 1
	else:
		print(colour.red+" Wavelength Test: FAILED"+colour.end)
	
	### Disconnect
	print(" Disconnected from Laser")
	if pass_count == test_count:
		print(colour.green+" Passed all tests"+colour.end)
	else:
		print(colour.red+" Passed "+str(pass_count)+"/"+str(test_count)+" tests"+colour.end)
	
if __name__ == "__main__":
	if len(sys.argv)-1 == 1:
		#One input (spectrum_analyzer)
		Spectrum_Analyzer_Regression_Test(sys.argv[1])
	else:
		raise Exception(colour.red+colour.alert+" Spectrum_Analyzer_Regression_Test needs one argument"+colour.end)
