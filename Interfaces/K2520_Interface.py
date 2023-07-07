#########################################################################
# Functions to interface with K2520 current source 						#
# Current source common functions:										#
# -is_on()																#
# -get_mode()															#
# -safe_turn_off()														#
# -safe_turn_on()														#
# -set_voltage_protection()												#
# -set_current_protection()												#
# -set_waveform()														#
# -set_trigger_count()													#
# -initiate_trigger()													#
# -abort_trigger()														#
# -set_value()															#
# -read_value()															#
# -read_power()															#
# -read_setting()														#
# -set_output()															#
# -set_mode()															#
#																		#
# K2520 specific functions:												#
# -sweep_current()														#
# -enable_init_continuous()												#
#																		#
# Author: Trevor Stirling												#
# Date: July 6, 2023													#
#########################################################################

import time
from common_functions import colour

class K2520:
	def __init__(self, rm, address, channel_input, mode):
		self.GPIB = rm.open_resource(address)
		self.GPIB.timeout = 30000 #[ms] set long timeout to allow sweeping
		self.mode = mode.capitalize()
		self.responsivity = 1/1.74 #measured photodiode responsivity [A/W]
		if self.mode != 'Current':
			raise Exception(colour.red+colour.alert+" The K2520 mode must be Current"+colour.end)
		self.safe_turn_off()
		self.GPIB.write('*RST')
		#Set Mode
		self.set_waveform('PULSED', 20e-6, 1e-6) #set up pulsed mode
		self.set_waveform('DC') #actually use DC mode
		self.set_voltage_protection(4) #[V]
		self.GPIB.write(':SOUR1:CURR:LOW 0')
		self.GPIB.write(':SOUR1:CURR:RANG 0.5') #0.5 or 5 A
		#Set Up Laser Voltage
		self.GPIB.write(':SENS1:VOLT:RANG 5') #5 or 10 V
		self.GPIB.write(':SENS1:VOLT:POL POS')
		#Set Up Detector
		self.GPIB.write(':SENS2:CURR:POL POS')
		self.GPIB.write(':SENS2:CURR:RANG .01') #10, 20, 50, or 100 mA
		self.GPIB.write(':SOUR2:VOLT -20')
		#Set Up Laser Source
		self.GPIB.write(':SOUR1:CURR:POL POS')
		#Configure Math Functions
		self.GPIB.write(':CALC1:FORM RES')
		self.GPIB.write(':CALC1:STAT OFF')
		#Format Data Output
		self.GPIB.write(':FORM:DATA ASC')
		self.GPIB.write(':FORM:ELEM CURR,VOLT,CURR2')

	def is_on(self):
		if self.GPIB.query_ascii_values(':OUTP:STAT?')[0]:
			return True
		else:
			return False
	
	def get_mode(self):
		return 'Current'
	
	def safe_turn_off(self):
		if self.is_on():
			step_size = .01
			end_value = 1e-3
			starting_value = int(self.read_setting()/step_size)
			if starting_value > 0:
				for i in range(starting_value,0,-1*int(starting_value/abs(starting_value))):
					time.sleep(0.1)
					self.set_value(i*step_size)
			time.sleep(0.1)
			self.set_value(end_value)
			self.set_output('OFF')
	
	def safe_turn_on(self, value):
		step_size = .01*value/abs(value)
		if abs(value)>abs(step_size):
			self.set_value(step_size)
			self.set_output('ON')
			for i in range(2,int(value/step_size),1):
				time.sleep(0.5)
				self.set_value(i*step_size)
			time.sleep(0.5)
			self.set_value(value)
		else:
			self.set_value(value)
			self.set_output('ON')
	
	def set_voltage_protection(self, value):
		self.GPIB.write(':SOUR1:VOLT:PROT '+str(value))
		
	def set_current_protection(self, value):
		pass
		#Command not necessary for K2520

	def set_waveform(self, waveform, delay=20e-6, width=1e-6):
		if waveform == 'DC':
			self.GPIB.write(':SOUR1:FUNC:SHAP DC')
		elif waveform == 'PULSED':
			self.GPIB.write(':SOUR1:FUNC:SHAP PULS')
			self.GPIB.write(':SOUR1:PULS:DEL '+str(delay))
			self.GPIB.write(':SOUR1:PULS:WIDT '+str(width))

	def set_value(self, value):
		self.GPIB.write(':SOUR1:CURR '+str(value))

	def set_trigger_count(self, value):
		#set value to zero for infinite trigger count
		if value == 0:
			self.GPIB.write(':TRIG:COUN INF')
		else:
			self.GPIB.write(':TRIG:COUN '+str(value))

	def initiate_trigger(self):
		self.GPIB.write(':INIT')
		
	def abort_trigger(self):
		self.GPIB.write(':ABOR')

	def read_value(self, type):
		result = self.GPIB.query_ascii_values(':READ?')
		#result.extend(self.GPIB.query_ascii_values(':CALC1:DATA?'))
		drive_current, voltage, photodiode_current = result
		if type == 'Current':
			return float(drive_current)
		elif type == 'Voltage':
			return float(voltage)
		elif type == 'PD_current':
			return float(photodiode_current)
		elif type == 'Resistance':
			return float(voltage/drive_current)
		else:
			raise Exception(colour.red+colour.alert+" Read Error: Invalid Data Name"+colour.end)
	
	def read_power(self):
		pd_curr = self.read_value('PD_current')
		return float(pd_curr)/self.responsivity #[W]

	def read_setting(self):
		return float(self.GPIB.query(':SOUR1:CURR?'))

	def set_output(self, state):
		if state == 'ON':
			self.GPIB.write(':OUTP1 ON')
		elif state == 'OFF':
			self.GPIB.write(':OUTP1 OFF')
		else:
			raise Exception(colour.red+colour.alert+" Channel state must be ON or OFF"+colour.end)
		
	def set_display(self, state):
		if state == 'ON':
			self.GPIB.write(':DISP:ENAB ON')
		elif state == 'OFF':
			self.GPIB.write(':DISP:ENAB OFF')
		else:
			raise Exception(colour.red+colour.alert+" Display enable state must be ON or OFF"+colour.end)

	def set_mode(self):
		pass
		#Command not necessary for K2520

	def sweep_current(self, start, step, stop):
		#K2520 has internal sweep function
		if stop > 0.45:
			self.GPIB.write(':SOUR1:CURR:RANG 5') #0.5 or 5 A
		self.GPIB.write(':FORM:ELEM CURR,VOLT,CURR2')
		self.GPIB.write(':SOUR1:CURR:MODE SWE')
		self.GPIB.write(':SOUR1:SWE:SPAC LIN')
		self.GPIB.write(':SOUR1:SWE:DIR UP')
		extra_point = False
		if start-step < 0:
			print(colour.yellow+" Warning: could not collect an extra data point, there may be a voltage spike at the start"+colour.end)
			start = start-step
			extra_point = True
		self.GPIB.write(':SOUR1:CURR '+str(start)) #set current here to display current on K2520 during sweep
		self.GPIB.write(':SOUR1:CURR:STAR '+str(start)) #collect one extra data point to avoid initial spike in DC mode
		self.GPIB.write(':SOUR1:CURR:STOP '+str(stop))
		self.GPIB.write(':SOUR1:CURR:STEP '+str(step))
		self.GPIB.write(':OUTP1 ON')
		result = self.GPIB.query_ascii_values(':READ?')
		if extra_point:
			current, voltage, photocurrent = [result[3::3],result[4::3],result[5::3]] #separate result and delete extra data point added above
		else:
			current, voltage, photocurrent = [result[0::3],result[1::3],result[2::3]] #separate result
		self.GPIB.write(':OUTP1 OFF')
		self.GPIB.write(':SOUR1:CURR ' + str(start)) #set to first input to avoid accidental damage
		power = [i/self.responsivity for i in photocurrent]
		return current, voltage, power

	def enable_init_continuous(self):
		#Turns on INIT Continuous setting which is auto disabled after a pulsed sweep
		#There does not seem to be a command to change this setting, so currently sending individual key presses with delay.
		self.GPIB.write(':SYST:KEY 28')
		time.sleep(0.1)
		self.GPIB.write(':SYST:KEY 20')
		time.sleep(0.1)
		self.GPIB.write(':SYST:KEY 3')
		time.sleep(0.1)
		self.GPIB.write(':SYST:KEY 3')
		time.sleep(0.1)
		self.GPIB.write(':SYST:KEY 3')
		time.sleep(0.1)
		self.GPIB.write(':SYST:KEY 3')
		time.sleep(0.1)
		self.GPIB.write(':SYST:KEY 10')
		time.sleep(0.1)
		self.GPIB.write(':SYST:KEY 18')
		time.sleep(0.1)
		self.GPIB.write(':SYST:KEY 3')
		time.sleep(0.1)
		self.GPIB.write(':SYST:KEY 18')
		time.sleep(0.1)
		self.GPIB.write(':SYST:KEY 11')