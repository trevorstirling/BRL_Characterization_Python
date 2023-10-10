#########################################################################
# Functions to interface with K2604B current source						#
# Current source common functions:										#
# -is_on()																#
# -get_mode()															#
# -safe_turn_off()														#
# -safe_turn_on()														#
# -set_value()															#
# -set_voltage_protection()												#
# -set_current_protection()												#
# -set_waveform()														#
# -set_trigger_count()													#
# -initiate_trigger()													#
# -abort_trigger()														#
# -read_value()															#
# -read_setting()														#
# -set_output()															#
# -set_mode()															#
#																		#
# Author: Trevor Stirling												#
# Date: Sept 29, 2023													#
#########################################################################

import time
import PySimpleGUI as psg

class K2604B:
	def __init__(self, rm, address, channel_input, mode):
		self.GPIB = rm.open_resource(address)
		self.GPIB.timeout = 3000 #[ms]
		self.mode = mode.capitalize()
		if self.mode != 'Current' and self.mode != 'Voltage':
			psg.popup("The K2604B mode must be Current or Voltage")
		#Set Channel
		if str(channel_input) == '1' or channel_input == 'A':
			self.channel = 'smua'
		elif str(channel_input) == '2' or channel_input == 'B':
			self.channel = 'smub'
		else:
			psg.popup("The K2604B channel must be A or B")
		self.safe_turn_off()
		#Set Mode
		self.set_mode()
		if self.mode == 'Current':
			self.set_voltage_protection(4) #[V]
			self.GPIB.write(self.channel+'.source.autorangei = '+self.channel+'.AUTORANGE_ON')
		elif self.mode == 'Voltage':
			self.set_current_protection(0.1) #[A]
			self.GPIB.write(self.channel+'.source.autorangev = '+self.channel+'.AUTORANGE_ON')

	def is_on(self):
		if float(self.GPIB.query('printnumber('+self.channel+'.source.output)')):
			return True
		else:
			return False
			
	def get_mode(self):
		if float(self.GPIB.query('printnumber('+self.channel+'.source.func)')):
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
					self.set_value(i*step_size,self.get_mode())
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

	def set_value(self, value, type='N/A'):
		if type == 'N/A':
			type = self.mode
		if type == 'Current':
			self.GPIB.write(self.channel+'.source.leveli = '+str(value))
		elif type == 'Voltage':
			self.GPIB.write(self.channel+'.source.levelv = '+str(value))

	def set_current_protection(self, value):
		self.GPIB.write(self.channel+'.source.limiti = '+str(value))
	
	def set_voltage_protection(self, value):
		self.GPIB.write(self.channel+'.source.limitv = '+str(value))
		
	def set_waveform(self, waveform, delay=20e-6, width=1e-6):
		if waveform == 'PULSED':
			psg.popup("K2604B can not operate in pulsed mode")
	
	def set_trigger_count(self, value):
		#set value to zero for infinite trigger count
		self.GPIB.write(self.channel+'.trigger.count = '+str(value))
	
	def initiate_trigger(self):
		self.GPIB.write(self.channel+'.trigger.initiate()')
		
	def abort_trigger(self):
		self.GPIB.write(self.channel+'.abort()')
	
	def read_value(self, type):
		if type == 'Voltage':
			return float(self.GPIB.query('printnumber('+self.channel+'.measure.v())'))
		elif type == 'Current':
			return float(self.GPIB.query('printnumber('+self.channel+'.measure.i())'))
		elif type == 'Resistance':
			return float(self.GPIB.query('printnumber('+self.channel+'.measure.r())'))
		else:
			psg.popup("Read Error: "+str(type)+" Is An Invalid Data Name")
	
	def read_setting(self):
		if self.get_mode() == 'Voltage':
			value = self.GPIB.query('printnumber('+self.channel+'.source.levelv)')
		elif self.get_mode() == 'Current':
			value = self.GPIB.query('printnumber('+self.channel+'.source.leveli)')
		return float(value)
	
	def set_output(self, state):
		if state == 'ON':
			self.GPIB.write(self.channel + '.source.output = 1')
		elif state == 'OFF':
			self.GPIB.write(self.channel + '.source.output = 0')
		else:
			psg.popup("Channel state must be ON or OFF")
	
	def set_mode(self):
		if self.mode == 'Current':
			self.GPIB.write(self.channel + '.source.func = 0')
		elif self.mode == 'Voltage':
			self.GPIB.write(self.channel + '.source.func = 1')

	
