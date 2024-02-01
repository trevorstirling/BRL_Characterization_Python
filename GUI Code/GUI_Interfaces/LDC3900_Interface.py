#########################################################################
# Functions to interface with LDC3908 and LDC3916 current sources       #
# (DFB Controller)                                                      #
# Current source common functions:                                      #
# -is_on()                                                              #
# -get_mode()                                                           #
# -safe_turn_off()                                                      #
# -safe_turn_on()                                                       #
# -set_voltage_protection()                                             #
# -set_current_protection()                                             #
# -set_waveform()                                                       #
# -set_value()                                                          #
# -set_trigger_count()                                                  #
# -initiate_trigger()                                                   #
# -abort_trigger()                                                      #
# -read_value()                                                         #
# -read_setting()                                                       #
# -set_output()                                                         #
# -set_mode()                                                           #
#                                                                       #
# LDC3900 specific functions:                                           #
# -set_channel()                                                        #
#                                                                       #
# Notes: consider implementing wait_for_OPC rather than time.sleep(5)   #
#        consider implementing a check for error if no device connected #
#                                                                       #
# Author: Trevor Stirling                                               #
# Date: Jan 31, 2024                                                    #
#########################################################################

import time
import PySimpleGUI as psg

class LDC3900:
	def __init__(self, rm, address, channel_input, mode,num_channels):
		if num_channels == 8:
			self.name = "LDC3908"
		elif num_channels == 16:
			self.name = "LDC3916"
		else:
			psg.popup("The LDC3900 must have 8 or 16 channels")
		self.GPIB = rm.open_resource(address)
		self.GPIB.timeout = 30000 #[ms]
		self.mode = mode.capitalize()
		if self.mode != 'Current':
			psg.popup("The "+self.name+" mode must be Current")
		#Set Channel
		if str(channel_input) in [str(i) for i in range(1,num_channels+1)]:
			self.channel = str(channel_input)
			self.set_channel()
		else:
			psg.popup("The "+self.name+" channel must an integer 1 to "+str(num_channels))
		self.safe_turn_off()
		self.set_voltage_protection(4) #[V]

	def set_channel(self,channel_num='N/A'):
		if channel_num == 'N/A':
			self.GPIB.write('CHAN '+str(self.channel)) #debug: could be LAS:CHAN
		else:
			self.GPIB.write('CHAN '+str(channel_num)) #debug: could be LAS:CHAN

	def is_on(self):
		self.set_channel()
		if int(self.GPIB.query('LAS:OUT?')[:-1]):
			return True
		else:
			return False
	
	def get_mode(self):
		return 'Current'
	
	def safe_turn_off(self):
		self.set_channel()
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
		self.set_channel()
		step_size = .01
		if value<0:
			step_size = -1*step_size
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
		self.set_channel()
		self.GPIB.write('LAS:LIM:V '+str(value))
		
	def set_current_protection(self, value):
		pass
		#Command not necessary for LDC3900
    
	def set_waveform(self, waveform, delay=20e-6, width=1e-6):
		if waveform == 'PULSED':
			psg.popup(self.name+" can not operate in pulsed mode")

	def set_value(self, value):
		self.set_channel()
		value = value*1e3 #convert from [A] to [mA]
		self.GPIB.write('LAS:I '+str(value))

	def set_trigger_count(self, value):
		pass
		#Command not necessary for LDC3900
	
	def initiate_trigger(self):
		pass
		#Command not necessary for LDC3900
	
	def abort_trigger(self):
		pass
		#Command not necessary for LDC3900

	def read_value(self, type):
		self.set_channel()
		if type == 'Voltage':
			result = float(self.GPIB.query('LAS:LDV?')) #[V]
		elif type == 'Current':
			result = float(self.GPIB.query('LAS:I?'))*1e-3 #[A]
		elif type == 'Resistance':
			return self.read_value('Voltage')/self.read_value('Current')
		else:
			psg.popup("Read Error: "+str(type)+" Is An Invalid Data Name")
		return result

	def read_setting(self):
		self.set_channel()
		return float(self.GPIB.query('LAS:I?'))*1e-3 #[A]

	def set_output(self, state):
		self.set_channel()
		if state == 'ON':
			self.GPIB.write('LAS:OUT ON')
			time.sleep(5) #Wait for device to turn on
		elif state == 'OFF':
			self.GPIB.write('LAS:OUT OFF')
		else:
			psg.popup("Channel state must be ON or OFF")

	def set_mode(self):
		pass
		#Command not necessary for LDC3900
