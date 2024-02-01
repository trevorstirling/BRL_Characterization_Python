#########################################################################
# Functions to interface with SR830 Amplifier                           #
# Functions:                                                            #
# -set_time_constant()                                                  #
# -set_sensitivity()                                                    #
# -read_value()                                                         #
# -read_power()                                                         #
# -read_buffer_size()                                                   #
# -empty_buffer()                                                       #
# -start_buffer_collection()                                            #
# -read_from_buffer()                                                   #
# -set_sampling_rate()                                                  #
#                                                                       #
# Author: Trevor Stirling                                               #
# Date: Sept 29, 2023                                                   #
#########################################################################

import time
import struct
import PySimpleGUI as psg

class SR830:
	def __init__(self, rm, address):
		self.GPIB = rm.open_resource(address)
		self.GPIB.timeout = 30000 #[ms] set long timeout to allow data collection
		self.GPIB.write('OFSL 3') #Set Low Pass Filter slope to 24 dB/oct
		self.GPIB.write('APHS') #Auto Phase
		self.GPIB.write('ALRM 0') #Silence Alarms

	def set_time_constant(self, value):
		time_constants = [10e-6,30e-6,100e-6,300e-6,1e-3,3e-3,10e-3,30e-3,100e-3,300e-3,1,3,10,30,100,300,1e3,3e3,10e3,30e3]
		if value in time_constants:
			range_num = time_constants.index(value)
		else:
			if value < time_constants[0]:
				psg.popup("The time constant can not be set as low as "+str(value)+" s")
			elif value > time_constants[-1]:
				psg.popup("The time constant can not be set as high as "+str(value)+" s")
			else:
				range_num = sum([value>i for i in time_constants])
				print(" Time constant "+str(value)+" s is not valid, set to "+str(time_constants[range_num])+" s instead")
		self.GPIB.write('OFLT'+str(range_num))

	def set_sensitivity(self, value):
		sensitivities = [2e-9,5e-9,10e-9,20e-9,50e-9,100e-9,200e-9,500e-9,1e-6,2e-6,5e-6,10e-6,20e-6,50e-6,100e-6,200e-6,500e-6,1e-3,2e-3,5e-3,10e-3,20e-3,50e-3,100e-3,200e-3,500e-3,1]
		if value in sensitivities:
			range_num = sensitivities.index(value)
		else:
			if value < sensitivities[0]:
				psg.popup("The sensitivity can not be set as low as "+str(value)+" V")
			elif value > sensitivities[-1]:
				psg.popup("The sensitivity can not be set as high as "+str(value)+" V")
			else:
				range_num = sum([value>i for i in sensitivities])
				print(" Sensitivity "+str(value)+" V is not valid, set to "+str(sensitivities[range_num])+" V instead")
		self.GPIB.write('SENS'+str(range_num))
	
	def read_value(self,type="All"):
		[r,theta,freq] = [float(i) for i in self.GPIB.query('SNAP?3,4,9').split(",")]
		if type == "Power":
			return r
		elif type == "Phase":
			return theta
		elif type == "Frequency":
			return freq
		elif type == "All":
			return [r,theta,freq]
		else:
			psg.popup("Can not read "+str(type)+", type not recognized")
	
	def read_power(self):
		return self.read_value("Power")

	def read_buffer_size(self):
		num_points = self.GPIB.query("SPTS?")
		return int(num_points)

	def empty_buffer(self):
		self.GPIB.write("REST")

	def start_buffer_collection(self):
		self.GPIB.write("STRT")

	def read_from_buffer(self, num_points):
		self.GPIB.write("PAUS")
		#TRCA works but is slower
		# result = self.GPIB.query("TRCA?1,0,"+str(num_points))
		# result = [float(i) for i in result.split(",")[:-1]]
		self.GPIB.write("TRCB?1,0,"+str(num_points))
		result = self.GPIB.read_raw()
		result = [struct.unpack("f",result[i*4:i*4+4])[0] for i in range(len(result)//4)]
		return result

	def set_sampling_rate(self, value):
		rates = [62.5e-3,125e-3,250e-3,500e-3,1,2,4,8,16,32,64,128,256,512]
		if value in rates:
			range_num = rates.index(value)
		else:
			if value < rates[0]:
				psg.popup("The sampling rate can not be set as low as "+str(value)+" Hz")
			elif value > rates[-1]:
				psg.popup("The sampling rate can not be set as high as "+str(value)+" Hz")
			else:
				range_num = sum([value>i for i in sensitivities])
				print(" Sampling rate "+str(value)+" Hz is not valid, set to "+str(rates[range_num])+" Hz instead")
		self.GPIB.write('SRAT'+str(range_num))