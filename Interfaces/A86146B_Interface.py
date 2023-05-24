#########################################################################
# Functions to interface with A86146B optical spectrum analyzer			#
# OSA common functions:													#
# -initialize()															#
# -capture()															#
# -is_sweeping()														#
# -wait_for_sweeping()													#
# -sweep()																#
# -set_ref_level()														#
# -set_y_scale()														#
# -set_wavelength()														#
# -set_span()															#
# -set_rbw()															#
# -peak_to_center()														#
# -sweep_continuous()													#
# -read_value()															#
#																		#
# A86146B specific functions:											#
# -set_vbw()															#
#																		#
# Author: Trevor Stirling												#
# Date: Feb 18, 2022													#
#########################################################################

### Need to test is_sweeping(), wait_for_sweeping(), and sweep()

import numpy as np
from common_functions import colour

class A86146B:
	def __init__(self, rm, address):
		self.GPIB = rm.open_resource(address)
		self.GPIB.timeout = 30000 #set long timeout to allow sweeping

	def initialize(self):
		#Restore Defaults
		self.GPIB.timeout = 90000 #[ms] set extremely long timeout to allow restart
		self.GPIB.write('*RST')
		self.GPIB.write('*OPC')
		self.GPIB.timeout = 30000
		#Set Up Amplitude
		self.set_ref_level(-25) #dBm
		self.set_y_scale(6)#dB/div
		#Set Up Wavelength
		self.set_wavelength(780) #nm
		self.set_span(60) #nm
		#Set Up Bandwidths
		self.set_rbw(.06) #nm
		self.set_vbw(2000) #Hz
	
	def capture(self, channel):
		if channel not in ['A','B','C','D','E','F']:
			raise Exception(colour.red+colour.alert+" "+str(channel)+" is not a valid channel, should be A-F"+colour.end)
		print(" Capturing...")
		start_output = self.GPIB.query_ascii_values('TRACE:DATA:X:STAR? TR'+channel)
		stop_output = self.GPIB.query_ascii_values('TRACE:DATA:X:STOP? TR'+channel)
		start = start_output[0]*1e9
		stop = stop_output[0]*1e9
		self.GPIB.write('FORM REAL, 64; TRAC:DATA:Y? TR'+channel)
		output_data = self.GPIB.read_binary_values(datatype='d', is_big_endian=True)
		power = [x for x in output_data]
		n = len(power)
		step = (stop-start)/(n-1)
		wavelength = np.arange(start, stop + step/2, step) #end value just past stop to include end point
		print(" Capture complete")
		return wavelength, power
	
	def is_sweeping(self):
		self.GPIB.write('*ESE 1')
		complete = self.GPIB.query_ascii_values('*ESE?')
		if complete:
			return False
		else:
			return True
	
	def wait_for_sweeping(self):
		self.GPIB.write('*OPC?')
		self.GPIB.write('*WAI')
	
	def sweep(self ,channel='N/A'):
		#if passed a channel, only sweep that channel
		channel_list = ['A','B','C','D','E','F']
		if channel in channel_list:
			for chan in channel_list:
				if chan != channel:
					self.GPIB.write('TRAC:FEED:CONT TR'+chan+', NEV')
			self.GPIB.write('TRAC:FEED:CONT TR'+channel+', ALW')
		elif channel != 'N/A':
			raise Exception(colour.red+colour.alert+" "+str(channel)+" is not a valid channel, should be A-F (or left empty)"+colour.end)
		print(" Sweeping...")
		self.GPIB.write('INIT:IMM')
		self.wait_for_sweeping()
		print(" Sweep complete")

	def set_ref_level(self, ref_level):
		self.GPIB.write('DISP:WIND:TRAC:Y:SCAL:RLEV '+str(ref_level)+'dBm')
	
	def set_y_scale(self, scale):
		self.GPIB.write('DISP:WIND:TRAC:Y:SCAL:PDIV '+str(scale)+'dB')
	
	def set_wavelength(self, wavelength):
		self.GPIB.write('SENS:WAV:CENT '+str(wavelength)+'nm')
	
	def set_span(self, span):
		self.GPIB.write('SENS:WAV:SPAN '+str(span)+'nm')
		
	def set_rbw(self, rbw):
		self.GPIB.write('SENS:BWID:RES '+str(rbw)+'nm')
	
	def set_vbw(self, vbw):
		self.GPIB.write('SENS:BWID:VID '+str(vbw)+'Hz') #0.1 to 3000 Hz
		
	def peak_to_center(self):
		self.GPIB.write('CALC1:MARK1:MAX')#marker to peak
		self.GPIB.write('CALC1:MARK1:SCEN')#marker to center
		wavelength = self.GPIB.query_ascii_values('CALC1:MARK1:X?')
		power = self.GPIB.query_ascii_values('CALC1:MARK1:Y?')
		print(" Wavelength = "+"{:.2f}".format(wavelength[0]*1e9)+" nm")
		print(" Power = "+"{:.2f}".format(power[0])+" dBm")
		
	def sweep_continuous(self, status):
		if status == 1:
			self.GPIB.write('INIT:CONT ON')
		elif status == 0:
			self.GPIB.write('INIT:CONT OFF')
		else:
			raise Exception(colour.red+colour.alert+" sweep_continuous status must be 1 or 0"+colour.end)

	def read_value(self, type):
		if type == 'Reference Level':
			return float(self.GPIB.query_ascii_values('DISP:WIND:TRAC:Y:SCAL:RLEV?')[0])
		elif type == 'Wavelength':
			return float(self.GPIB.query_ascii_values('SENS:WAV:CENT?')[0])
		elif type == 'Span':
			return float(self.GPIB.query_ascii_values('SENS:WAV:SPAN?')[0])
		elif type == 'Y Scale':
			return float(self.GPIB.query_ascii_values('DISP:WIND:TRAC:Y:SCAL:PDIV?')[0])
		elif type == 'RBW':
			return float(self.GPIB.query_ascii_values('SENS:BWID:RES?')[0])
		elif type == 'VBW':
			return float(self.GPIB.query_ascii_values('SENS:BWID:VID?')[0])
		else:
			raise Exception(colour.red+colour.alert+" Read Error: "+str(type)+" Is An Invalid Data Name"+colour.end)
