#########################################################################
# Functions to interface with SWS15101 tunable laser source 			#
# Laser source common functions:										#
# -set_power()															#
# -set_wavelength()														#
# -read_value()															#
# -set_output()															#
#																		#
# SWS15101 specific functions:											#
# -wait_for_OPC()														#
#																		#
# Note: Need to wait for "Operation Complete" from instrument			#
#       Don't query, use a write, wait, read instead					#
#																		#
# Author: Trevor Stirling												#
# Date: Nov 11, 2022													#
#########################################################################

from common_functions import colour

class SWS15101:
	def __init__(self, rm, address):
		self.GPIB = rm.open_resource(address)
		self.max_wait_cycles = 1000

	def wait_for_OPC(self):
		wait_count = 0
		while self.GPIB.stb&1 != 1:
			wait_count = wait_count + 1
			if wait_count == self.max_wait_cycles-1:
				raise Exception(colour.red+colour.alert+" Operation not complete after "+str(self.max_wait_cycles)+" wait cycles."+colour.end)

	def set_power(self, value):
		#assumes value is in [mW]
		self.GPIB.write('mW') #set units, alternately 'dBm'
		self.wait_for_OPC()
		self.GPIB.write('P=' + str(value))
		self.wait_for_OPC()

	def set_wavelength(self, value):
		#assumes value is in nm
		self.GPIB.write('L=' + str(value)) #alternately 'F=' for frequency
		self.wait_for_OPC()

	def read_value(self, type):
		#The read register can have multiple queued values, so first empty it
		read_count = 0
		while self.GPIB.stb&16:
			read_count = read_count + 1
			#something is in the read register, remove it
			self.GPIB.read()
			if read_count == 99:
				raise Exception(colour.red+colour.alert+" Read register not empty after 100 reads."+colour.end)
		if type == 'Power':
			self.GPIB.write('P?')
			self.wait_for_OPC()
			result = self.GPIB.read().strip('\n') #[mW]
			if result == 'DISABLED':
				return 0
			elif result[:2] == 'P=':
				return float(result.strip('P='))
			else:
				raise Exception(colour.red+colour.alert+" Received incorrect result:"+result+". Please try again."+colour.end)
		if type == 'Current':
			self.GPIB.write('I?')
			self.wait_for_OPC()
			result = self.GPIB.read().strip('\n') #[mW]
			if result == 'DISABLED':
				return 0
			elif result[:2] == 'I=':
				return float(result.strip('I='))
			else:
				raise Exception(colour.red+colour.alert+" Received incorrect result:"+result+". Please try again."+colour.end)
		elif type == 'Wavelength':
			self.GPIB.write('L?')
			self.wait_for_OPC()
			result = self.GPIB.read().strip('\n') #[mW]
			if result[:2] == 'L=':
				return float(result.strip('L='))
			else:
				raise Exception(colour.red+colour.alert+" Received incorrect result:"+result+". Please try again."+colour.end)
		else:
			raise Exception(colour.red+colour.alert+" Read Error: "+str(type)+" Is An Invalid Data Name"+colour.end)
		return result

	def set_output(self, state):
		if state.lower() == 'on':
			self.GPIB.write('ENABLE')
			self.wait_for_OPC()
		elif state.lower() == 'off':
			self.GPIB.write('DISABLE')
			self.wait_for_OPC()
		else:
			raise Exception(colour.red+colour.alert+" Channel state must be ON or OFF"+colour.end)
