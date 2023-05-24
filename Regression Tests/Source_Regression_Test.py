#########################################################################
# Script to test current/voltage source code works properly				#
#																		#
# Author: Trevor Stirling												#
# Date: Nov 14, 2022													#
#########################################################################

import sys
from common_functions import colour,connect_to_GPIB

def Source_Regression_Test(device):
	input(colour.yellow+colour.alert+" WARNING: This will send up to 100 mA from the source. Ensure no device is probed, then press any key to continue..."+colour.end)
	### Connect to Source
	source_mode = 'Current'
	source_inst = connect_to_GPIB(device,[source_mode,1,4,0.1,"DC",20e-6,1e-6])
	test_count = 0
	pass_count = 0
	if device == 'B2902A' or device == 'K2604B':
		has_voltage_mode = True
	else:
		has_voltage_mode = False
	##########################################
	####           Start Tests            ####
	##########################################
	#Set Current Test
	test_count += 1
	value_1_set = 10*1e-3
	value_2_set = 25*1e-3
	if has_voltage_mode:
		source_inst.set_value(value_1_set,'Current')
	else:
		source_inst.set_value(value_1_set)
	value_1 = source_inst.read_setting()
	if has_voltage_mode:
		source_inst.set_value(value_2_set,'Current')
	else:
		source_inst.set_value(value_2_set)
	value_2 = source_inst.read_setting()
	if round(value_1*1e3) == round(value_1_set*1e3) and round(value_2*1e3) == round(value_2_set*1e3):
		print(colour.green+" Set Current Test: PASSED"+colour.end)
		pass_count += 1
	else:
		print(colour.red+" Set Current Test: FAILED"+colour.end)
	#Get Mode Test
	test_count += 1
	if source_inst.get_mode() == source_mode:
		print(colour.green+" Get Mode Test: PASSED"+colour.end)
		pass_count += 1
	else:
		print(colour.red+" Get Mode Test: FAILED"+colour.end)
	#Safe Turn On/Off Test
	test_count += 1
	turn_on_value = 100*1e-3
	input(colour.yellow+" Please watch to see if the current ramps up gradually. Press any key to begin..."+colour.end)
	source_inst.safe_turn_on(turn_on_value)
	input_1 = input(colour.yellow+" Did the current ramp up? [y/n]"+colour.end)
	current_on = source_inst.read_value('Current')
	input(colour.yellow+" Please watch to see if the current ramps down gradually. Press any key to begin..."+colour.end)
	source_inst.safe_turn_off()
	input_2 = input(colour.yellow+" Did the current ramp down? [y/n]"+colour.end)
	if input_1.lower() == 'y' and input_2.lower() == 'y':
		print(colour.green+" Safe Turn On/Off Current Test: PASSED"+colour.end)
		pass_count += 1
	else:
		print(colour.red+" Safe Turn On/Off Current Test: FAILED"+colour.end)
	#Read Current Test - relies on Safe Turn On/Off Test run previously
	test_count += 1
	if round(current_on*1e3) == round(turn_on_value*1e3):
		print(colour.green+" Read Current Test: PASSED"+colour.end)
		pass_count += 1
	else:
		print(colour.red+" Read Current Test: FAILED"+colour.end)
	#Voltage mode tests
	if has_voltage_mode:
		source_mode = 'Voltage'
		source_inst.mode = source_mode
		source_inst.set_mode()
		#Set Voltage Test
		test_count += 1
		value_1_set = 0.1
		value_2_set = 0.8
		source_inst.set_value(value_1_set,'Voltage')
		value_1 = source_inst.read_setting()
		source_inst.set_value(value_2_set,'Voltage')
		value_2 = source_inst.read_setting()
		if round(value_1*10) == rount(value_1_set*10) and round(value_2*10) == round(value_2_set*10):
			print(colour.green+" Set Current Test: PASSED"+colour.end)
			pass_count += 1
		else:
			print(colour.red+" Set Current Test: FAILED"+colour.end)
		#Safe Turn On/Off Test
		test_count += 1
		turn_on_value = 2
		input(colour.yellow+" Please watch to see if the voltage ramps up gradually. Press any key to begin..."+colour.end)
		source_inst.safe_turn_on(turn_on_value)
		input_1 = input(colour.yellow+" Did the voltage ramp up? [y/n]"+colour.end)
		voltage_on = source_inst.read_value('Voltage')
		input(colour.yellow+" Please watch to see if the voltage ramps down gradually. Press any key to begin..."+colour.end)
		source_inst.safe_turn_off()
		input_2 = input(colour.yellow+" Did the voltage ramp down? [y/n]"+colour.end)
		if input_1.lower() == 'y' and input_2.lower() == 'y':
			print(colour.green+" Safe Turn On/Off Voltage Test: PASSED"+colour.end)
			pass_count += 1
		else:
			print(colour.red+" Safe Turn On/Off Voltage Test: FAILED"+colour.end)
		#Read Voltage Test - relies on Safe Turn On/Off Test run previously
		test_count += 1
		if round(voltage_on*10) == round(turn_on_value*10):
			print(colour.green+" Read Voltage Test: PASSED"+colour.end)
			pass_count += 1
		else:
			print(colour.red+" Read Voltage Test: FAILED"+colour.end)
	### Disconnect
	print(" Disconnected from Source")
	if pass_count == test_count:
		print(colour.green+" Passed all tests"+colour.end)
	else:
		print(colour.red+" Passed "+str(pass_count)+"/"+str(test_count)+" tests"+colour.end)
	
if __name__ == "__main__":
	if len(sys.argv)-1 == 1:
		#One input (device)
		Source_Regression_Test(sys.argv[1])
	else:
		raise Exception(colour.red+colour.alert+" Source_Regression_Test needs one argument"+colour.end)
