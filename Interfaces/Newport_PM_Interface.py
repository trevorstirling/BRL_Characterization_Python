#########################################################################
# Functions to interface with Newport power meter (one or two channel)	#
# Functions:															#
# -set_channel()														#
# -read_power()															#
# -set_wavelength()														#
# -read_wavelength()													#
# -set_filtering()														#
# -set_analogfilter()													#
# -set_digitalfilter()													#
# -set_range()															#
# -set_autorange()														#
# -read_range()															#
#																		#
# Author: Trevor Stirling												#
# Date: April 19, 2023													#
#########################################################################

import os
import sys
import time
from common_functions import colour
from ctypes import *

class Newport_PM:
	def __init__(self, rm, address, channel):
		if sys.platform == "win32":
			self.lib = windll.LoadLibrary(address)
			arInstruments = c_int()
			arInstrumentsModel = c_int()
			arInstrumentsSN = c_int()
			nArraySize = c_int()
			self.lib.GetInstrumentList(byref(arInstruments),byref(arInstrumentsModel),byref(arInstrumentsSN),byref(nArraySize))			
			self.device_id = arInstruments.value
		else:
			self.USB = rm.open_resource(address)
		self.set_channel(channel)
		self.read_power() #read power once to check connection
		
	def write(self,command_string):
		if sys.platform == "win32":
			command = create_string_buffer(str.encode(command_string))
			self.lib.newp_usb_send_ascii(c_long(self.device_id), byref(command), c_ulong(sizeof(command)))
		else:
			self.USB.write(command_string)
			
	def query(self,query_string):
		if sys.platform == "win32":
			command = create_string_buffer(str.encode(query_string))
			self.lib.newp_usb_send_ascii(c_long(self.device_id), byref(command), c_ulong(sizeof(command)))
			#time.sleep(0.2) #not sure why this was necessary, commented out but leaving in for future debugging
			response = create_string_buffer(c_ulong(1024).value)
			read_bytes = c_ulong()
			self.lib.newp_usb_get_ascii(c_long(self.device_id), byref(response), c_ulong(1024), byref(read_bytes))
			temp_response = response.value.decode("utf-8")
			answer = temp_response[0:read_bytes.value].rstrip('\r\n')		
		else:
			answer = self.USB.query(query_string)
		return answer
	
	def set_channel(self, channel):
		if channel == 'A':
			self.write('PM:CHAN 1')
		elif channel == 'B':
			self.write('PM:CHAN 2')
		elif str(channel) == '1' or str(channel) == '2':
			self.write('PM:CHAN '+str(channel))
		else:
			raise Exception(colour.red+colour.alert+" Channel "+str(channel)+" is not a valid choice"+colour.end)
	
	def read_power(self):
		power = float(self.query('PM:P?'))
		if power<-3e+38:
			#detector saturated
			input(colour.yellow+colour.alert+" The detector is saturated, please unsatuturate it and press enter to continue..."+colour.alert+colour.end)
			power = self.read_power()
		count = 0
		while power>3e+38:
			#no detector connected
			if count<100:
				power = float(self.query('PM:P?'))
			else:
				raise Exception(colour.red+colour.alert+" Could not obtain valid reading from power meter. Check the power meter is connected to the correct channel"+colour.end)
			count += 1
		return power
		
	def set_wavelength(self, wavelength):
		wavelength = int(wavelength)
		if wavelength >= int(self.query('PM:MIN:Lambda?')) and wavelength <= int(self.query('PM:MAX:Lambda?')):
			self.write('PM:Lambda '+str(wavelength))
		else:
			print('Wavelenth out of range, did not change wavelength')

	def read_wavelength(self):
		return float(self.query('PM:Lambda?'))
		
	def set_filtering(self, filter_type=0):
		"""
        0: No filtering
        1: Analog filter
        2: Digital filter
        3: Analog and Digital filter
        """
		if filter_type == 0 or filter_type == 1 or filter_type == 2 or filter_type == 3:
			self.write('PM:FILT '+str(filter_type))
		else:
			raise Exception(colour.red+colour.alert+" Filter type must be 0, 1, 2, or 3"+colour.end)

	def set_analogfilter(self, type):
		"""
        0: Off
        1: 250 kHz
        2: 12.5 kHz
        3: 1 kHz
        4: 5 Hz
        """
		if type == 0 or type == 1 or type == 2 or type == 3 or type == 4:
			self.write('PM:ANALOGFILTER ' + str(type))
		else:
			raise Exception(colour.red+colour.alert+" Analog filter type must be 0, 1, 2, 3, or 4"+colour.end)

	def set_digitalfilter(self, value):
		if 0 <= value and value <= 10000:
			self.write('PM:DIGITALFILTER ' + str(value))
		else:
			raise Exception(colour.red+colour.alert+" Digital filter must be between 0 and 10000"+colour.end)

	def set_range(self, range):
		"""
        0: 5.474 uW
        1: 54.74 uW
        2: 547.4 uW
        3: 5.474 mW
        4: 54.74 mW
        """
		if range == 0 or range == 1 or range == 2 or range == 3 or range == 4:
			self.write('PM:RAN ' + str(range))
		else:
			raise Exception(colour.red+colour.alert+" Range must be 0, 1, 2, 3, or 4"+colour.end)

	def set_autorange(self):
		if status == 0 or status == 1:
			self.write('PM:AUTO '+str(status))
		else:
			raise Exception(colour.red+colour.alert+" Autorange status must be 0 or 1"+colour.end)
	
	def read_range(self):
		return int(self.query('PM:RAN?'))
