#########################################################################
# Functions to interface with B2902A current source						#
# Current source common functions:										#
# -is_on()																#
# -get_mode()															#
# -safe_turn_off()														#
# -safe_turn_on()														#
# -set_voltage_protection()												#
# -set_current_protection()												#
# -set_waveform()														#
# -set_value()															#
# -set_trigger_count()													#
# -initiate_trigger()													#
# -abort_trigger()														#
# -read_value()															#
# -read_setting()														#
# -set_output()															#
# -set_mode()															#
#																		#
# Author: Trevor Stirling												#
# Date: April 19, 2023													#
#########################################################################

import time
from common_functions import colour

class B2902A:
	def __init__(self, rm, address, channel_input, mode):
		self.GPIB = rm.open_resource(address)
		self.GPIB.timeout = 30000 #[ms]
		self.mode = mode.capitalize()
		if self.mode != 'Current' and self.mode != 'Voltage':
			raise Exception(colour.red+colour.alert+" The B2902A mode must be Current or Voltage"+colour.end)
		#Set Channel
		if str(channel_input) == '1' or channel_input == 'A':
			self.channel = '1'
		elif str(channel_input) == '2' or channel_input == 'B':
			self.channel = '2'
		else:
			raise Exception(colour.red+colour.alert+" The B2902A channel must be 1 or 2"+colour.end)
		self.safe_turn_off()
		#Set Mode
		self.set_mode()
		self.set_waveform('PULSED', 20e-6, 1e-6) #set up pulsed mode
		self.set_waveform('DC') #actually use DC mode
		if self.mode == 'Current':
			self.set_voltage_protection(4) #[V]
			self.GPIB.write(':SOUR:CURR:RANG:AUTO ON')
		elif self.mode == 'Voltage':
			self.set_current_protection(0.1) #[A]
			self.GPIB.write(':SOUR:VOLT:RANG:AUTO ON')
	
	def is_on(self):
		if float(self.GPIB.query(':OUTP'+self.channel+':STAT?')):
			return True
		else:
			return False
	
	def get_mode(self):
		if self.GPIB.query(':SOUR'+self.channel+':FUNC:MODE?').strip('\n') == 'VOLT':
			return 'Voltage'
		else:
			return 'Current'
	
	def safe_turn_off(self):
		if self.is_on():
			if self.get_mode() == 'Current':
				step_size = .01
				end_value = 1e-3
			elif self.get_mode() == 'Voltage':
				step_size = .1
				end_value = 0
			starting_value = int(self.read_setting()/step_size)
			if starting_value != 0:
				for i in range(starting_value,0,-1*int(starting_value/abs(starting_value))):
					time.sleep(0.1)
					self.set_value(i*step_size, self.get_mode())
			time.sleep(0.1)
			self.set_value(end_value,self.get_mode())
			self.set_output('OFF')
	
	def safe_turn_on(self, value):
		if self.mode == 'Current':
			step_size = .01*value/abs(value)
		elif self.mode == 'Voltage':
			step_size = .1*value/abs(value)
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
		self.GPIB.write(':SENS'+self.channel+':VOLT:PROT '+str(value))
	
	def set_current_protection(self, value):
		self.GPIB.write(':SENS'+self.channel+':CURR:PROT '+str(value))
	
	def set_waveform(self, waveform, delay=20e-6, width=1e-6):
		if(waveform == 'DC'):
			self.GPIB.write(':SOUR'+self.channel+':FUNC:SHAP DC')
		elif(waveform == 'PULSED'):
			self.GPIB.write(':SOUR'+self.channel+':FUNC:SHAP PULS')
			self.GPIB.write(':SOUR'+self.channel+':PULS:DEL ' + str(delay))
			self.GPIB.write(':SOUR'+self.channel+':PULS:WIDT ' + str(width))
			
	def set_value(self, value, type='N/A'):
		if type == 'N/A':
			type = self.mode
		if type == 'Current':
			self.GPIB.write(':SOUR'+self.channel+':CURR '+str(value))
		elif type == 'Voltage':
			self.GPIB.write(':SOUR'+self.channel+':VOLT '+str(value))

	def set_trigger_count(self, value):
		#set value to zero for infinite trigger count?
		if value == 0:
			self.GPIB.write('OUTP'+self.channel+':ON:AUTO ON')
		else:
			self.GPIB.write(':TRIG'+self.channel+':COUN '+str(value))
	
	def initiate_trigger(self):
		self.GPIB.write(':INIT (@'+self.channel+')')
		time.sleep(0.5) #Required for B2902A to stabilize
		
	def abort_trigger(self):
		pass
		#Command not necessary for B2902A

	def read_value(self, type):
		result = self.GPIB.query(':INIT:IMM:ACQ (@'+self.channel+');:FETC? (@'+self.channel+')')
		voltage, current, resistance, time, status, source = result.split(',')
		if type == 'Voltage':
			return float(voltage)
		elif type == 'Current':
			return float(current)
		elif type == 'Resistance':
			#Native resistance measurement returns 9e37
			return self.read_value('Voltage')/self.read_value('Current')
		else:
			raise Exception(colour.red+colour.alert+" Read Error: "+str(type)+" Is An Invalid Data Name"+colour.end)
	
	def read_setting(self):
		if self.get_mode() == 'Voltage':
			value = self.GPIB.query(':SOUR'+self.channel+':VOLT?')
		elif self.get_mode() == 'Current':
			value = self.GPIB.query(':SOUR'+self.channel+':CURR?')
		return float(value)
			
	def set_output(self, state):
			if state == 'ON':
				self.GPIB.write(':OUTP'+self.channel+':STAT ON')
				time.sleep(0.5) #Required for B2902A to stabilize
			elif state == 'OFF':
				self.GPIB.write(':OUTP'+self.channel+':STAT OFF')
			else:
				raise Exception(colour.red+colour.alert+" Channel state must be ON or OFF"+colour.end)

	def set_mode(self):
		if self.mode == 'Current':
			self.GPIB.write(':SOUR'+self.channel+':FUNC:MODE CURR')
			self.GPIB.write(':SOUR'+self.channel+':CURR:MODE FIX')
			self.GPIB.write(':SENS'+self.channel+':FUNC VOLT')
		elif self.mode == 'Voltage':
			self.GPIB.write(':SOUR'+self.channel+':FUNC:MODE VOLT')
			self.GPIB.write(':SOUR'+self.channel+':VOLT:MODE FIX')
			self.GPIB.write(':SENS'+self.channel+':FUNC CURR')
