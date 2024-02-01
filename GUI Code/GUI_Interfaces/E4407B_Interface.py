#########################################################################
# Functions to interface with E4407B electrical spectrum analyzer       #
# SA common functions:                                                  #
# -initialize()                                                         #
# -capture()                                                            #
# -is_sweeping()                                                        #
# -wait_for_sweeping()                                                  #
# -sweep()                                                              #
# -set_ref_level()                                                      #
# -set_y_scale()                                                        #
# -set_frequency()                                                      #
# -set_span()                                                           #
# -set_rbw()                                                            #
# -peak_to_center()                                                     #
# -sweep_continuous()                                                   #
# -read_value()                                                         #
#                                                                       #
# E4407B specific functions:                                            #
# -set_vbw()                                                            #
#                                                                       #
# Author: Trevor Stirling                                               #
# Date: Dec 5, 2023                                                     #
#########################################################################

import numpy as np
import math
import time
import PySimpleGUI as psg

class E4407B:
	def __init__(self, rm, address):
		self.GPIB = rm.open_resource(address)
		self.GPIB.timeout = 25000
		self.isESA = True
		self.isOSA = False

	def initialize(self): # new addition 
		#Restore Defaults
		self.GPIB.timeout = 90000 #[ms] set extremely long timeout to allow restart
		self.GPIB.write('*RST')
		self.GPIB.timeout = 25000
		#Set Up Amplitude
		self.set_ref_level(0) #dBm
		self.set_y_scale(10) #dB/div
		#Set Up Wavelength
		self.set_frequency(13.75e9) #Hz
		self.set_span(13.75e9) #Hz
		#Set Up Bandwidths
		self.set_rbw(1000) #Hz
		self.set_vbw(2000) #Hz
	
	def capture(self, channel, print_status=True):
		if print_status:
			print(" Capturing...")
		self.GPIB.write(':CALC:NTD 0;:FORM ASC;:FORM:BORD NORM') #command from page 278
		power = self.GPIB.query_ascii_values(':TRAC? TRACE'+str(channel))
		start = self.GPIB.query_ascii_values(':FREQ:STAR?')[0]
		span = self.GPIB.query_ascii_values(':FREQ:SPAN?')[0]
		step = span/(len(power)-1)
		frequency = np.arange(start, start+span+step/2, step)
		frequency = [x/1e9 for x in frequency]
		if print_status:
			print(" Capture complete")
		return frequency, power #GHz, dBm

	def is_sweeping(self):
		#result = int(self.GPIB.query_ascii_values(':STAT:OPER?')[0]) #note: this clears the register after reading
		#causing problems, always return 0 for now and debug later
		return 0
		#return result&8 == 8

	def wait_for_sweeping(self):
		if self.is_sweeping():
			self.GPIB.query('*OPC?')
			
	def sweep(self, channel='N/A', print_status=True):
		#if passed a channel, only sweep that channel
		channel_list = ['1','2','3']
		if channel in channel_list:
			for chan in channel_list:
				if chan != channel:
					self.GPIB.write(':TRAC'+channel+':MODE BLAN')
			self.GPIB.write(':TRAC'+channel+':MODE WRIT')
		if print_status:
			print(" Sweeping...")
		self.sweep_continuous(0)
		self.GPIB.write(':INIT')
		self.wait_for_sweeping()
		if print_status:
			print(" Sweep complete")

	def set_ref_level(self, ref_level):
		self.GPIB.write(':DISP:WIND:TRAC:Y:SCAL:RLEV '+str(ref_level)) #-149.9 to 55 dBm, page 275 

	def set_y_scale(self, scale):
		self.GPIB.write(':DISP:WIND:TRAC:Y:SCAL:PDIV '+str(scale)) #0.1 to 20 dB/div, page 274        
		
	def set_frequency(self, frequency):
		self.GPIB.write(':SENS:FREQ:CENT '+ str(frequency)) #9 kHz - 26.5 GHz, page 322   
	
	def set_span(self, span):
		self.GPIB.write(':SENS:FREQ:SPAN '+ str(span)) # 100 Hz - 27 GHz, page 322
		
	def set_rbw(self, rbw):
		self.GPIB.write(':BAND '+ str(rbw)) #1 to 5000 Hz, page 306
	
	def set_vbw(self, vbw):
		self.GPIB.write(':SENS:BWID:VID '+str(vbw)) #1 to 3000 Hz, page 306

	def peak_to_center(self, print_status=True):
		self.GPIB.write(':CALC:MARK1:MAX')
		frequency = self.GPIB.query_ascii_values(':CALC:MARK1:X?')[0]
		self.set_frequency(frequency)
		power = self.GPIB.query_ascii_values(':CALC:MARK1:Y?')[0]
		if print_status:
			print(" Frequency = "+"{:.2f}".format(frequency/1e9)+" GHz")
			print(" Power = "+"{:.2f}".format(power)+" dBm")

	def sweep_continuous(self, status):
		self.GPIB.write(':INIT:CONT '+str(status))
		time.sleep(0.1)

	def read_value(self, type):
		if type == 'Reference Level':
			return float(self.GPIB.query_ascii_values(':DISP:WIND:TRAC:Y:SCAL:RLEV?')[0])
		elif type == 'Frequency':
			return float(self.GPIB.query_ascii_values(':SENS:FREQ:CENT?')[0])
		elif type == 'Span':
			return float(self.GPIB.query_ascii_values(':SENS:FREQ:SPAN?')[0])
		elif type == 'Y Scale':
			return float(self.GPIB.query_ascii_values(':DISP:WIND:TRAC:Y:SCAL:PDIV?')[0])
		elif type == 'RBW':
			return float(self.GPIB.query_ascii_values(':BAND?')[0])
		elif type == 'VBW':
			return float(self.GPIB.query_ascii_values(':SENS:BWID:VID?')[0])
		else:
			psg.popup("Read Error: "+str(type)+" Is An Invalid Data Name")
