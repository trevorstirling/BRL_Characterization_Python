#########################################################################
# Functions to interface with AQ6374 optical spectrum analyzer          #
# OSA common functions:                                                 #
# -initialize()                                                         #
# -capture()                                                            #
# -is_sweeping()                                                        #
# -wait_for_sweeping()                                                  #
# -sweep()                                                              #
# -set_ref_level()                                                      #
# -set_y_scale()                                                        #
# -set_wavelength()                                                     #
# -set_span()                                                           #
# -set_rbw()                                                            #
# -peak_to_center()                                                     #
# -sweep_continuous()                                                   #
# -read_value()                                                         #
#                                                                       #
# AQ6374 specific functions:                                            #
# -set_sensitivity()                                                    #
#                                                                       #
# Author: Trevor Stirling                                               #
# Date: Sept 26, 2023                                                   #
#########################################################################

import numpy as np
import math
import time
from common_functions import colour

class AQ6374:
	def __init__(self, rm, address):
		self.GPIB = rm.open_resource(address)
		self.GPIB.timeout = 30000 #[ms] set long timeout to allow sweeping
		self.isESA = False
		self.isOSA = True
		#set command format to AQ6374 format:
		self.GPIB.write('CFORM1') #If in AQ6317 format, change to AQ6374 format
        
	def initialize(self):
		#Restore Defaults
		self.GPIB.timeout = 90000 #[ms] set extremely long timeout to allow restart
		self.GPIB.write('*RST')
		self.GPIB.timeout = 30000
		#Set Up Amplitude
		self.set_ref_level(-30) #dBm
		self.set_y_scale(10) #dB/div
		#Set Up Wavelength
		self.set_wavelength(780) #nm
		self.set_span(6) #nm
		#Set Up Bandwidths
		self.set_rbw(.1) #nm
		self.set_sensitivity('MID') #MID, HIGH1, HIGH2, or HIGH3
	
	def capture(self, channel, print_status=True):
		if channel not in ['A','B','C','D','E','F','G']:
			raise Exception(colour.red+colour.alert+" "+str(channel)+" is not a valid channel, should be A-G"+colour.end)
		if print_status:
			print(" Capturing...")
		power = np.array(self.GPIB.query_ascii_values(':TRAC:DATA:Y? TR'+channel)) #Level data
		wavelength = np.array(self.GPIB.query_ascii_values(':TRAC:DATA:X? TR'+channel)) #Wavelength data
		wavelength = wavelength*1e9 #convert to nm
		# #Delete first data point (always erroneous)
		# power = power[1:]
		# wavelength = wavelength[1:]
		#replace -210 dBm with -infinity
		for i in range(len(power)):
			if power[i] == -210:
				power[i] = -math.inf
		if print_status:
			print(" Capture complete")
		return wavelength, power #nm, dBm
            
	def is_sweeping(self):
		self.GPIB.write(':SYST:COMM:CFOR 0') #switch to AQ6317 command format to check if sweeping
		sweeping = np.array(self.GPIB.query_ascii_values('SWEEP?'))
		self.GPIB.write('CFORM1') #switch back to AQ6374 command format
		if sweeping:
			return True
		else:
			return False
	
	def wait_for_sweeping(self):
		sweeping = self.is_sweeping()
		while sweeping == 1:
			time.sleep(1)
			sweeping = self.is_sweeping()

	def sweep(self, channel='N/A', print_status=True):
		#if passed a channel, only sweep that channel
		channel_list = ['A','B','C','D','E','F','G']
		if channel in channel_list:
			for chan in channel_list:
				if chan != channel:
					self.GPIB.write(':TRAC:ATTR:TR'+chan+' FIX')
			self.GPIB.write(':TRAC:ATTR:TR'+channel+' WRIT')
		elif channel != 'N/A':
			raise Exception(colour.red+colour.alert+" "+str(channel)+" is not a valid channel, should be A-G (or left empty)"+colour.end)
		if print_status:
			print(" Sweeping...")
		self.GPIB.write(':INIT:SMOD 1;:INIT')
		self.wait_for_sweeping()
		if print_status:
			print(" Sweep complete")
	
	def set_ref_level(self, ref_level):
		self.GPIB.write(':DISP:WIND:TRAC:Y1:SCAL:RLEV '+str(ref_level)) #-90 to 20 dBm

	def set_y_scale(self, scale):
		self.GPIB.write(':DISP:WIND:TRAC:Y1:SCAL:PDIV '+str(scale)) #dB/div

	def set_wavelength(self, wavelength):
		self.GPIB.write(':SENS:WAV:CENT '+str(wavelength)+'nm') #600 to 1750 nm

	def set_span(self, span):
		self.GPIB.write(':SENS:WAV:SPAN '+str(span)+'nm') #0, or 0.5 to 1200 nm

	def set_rbw(self, rbw):
		self.GPIB.write(':SENS:BAND:RES '+str(rbw)+'nm') #0.01 to 2.0 nm
	
	def set_sensitivity(self, sensitivity):
		if sensitivity == 'MID':
			self.GPIB.write(':SENS:SENS MID')
		elif sensitivity == 'HIGH1':
			self.GPIB.write(':SENS:SENS HIGH1')
		elif sensitivity == 'HIGH2':
			self.GPIB.write(':SENS:SENS HIGH2')
		elif sensitivity == 'HIGH3':
			self.GPIB.write(':SENS:SENS HIGH3')
		else:
			raise Exception(colour.red+colour.alert+" "+str(sensitivity)+" is not a valid sensitivity setting"+colour.end)

	def peak_to_center(self, print_status=True):
		self.GPIB.write(':CALC:MARK:MAX')
		wavelength = float(self.GPIB.query_ascii_values(':CALC:MARK:X? 0')[0])*1e9
		self.GPIB.write(':CALC:MARK:MAX:SCEN')
		self.sweep()
		self.GPIB.write(':CALC:MARK:X 0,'+str(wavelength)+'nm')
		power = float(self.GPIB.query_ascii_values(':CALC:MARK:Y? 0')[0])
		if print_status:
			print(" Wavelength = "+"{:.2f}".format(wavelength)+" nm")
			print(" Power = "+"{:.2f}".format(power)+" dBm")

	def sweep_continuous(self, status):
		if status == 1:
			self.GPIB.write(':INIT:SMOD REP;:INIT')
		elif status == 0:
			self.GPIB.write(':INIT:SMOD SING;:INIT')
		else:
			raise Exception(colour.red+colour.alert+" sweep_continuous status must be 1 or 0"+colour.end)

	def read_value(self, type):
		if type == 'Reference Level':
			return float(self.GPIB.query_ascii_values(':DISP:WIND:TRAC:Y1:SCAL:RLEV?')[0])
		elif type == 'Wavelength':
			return float(self.GPIB.query_ascii_values(':SENS:WAV:CENT?')[0]*1e9)
		elif type == 'Span':
			return float(self.GPIB.query_ascii_values(':SENS:WAV:SPAN?')[0]*1e9)
		elif type == 'Y Scale':
			return float(self.GPIB.query_ascii_values(':DISP:WIND:TRAC:Y1:SCAL:PDIV?')[0])
		elif type == 'RBW':
			return float(self.GPIB.query_ascii_values(':SENS:BAND:RES?')[0]*1e9)
		elif type == 'Sensitivity':
			sensitivity = int(self.GPIB.query_ascii_values(':SENS:SENS?')[0])
			if sensitivity == 0:
				return 'NORM HOLD'
			if sensitivity == 1:
				return 'NORM AUTO'
			elif sensitivity == 2:
				return 'MID'
			elif sensitivity == 3:
				return 'HIGH1'
			elif sensitivity == 4:
				return 'HIGH2'
			elif sensitivity == 5:
				return 'HIGH3'
			elif sensitivity == 6:
				return 'NORM'
		else:
			raise Exception(colour.red+colour.alert+" Read Error: "+str(type)+" Is An Invalid Data Name"+colour.end)
