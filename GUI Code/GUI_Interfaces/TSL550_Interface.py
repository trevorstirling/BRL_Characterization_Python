#########################################################################
# Functions to interface with TSL550 (Santec) tunable laser source      #
# Laser source common functions:                                        #
# -set_power()                                                          #
# -set_wavelength()                                                     #
# -read_value()                                                         #
# -set_output()                                                         #
#                                                                       #
# Author: Trevor Stirling                                               #
# Date: Nov 22, 2023                                                    #
#########################################################################

import PySimpleGUI as psg

class TSL550:
	def __init__(self, rm, address):
		self.GPIB = rm.open_resource(address)
		self.max_wait_cycles = 1000

	def set_power(self, value):
		#assumes value is in [mW]
		self.GPIB.write(':SOUR:POW:UNIT 1') #set units to mW, alternatively 0 for dBm
		self.GPIB.write(':SOUR:POW:LEV '+str(value))

	def set_wavelength(self, value):
		#assumes value is in [nm]
		self.GPIB.write(':SOUR:WAV:UNIT 0') #set units to nm, alternatively 1 for THz
		self.GPIB.write(':SOUR:WAV '+str(value))

	def read_value(self, type):
		if type == 'Power':
			self.GPIB.write(':SOUR:POW:UNIT 1') #set units to mW, alternatively 0 for dBm
			result = self.GPIB.query(':SOUR:POW:LEV?')
		elif type == 'Wavelength':
			self.GPIB.write(':SOUR:WAV:UNIT 0') #set units to nm, alternatively 1 for THz
			result = self.GPIB.query(':SOUR:WAV?')
		else:
			psg.popup("Read Error: "+str(type)+" Is An Invalid Data Name")
		return result

	def set_output(self, state):
		if state.lower() == 'on':
			self.GPIB.write(':SOUR:POW:SHUT 0')
		elif state.lower() == 'off':
			self.GPIB.write(':SOUR:POW:SHUT 1')
		else:
			psg.popup("Channel state must be ON or OFF")
