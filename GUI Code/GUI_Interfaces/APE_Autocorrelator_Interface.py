#########################################################################
# Functions to interface with APE Pulse Check Autocorrelator            #
# -query()                                                              #
# -set_average()                                                        #
# -get_average()                                                        #
# -get_scan_range()                                                     #
# -get_autocorrelation_trace()                                          #
# -capture_current()                                                    #
#                                                                       #
# Author: Trevor Stirling                                               #
# Date: July 30, 2023                                                   #
#########################################################################

class APE_Autocorrelator:
	def __init__(self, rm, address):
		self.GPIB = rm.open_resource(address)

	def query(self, command):
		self.GPIB.write(command)
		result = self.GPIB.read_raw()
		return [i for i in result]

	def set_average(self, value):
		self.GPIB.write('A'+str(value))

	def get_average(self):
		result = self.query('GAV')
		return result[0]

	def get_scan_range(self):
		#assumes 50 ps max scan range version
		sr = self.query('GSR')[0]
		if sr == 0:
			return 0
		elif sr == 1:
			return 500e-15
		elif sr == 2:
			return 1500e-15
		elif sr == 3:
			return 5e-12
		elif sr == 4:
			return 15e-12
		elif sr == 5:
			return 50e-12

	def get_autocorrelation_trace(self):
		result = self.query('GAC')
		#convert from high and low byte to values
		result = [result[2*i]*2**8+result[2*i+1] for i in range(int(len(result)/2))]
		#ignore first and last points which are usually low
		return result[1:-1]

	def capture_current(self):
		intensity = self.get_autocorrelation_trace()
		t_max = self.get_scan_range()
		dt = t_max/(len(intensity)-1)
		time = [i*dt*1e15 for i in range(len(intensity))] #[fs]
		return time, intensity