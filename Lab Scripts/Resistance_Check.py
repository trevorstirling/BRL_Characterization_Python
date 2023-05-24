#########################################################################
# Script to check resistance of devices with current applied using		#
# various current sources. Should usually be 1.5 kΩ at 1 mA. 			#
#																		#
# Author: Trevor Stirling												#
# Date: Aug 17, 2022													#
#########################################################################

import time
from common_functions import connect_to_GPIB

def Res_Check():
	##########################################
	####         Define Variables         ####
	##########################################
	### Source - K2520, K2604B, B2902A, or LDC3908
	Source = 'K2520'
	Source_channel = 1 #1-8, A or B, for two channel sources only (ignored for one channel)
	measurement_current = 1 #[mA]
	waveform = "DC" #pulsed or DC
	pulse_delay = 20e-6 #delay between pulses [s] (pulsed mode only)
	pulse_width = 1e-6 #width of pulses [s] (pulsed mode only)
	protection_voltage = 4 #[V]
	protection_current = 0.1 #[A]
	##########################################
	####            Main Code             ####
	##########################################
	### Connect to Lab Equipment
	# Source
	Source_inst = connect_to_GPIB(Source,['Current',Source_channel,protection_voltage,protection_current,waveform,pulse_delay,pulse_width])
	### Turn on current and measure resistance
	Source_inst.set_value(measurement_current*1e-3)
	Source_inst.set_output('ON')
	if Source == 'K2520':
		time.sleep(1)
	resistance = Source_inst.read_value('Resistance')
	Source_inst.set_output('OFF')
	print(" {:.1f}".format(resistance),"Ohms at",measurement_current,"mA")
	print(" Disconnected from",Source)

if __name__ == "__main__":
	Res_Check()
