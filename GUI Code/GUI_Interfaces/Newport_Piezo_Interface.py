#########################################################################
# Functions to interface with Newport piezo stage                       #
# Functions:                                                            #
# -set_channel()                                                        #
# -read_channel()                                                       #
# -wait_for_complete()                                                  #
# -reset()                                                              #
# -move_relative()                                                      #
# -move_to_limit()                                                      #
# -start_jog()                                                          #
# -stop_motion()                                                        #
# -disconnect()                                                         #
# -zero_position()                                                      #
# -get_position()                                                       #
# -set_step_amplitude()                                                 #
# -disconnect()                                                         #
#                                                                       #
# Author: Trevor Stirling                                               #
# Date: Sept 29, 2023                                                   #
#########################################################################

import sys
import time
import serial
import PySimpleGUI as psg

class Newport_Piezo:
	def __init__(self, rm, port, channel, axis):
		if sys.platform == "win32":
			self.USB = serial.Serial(port, 921600, timeout=3)
		else:
			#self.USB = rm.open_resource(port)
			psg.popup("Not yet configured for MacOS")
		if axis in [1,2]:
			self.axis = str(axis)
		else:
			psg.popup("Axis "+str(axis)+" must be 1 or 2")
		self.set_channel(channel)
		# Reset device and put into remote mode
		self.reset()
		try:
			version = self.read_version()
			print(" Connected to Piezo "+version+" via",port)
		except:
			psg.popup("Can not communicate with Piezo, check the port is correct or try disconnecting and reconnecting it")
		
	def write(self,command_string):
		self.USB.write(command_string.encode()+'\r\n'.encode())
		time.sleep(0.1) #Seems to require a pause after each command or else the next command will not be read

	def read(self):
		return self.USB.readline().decode().rstrip()
			
	def query(self,query_string):
		self.write(query_string)
		result = self.read()
		if result == '':
			psg.popup("No response after query: "+query_string)
		return result
	
	def set_channel(self,channel):
		if channel in [1,2,3,4]:
			self.write('CC'+str(channel))
		else:
			psg.popup("Channel "+str(channel)+" must be 1, 2, 3, or 4")
	
	def wait_for_complete(self,timeout=10000):
		for _ in range(timeout):
			time.sleep(0.001)
			self.write(self.axis+'TS')
			if self.axis+'TS0' in self.read():
				return 0
		psg.popup("Timeout from piezo. Check connection or increase timeout time if piezo is still moving")

	def reset(self):
		self.write('RS')
		self.wait_for_complete()
		self.write('MR')

	def move_relative(self,num_steps):
		self.write(self.axis+'PR'+str(int(num_steps)))

	def move_to_limit(self, speed=666):
		if speed in [-1700,-666,-100,-5,5,100,666,1700]:
			self.write(self.axis+'MV'+str(speed))
		else:
			psg.popup("Speed "+str(speed)+" must be plus or minus 5, 100, 666, or 1700")

	def start_jog(self, speed=666):
		speeds = [0,5,100,1700,666]
		if abs(speed) in speeds:
			range_num = speeds.index(abs(speed))
			sign = int(speed/abs(speed))
			self.write(self.axis+'JA'+str(sign*range_num))
		else:
			psg.popup("Speed "+str(speed)+" must be plus or minus 5, 100, 666, or 1700")

	def stop_motion(self):
		self.write(self.axis+'ST')

	def zero_position(self):
		self.write(self.axis+'ZP')

	def get_position(self):
		result = self.query(self.axis+'TP')
		if 'TP' in result:
			return int(result[3:])
		psg.popup("Error on position read, received "+str(result))

	def set_step_amplitude(self, amplitude):
		if amplitude <=50 and amplitude >= -50:
			self.write(self.axis+'SU'+str(amplitude))
		else:
			psg.popup("Step Amplitude "+str(amplitude)+" must be between -50 and 50")

	def read_version(self):
		result = self.query('VE?')
		if 'AG-UC8' in result:
			return result
		psg.popup("Failed to read version from piezo")

	def disconnect(self):
		self.USB.close()
