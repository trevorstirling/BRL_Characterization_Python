#########################################################################
# Script to check resistance of devices with current applied using		#
# various current sources. Should usually be 1.5 kΩ at 1 mA. 			#
#																		#
# Author: Trevor Stirling												#
# Date: July 6, 2023													#
#########################################################################

import time
from common_functions import connect_to_GPIB, connect_to_PM

def Res_Check():
	##########################################
	####         Define Variables         ####
	##########################################
	### Source - K2520, K2604B, B2902A, or LDC3908
	Source = 'K2520'
	Source_channel = 1 #1-8, A or B, for two channel sources only (ignored for one channel)
	initial_current = 1 #[mA]
	waveform = "DC" #pulsed or DC
	pulse_delay = 160e-6 #delay between pulses [s] (pulsed mode only)
	pulse_width = 8e-6 #width of pulses [s] (pulsed mode only)
	protection_voltage = 4 #[V]
	protection_current = 0.1 #[A]
	### Power Meter
	Power_meter_channel_1 = 'A' #A or B, for two channel Newport only (ignored for one channel)
	Power_meter_channel_2 = 'B' #A, B, or OFF for two channel Newport only (ignored for one channel)
	### Spectrum Analyzer - A86146B, A86142A, AQ6317B, AQ6374, or E4407B
	spectrum_analyzer = 'AQ6317B'
	spectrum_analyzer_channel = 'A' #A-C for AQ6317B, A-F for A8614x, A-G for AQ6374, or 1-3 for E4407B
	##########################################
	####            Main Code             ####
	##########################################
	### Connect to Lab Equipment
	# Source
	if Source != 'OFF':
		Source_inst = connect_to_GPIB(Source,['Current',Source_channel,protection_voltage,protection_current,waveform,pulse_delay,pulse_width])
		Source_inst.set_value(initial_current*1e-3)
		print(" Initialized",Source)
	# Power Meter
	if Power_meter_channel_1 != 'OFF' or Power_meter_channel_2 != 'OFF':
		PM_inst = connect_to_PM(Power_meter_channel_1)
		if Power_meter_channel_2 != 'OFF':
			PM_inst.set_channel(Power_meter_channel_2)
			PM_inst.set_wavelength(780)
			PM_inst.set_filtering(0)
			PM_inst.set_autorange(1)
		if Power_meter_channel_1 != 'OFF':
			PM_inst.set_channel(Power_meter_channel_1)
			PM_inst.set_wavelength(780)
			PM_inst.set_filtering(0)
			PM_inst.set_autorange(1)
		print(" Initialized Newport Power Meter")
	# Spectrum Analyzer
	if spectrum_analyzer != 'OFF':
		spectrum_analyzer_inst = connect_to_GPIB(spectrum_analyzer)
		spectrum_analyzer_inst.set_wavelength(790)
		spectrum_analyzer_inst.set_span(20)
		spectrum_analyzer_inst.set_rbw(0.01)
		if spectrum_analyzer in ['AQ6317B', 'AQ6374']:
			spectrum_analyzer_inst.set_sensitivity('MID')
		else:
			spectrum_analyzer_inst.set_vbw(500)
		print(" Initialized",spectrum_analyzer)

if __name__ == "__main__":
	Res_Check()
