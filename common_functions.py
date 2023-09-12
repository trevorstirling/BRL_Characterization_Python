#########################################################################
# A collection of common functions used by characterization and 		#
# analysis scripts 														#
#																		#
# Author: Trevor Stirling												#
# Date: Aug 21, 2023													#
#########################################################################

import pyvisa
import os
import sys
import math
from datetime import date
from scipy.optimize import curve_fit
import numpy as np
import matplotlib.pyplot as plt
import PySimpleGUI as psg

if sys.platform == "win32":
	from ctypes import c_int,c_bool,byref, windll
	os.system("") #required to make coloured cmd output work

class colour:
	darkcyan = '\033[36m'
	red = '\033[91m'
	green = '\033[92m'
	yellow = '\033[93m'
	blue = '\033[94m'
	purple = '\033[95m'
	cyan = '\033[96m'
	white = '\033[97m'
	bold = '\033[1m'
	underline = '\033[4m'
	alert = '\a'
	end = '\033[0m'

def connect_to_PM(channel):
	from Interfaces import Newport_PM_Interface
	if sys.platform == "win32":
		address = r'C:\Program Files\Newport\Newport USB Driver\Bin\usbdll.dll'
		num_devices = c_int()
		windll.LoadLibrary(address).newp_usb_open_devices(c_int(0xCEC7), c_bool(1), byref(num_devices))
		if num_devices.value != 0:
			print(" Connected to Newport Power Meter via USB")
			return Newport_PM_Interface.Newport_PM("", address, channel)
		raise Exception(colour.red+colour.alert+" Could not connect to Newport Power Meter"+colour.end)
	else:
		possible_addresses = ['USB0::0x104D::0xCEC7::NI-VISA-340787200::RAW','USB0::0x104D::0xCEC7::NI-VISA-336592896::RAW','USB0::0x104D::0xCEC7::NI-VISA-339738624::RAW','USB0::0x104D::0xCEC7::NI-VISA-341835776::RAW'] #Required on mac only, specific to each computer
		rm = pyvisa.ResourceManager()
		USB_connection = rm.list_resources('?*')
		if (len(USB_connection) <1):
			raise Exception(colour.red+colour.alert+" No USB devices detected. You may need to restart the computer."+colour.end)
		for address in possible_addresses:
			if address in USB_connection:
				print(" Connected to Power Meter at",address)
				return Newport_PM_Interface.Newport_PM(rm, address, channel)
		raise Exception(colour.red+colour.alert+" No device found at any of "+str(possible_addresses)+" "+colour.end)

def connect_to_Piezo(port, channel, axis):
	import serial
	from Interfaces import Newport_Piezo_Interface
	if sys.platform == "win32":
		return Newport_Piezo_Interface.Newport_Piezo("", port, channel, axis)
	else:
		#return Newport_Piezo_Interface.Newport_piezo(rm,port,channel,axis)
		raise Exception(colour.red+colour.alert+" Not yet configured for MacOS"+colour.end)

def connect_to_GPIB(device_name,parameters=[]):
	if device_name == 'LDC3908':
		num_params = 7 #Source_mode,Source_channel,protection_voltage,protection_current,waveform,pulse_delay,pulse_width
		if len(parameters)<num_params:
			raise Exception(colour.red+colour.alert+" "+device_name+" requires "+str(num_params)+" parameters"+colour.end)
		from Interfaces import LDC3900_Interface
		GPIB_address = 'GPIB0::2::INSTR'
		rm = check_GPIB_connection(device_name, GPIB_address)
		device_inst = LDC3900_Interface.LDC3900(rm, GPIB_address, parameters[1], parameters[0],8)
		device_type = 'Source'
	elif device_name == 'LDC3916':
		num_params = 7 #Source_mode,Source_channel,protection_voltage,protection_current,waveform,pulse_delay,pulse_width
		if len(parameters)<num_params:
			raise Exception(colour.red+colour.alert+" "+device_name+" requires "+str(num_params)+" parameters"+colour.end)
		from Interfaces import LDC3900_Interface
		GPIB_address = 'GPIB0::5::INSTR'
		rm = check_GPIB_connection(device_name, GPIB_address)
		device_inst = LDC3900_Interface.LDC3900(rm, GPIB_address, parameters[1], parameters[0],16)
		device_type = 'Source'
	elif device_name == 'SR830':
		from Interfaces import SR830_Interface
		GPIB_address = 'GPIB0::8::INSTR'
		rm = check_GPIB_connection(device_name, GPIB_address)
		device_inst = SR830_Interface.SR830(rm, GPIB_address)
		device_type = 'Amplifier'
	elif device_name == 'SWS15101':
		from Interfaces import SWS15101_Interface
		GPIB_address = 'GPIB0::10::INSTR'
		rm = check_GPIB_connection(device_name, GPIB_address)
		device_inst = SWS15101_Interface.SWS15101(rm, GPIB_address)
		device_type = 'Laser'
	elif device_name == 'K2604B':
		num_params = 7 #Source_mode,Source_channel,protection_voltage,protection_current,waveform,pulse_delay,pulse_width
		if len(parameters)<num_params:
			raise Exception(colour.red+colour.alert+" "+device_name+" requires "+str(num_params)+" parameters"+colour.end)
		from Interfaces import K2604B_Interface
		GPIB_address = 'GPIB0::16::INSTR'
		rm = check_GPIB_connection(device_name, GPIB_address)
		device_inst = K2604B_Interface.K2604B(rm, GPIB_address, parameters[1], parameters[0])
		device_type = 'Source'
	elif device_name == 'AQ6317B':
		from Interfaces import AQ6317B_Interface
		GPIB_address = 'GPIB0::22::INSTR' #SYSTEM > MY ADRS
		rm = check_GPIB_connection(device_name, GPIB_address)
		device_inst = AQ6317B_Interface.AQ6317B(rm, GPIB_address)
		device_type = 'Spectrum_anlyzer'
	elif device_name == 'AQ6374':
		from Interfaces import AQ6374_Interface
		GPIB_address = 'GPIB0::22::INSTR' #Should change this to be different from AQ6317B
		rm = check_GPIB_connection(device_name, GPIB_address)
		device_inst = AQ6374_Interface.AQ6374(rm, GPIB_address)
		device_type = 'Spectrum_anlyzer'
	elif device_name == 'E4407B':
		from Interfaces import E4407B_Interface
		GPIB_address = 'GPIB0::18::INSTR'
		rm = check_GPIB_connection(device_name, GPIB_address)
		device_inst = E4407B_Interface.E4407B(rm, GPIB_address)
		device_type = 'Spectrum_anlyzer'
	elif device_name == 'B2902A':
		num_params = 7 #Source_mode,Source_channel,protection_voltage,protection_current,waveform,pulse_delay,pulse_width
		if len(parameters)<num_params:
			raise Exception(colour.red+colour.alert+" "+device_name+" requires "+str(num_params)+" parameters"+colour.end)
		from Interfaces import B2902A_Interface
		GPIB_address = 'GPIB0::23::INSTR'
		rm = check_GPIB_connection(device_name, GPIB_address)
		device_inst = B2902A_Interface.B2902A(rm, GPIB_address, parameters[1], parameters[0])
		device_type = 'Source'
	elif device_name == 'A86146B':
		from Interfaces import A8614x_Interface
		GPIB_address = 'GPIB0::24::INSTR'
		rm = check_GPIB_connection(device_name, GPIB_address)
		device_inst = A8614x_Interface.A8614x(rm, GPIB_address)
		device_type = 'Spectrum_anlyzer'
	elif device_name == 'A86142A':
		from Interfaces import A8614x_Interface
		GPIB_address = 'GPIB0::20::INSTR'
		rm = check_GPIB_connection(device_name, GPIB_address)
		device_inst = A8614x_Interface.A8614x(rm, GPIB_address)
		device_type = 'Spectrum_anlyzer'
	elif device_name == 'K2520':
		num_params = 7 #Source_mode,Source_channel,protection_voltage,protection_current,waveform,pulse_delay,pulse_width
		if len(parameters)<num_params:
			raise Exception(colour.red+colour.alert+" "+device_name+" requires "+str(num_params)+" parameters"+colour.end)
		from Interfaces import K2520_Interface
		GPIB_address = 'GPIB0::25::INSTR'
		rm = check_GPIB_connection(device_name, GPIB_address)
		device_inst = K2520_Interface.K2520(rm, GPIB_address, parameters[1], parameters[0])
		device_type = 'Source'
	elif device_name.lower() == 'off':
		return 'off'
	else:
		raise Exception(colour.red+colour.alert+" "+device_name+" is not set up for communication"+colour.end)
	if device_type == 'Source':
		if parameters[0] == 'Current':
			device_inst.set_voltage_protection(parameters[2])
		elif parameters[0] == 'Voltage':
			device_inst.set_current_protection(parameters[3])
		else:
			raise Exception(colour.red+colour.alert+" "+Source+" mode must be either Current or Voltage"+colour.end)
		if parameters[4].lower() == "pulsed":
			device_inst.set_waveform('PULSED', parameters[5], parameters[6])
		elif parameters[4].lower() == "dc":
			device_inst.set_waveform('DC')
		else:
			raise Exception(colour.red+colour.alert+" Type must be either pulsed or DC"+colour.end)
	return device_inst

def check_GPIB_connection(device,GPIB_address):
	rm = pyvisa.ResourceManager()
	GPIB_connection = rm.list_resources()
	if (len(GPIB_connection) <1):
		raise Exception(colour.red+colour.alert+" No GPIB devices detected. You may need to restart the computer."+colour.end)
	if GPIB_address in GPIB_connection:
		print(" Connected to",device,"via",GPIB_address)
	else:
		raise Exception(colour.red+colour.alert+" No device found at "+GPIB_address+". Check that the "+device+" is configured to this address."+colour.end)
	return rm

def check_or_make_directory(dir_path):
	if not os.path.isdir(dir_path):
		os.makedirs(dir_path)
		print(" Created new directory:", dir_path)

def get_unique_file_path(directory, old_name, extension):
	file_path = os.path.join(directory,old_name+extension)
	if os.path.isfile(file_path):
		name = input(colour.red+colour.alert+" "+file_path+" already exists. Press enter to overwrite, or enter a new name (excluding path and extension):\n"+colour.end)
		if name == "":
			return file_path, old_name
		else:
			file_path = get_unique_file_path(directory, name, extension)
	else:
		name = old_name
	return file_path, name

def get_file_locations(save_data, save_fig, characterization_directory, subfolder_name, device_name, folder_date=date.today().strftime("%Y_%m_%d")):
	csv_location = ''
	png_location = ''
	if save_data or save_fig:
		main_directory = os.path.join(characterization_directory,folder_date,subfolder_name)
		if save_data:
			data_directory = os.path.join(main_directory,'Data')
			check_or_make_directory(data_directory)
			device_name = get_unique_file_path(data_directory, device_name, '.csv')[1] #ensures unique name to avoid overwriting data
			csv_location = os.path.join(data_directory,device_name + '.csv')
		if save_fig:
			figure_directory = os.path.join(main_directory,'Figures')
			check_or_make_directory(figure_directory)
			device_name = get_unique_file_path(figure_directory, device_name, '.png')[1] #ensures unique name to avoid overwriting data
			png_location = os.path.join(figure_directory,device_name + '.png')
	return [csv_location, png_location, device_name]

def plot_LIV(device_name, power, current, voltage, show_best_fit=True, show_best_fit_numbers=True, plot_current_density=False, current_area=1, power2=False):
	#If plotting current density, expects area to be [cm^-2]
	#Calculate figure values
	power = [(x - power[0])*1000 for x in power] #converts from [W] to [mW] and zeros background
	if power2:
		power2 = [(x - power2[0])*1000 for x in power2] #converts from [W] to [mW] and zeros background
	current = [x*1000 for x in current] #converts from [A] to [mA]
	#Curve fit to piecewise linear function
	if len(power)<4:
		#can not curve fit
		good_fit = False
		threshold_current = 0
		post_thresh_slope = 0
	else:
		peak = max(power[0],power[1],power[2],power[3])
		for increasing_ends in range(4,len(power)):
			if power[increasing_ends] > peak:
				peak = power[increasing_ends]
			elif power[increasing_ends] < peak-.05:
				break
		current_fit = current[0:increasing_ends]
		power_fit = power[0:increasing_ends]
		threshold_estimate = (min(current_fit)+max(current_fit))/2
		dark_power_estimate = 0 #[mW]
		pre_thresh_slope_estimate = 0.001 #[mW/mA/facet]
		post_thresh_slope_estimate = 0.05 #[mW/mA/facet]
		estimate = [threshold_estimate, dark_power_estimate, pre_thresh_slope_estimate, post_thresh_slope_estimate]
		params,cov = curve_fit(piecewise_linear, current_fit, power_fit, estimate)
		threshold_current = params[0] #[mA]
		pre_thresh_slope = params[2] #[mW/mA/facet]
		post_thresh_slope = params[3] #[mW/mA/facet]
		if cov[0][0]<0:
			sd = math.inf
		else:
			sd = cov[0][0]**0.5
		good_fit = False
		#Check if standard deviation on threshold current is within 1/10 of the value chosen - experimental, consider changing to a better test
		if sd < threshold_current/10 and post_thresh_slope>pre_thresh_slope*1.5:
			good_fit = True
	#Format figure
	fig, ax1 = plt.subplots()
	plt.title(str(device_name))
	plt_colour = 'tab:blue'
	ax1.set_ylabel('Voltage [V]', color=plt_colour)
	if plot_current_density:
		ax1.plot([i/current_area/1000/1000 for i in current], voltage, color=plt_colour)
	else:
		ax1.plot(current, voltage, color=plt_colour)
	ax1.tick_params(axis='y', labelcolor=plt_colour)
	ax2 = ax1.twinx()
	plt_colour = 'tab:red'
	plt_colour_2 = 'tab:purple'
	ax2.set_ylabel('Power [mW]', color=plt_colour)
	if good_fit and show_best_fit:
		if plot_current_density:
			ax2.plot([i/current_area/1000/1000 for i in current_fit], piecewise_linear(current_fit,*params),'--',color='black',label='_nolegend_')
		else:
			ax2.plot(current_fit, piecewise_linear(current_fit,*params),'--',color='black',label='_nolegend_')
	if plot_current_density:
		ax2.plot([i/current_area/1000/1000 for i in current], power, color=plt_colour)
		x_label_string = 'Current Density [kA/cm^2]'
		if power2:
			ax2.plot([i/current_area/1000/1000 for i in current], power2, color=plt_colour_2)
	else:
		ax2.plot(current, power, color=plt_colour)
		x_label_string = 'Current [mA]'
		if power2:
			ax2.plot(current, power2, color=plt_colour_2)
	if good_fit and show_best_fit_numbers:
		ax1.set_xlabel(x_label_string+'\n\nThreshold current = '+"{:.1f}".format(threshold_current)+' mA\nSlope efficiency = '+"{:.1f}".format(post_thresh_slope*1000)+' mW/A/facet')
	else:
		ax1.set_xlabel(x_label_string)
	ax2.tick_params(axis='y', labelcolor=plt_colour)
	plt.tight_layout()
	if power2:
		ax2.legend(['Right facet', 'Left facet'])
	return [fig, threshold_current, post_thresh_slope, good_fit]

def find_FW(x,y,width_y):
	y = [i for i in y] #convert to list in case of numpy array
	y_max_index = y.index(max(y))
	for i in range(y_max_index,len(y)):
		if y[i]<=width_y:
			FW_end = x[i-1]
			break
	if i == len(y)-1:
		FW_end = x[-1]
	for i in range(y_max_index-1,-1,-1):
		if y[i]<=width_y:
			FW_start = x[i+1]
			break
	if i == 0:
		FW_start = x[0]
	FWHM = FW_end-FW_start
	return [FWHM,FW_start,FW_end]

def piecewise_linear(x, x0, b, m1, m2):
	condlist = [x < x0, x >= x0]
	funclist = [lambda x: m1*x + b, lambda x: m1*x + b + m2*(x-x0)]
	return np.piecewise(x, condlist, funclist)

def plot_spectrum(device_name, x_data, power, show_max=False, show_max_numbers=True, show_SMSR=False, peak_width=15, show_FWHM=False, x_is_freq=False):
	#Find peak power
	if x_is_freq:
		max_index = np.argmax(power[1:])+1
	else:
		max_index = np.argmax(power)
	max_x = x_data[max_index]
	max_power = power[max_index]
	#Find SMSR
	peaks = []
	peak_power = []
	peak_distance = int((peak_width-1)/2)
	for i in np.arange(1+peak_distance,len(power)-peak_distance,1):
		if (i < max_index-peak_distance or i > max_index+peak_distance) and power[i] == max(power[i-peak_distance:i+peak_distance]):
			peaks.append(i)
			peak_power.append(power[i])
	SM_index = peak_power.index(max(peak_power))
	SM_power = peak_power[SM_index]
	SM_x = x_data[peaks[SM_index]]
	SMSR = max_power-SM_power;
	#Format figure
	fig, ax = plt.subplots()
	plt.title(str(device_name))
	ax.plot(x_data, power)
	if show_SMSR:
		plt.annotate(text='', xy=(SM_x,SM_power), xytext=(SM_x,max_power), arrowprops=dict(arrowstyle='<->'))
		SMSR_text = plt.text(SM_x,SM_power+SMSR/2,' SMSR = '+str(round(SMSR,2))+' dB ')
		if (x_data[-1]+x_data[0])/2 < SM_x:
			plt.setp(SMSR_text,'horizontalalignment','right')
	HM = max(power)-10*math.log10(2)
	[FWHM,FW_start,FW_end] = find_FW(x_data,power,HM)
	if show_FWHM:
		FWHM_arrow_length = (x_data[-1]-x_data[0])/6
		plt.annotate(text='', xy=(max(FW_start-FWHM_arrow_length,x_data[0]),HM), xytext=(FW_start,HM), arrowprops=dict(arrowstyle='<-'))
		plt.annotate(text='', xy=(min(FW_end+FWHM_arrow_length,x_data[-1]),HM), xytext=(FW_end,HM), arrowprops=dict(arrowstyle='<-'))
		if (x_data[-1]+x_data[0])/2 < (FW_start+FW_end)/2:
			FHWM_text_x = FW_start
		else:
			FHWM_text_x = FW_end
		if x_is_freq:
			FWHM_text = plt.text(FHWM_text_x,HM+3,' FWHM = '+str(round(FWHM,2))+' GHz ')
		else:
			FWHM_text = plt.text(FHWM_text_x,HM+3,' FWHM = '+str(round(FWHM,2))+' nm ')
		if (x_data[-1]+x_data[0])/2 < (FW_start+FW_end)/2:
			plt.setp(FWHM_text,'horizontalalignment','right')
	if show_max:
		ax.plot(max_x, max_power, 'ok', markerfacecolor="None")
	if show_max_numbers:
		if x_is_freq:
			ax.set_xlabel('Frequency [GHz]\n\nMax Power ='+"{:.1f}".format(max_power)+' dBm at '+"{:.2f}".format(max_x)+' GHz')
		else:
			ax.set_xlabel('Wavelength [nm]\n\nMax Power ='+"{:.1f}".format(max_power)+' dBm at '+"{:.2f}".format(max_x)+' nm')
	else:
		if x_is_freq:
			ax.set_xlabel('Frequency [GHz]')
		else:
			ax.set_xlabel('Wavelength [nm]')
	ax.set_ylabel('Power [dBm]')
	plt.tight_layout()
	return [fig, max_x, max_power, SMSR, FWHM]

def SechSqr(x, offset, amplitude, center, width, suppress_overflow=True):
	if suppress_overflow:
		import warnings
		warnings.filterwarnings("ignore", message="overflow encountered in ")
	return offset+amplitude/(np.cosh((x-center)/width)**2)

def envelope_indices(s, trough_reduction_factor=1, peak_reduction_factor=1):
	#Finds the indices of every trough and peak, or every trough_reduction_factor troughs and peak_reduction_factor peaks.
	s = np.array(s)
	extrema = -np.diff(np.sign(np.diff(s)))
	trough_indices = (extrema < 0).nonzero()[0]+1
	trough_indices_reduced = trough_indices[[i+np.argmin(s[trough_indices[i:i+trough_reduction_factor]]) for i in range(0,len(trough_indices),trough_reduction_factor)]]
	peak_indices = (extrema > 0).nonzero()[0]+1
	peak_indices_reduced = peak_indices[[i+np.argmax(s[peak_indices[i:i+peak_reduction_factor]]) for i in range(0,len(peak_indices),peak_reduction_factor)]]
	return trough_indices_reduced,peak_indices_reduced

def plot_autocorrelator(device_name, time, intensity, envelope_reduction_factor=20, plot_fit=True, plot_envelope=False, plot_lower=False, x_axis_calibrated=True, normalize=True, cutoff_freq=200e12):
	fit_type = 'low_pass' #Should always be 'low_pass', left the option for 'envelope' to accomodate legacy code, but low_pass has been shown to be more mathematically sound
	if normalize: #normalize to a peak of 8 for an interferometric autocorrelation
		intensity_max = max(intensity)
		intensity = [i*8/intensity_max for i in intensity]
	intensity = np.array(intensity) #[A.U.]
	time = np.array(time) #[fs]
	if fit_type == 'envelope':
		lower_envelope_index, upper_envelope_index = envelope_indices(intensity, envelope_reduction_factor, envelope_reduction_factor)
		#estimate upper envelope fitting parameters and fit
		upper_offset_estimate = np.mean(intensity[upper_envelope_index[0:5]])
		width_estimate = 200 #[fs]
		max_index = np.argmax(intensity)
		max_time = time[max_index]
		upper_params,_ = curve_fit(SechSqr,time[upper_envelope_index],intensity[upper_envelope_index], p0=[upper_offset_estimate, 1-upper_offset_estimate, max_time, width_estimate])
		upper_params[3] = abs(upper_params[3]) #ensure width is positive
		FWHM = upper_params[3]*1.7627 #[fs]
		if plot_lower:
			#estimate lower envelope fitting parameters and fit
			lower_offset_estimate = np.mean(intensity[lower_envelope_index[0:5]])
			min_index = np.argmin(intensity)
			min_time = time[min_index]
			lower_params,_ = curve_fit(SechSqr,time[lower_envelope_index],intensity[lower_envelope_index], p0=[lower_offset_estimate, 0-upper_offset_estimate, min_time, FWHM])
		#incease fitted curve resolution 
		time_mesh = np.linspace(time[0],time[-1],1000)
		#Format figure
		fig, ax1 = plt.subplots()
		plt.plot(time,intensity,color='0.8')
		# legend_string = ["Measured Data","Sech^2"]
		if x_axis_calibrated:
			x_axis_text = 'Time [fs]'
		else:
			x_axis_text = 'Number of data points [uncalibrated]'
		if plot_envelope:
			plt.plot(time[upper_envelope_index],intensity[upper_envelope_index],color='0.1',label='_nolegend_')
			if plot_lower:
				plt.plot(time[lower_envelope_index],intensity[lower_envelope_index],color='0.1',label='_nolegend_')
		if plot_fit:
			plt.plot(time_mesh,SechSqr(time_mesh,*upper_params))
			if x_axis_calibrated:
				x_axis_text += '\nAutocorrelator sech$^2$ FWHM '+"{:.1f}".format(FWHM)+' fs\nCorresponding pulse FWHM '+"{:.1f}".format(FWHM/1.54)+' fs'
			else:
				x_axis_text += '\nAutocorrelator sech$^2$ FWHM '+"{:.1f}".format(FWHM)+' data points\nCorresponding pulse FWHM '+"{:.1f}".format(FWHM/1.54)+' data points'
			if plot_lower:
				plt.plot(time_mesh,SechSqr(time_mesh,*lower_params))
				if x_axis_calibrated:
					x_axis_text += '\nLower autocorrelator sech$^2$ FWHM '+"{:.1f}".format(lower_params[3])+' fs\nCorresponding lower pulse FWHM '+"{:.1f}".format(lower_params[3]/1.54)+' fs'
				else:
					x_axis_text += '\nLower autocorrelator sech$^2$ FWHM '+"{:.1f}".format(lower_params[3])+' data points\nCorresponding lower pulse FWHM '+"{:.1f}".format(lower_params[3]/1.54)+' data points'
		plt.xlabel(x_axis_text)
		plt.ylabel('Intensity [A.U.]')
		plt.title(device_name)
	elif fit_type == 'low_pass':
		#Filter
		Intensity_freq = np.fft.rfft(intensity)
		f = np.fft.rfftfreq(len(time),(time[1]-time[0])*1e-15)
		Intensity_low_freq = [Intensity_freq[i] if f[i]<=cutoff_freq else 0 for i in range(len(Intensity_freq))]
		intensity_low = np.fft.irfft(Intensity_low_freq)
		#Fit
		max_index = np.argmax(intensity_low)
		max_time = time[max_index]
		offset_estimate = abs(Intensity_freq[0])/len(intensity)
		width_estimate = 100 #[fs]
		filtered_params,_ = curve_fit(SechSqr,time,intensity_low, p0=[offset_estimate, 4-offset_estimate, max_time, width_estimate])
		filtered_params[3] = abs(filtered_params[3]) #ensure width is positive
		FWHM = filtered_params[3]*1.7627 #[fs]
		#incease fitted curve resolution 
		time_mesh = np.linspace(time[0],time[-1],1000)
		#Format figure
		fig, ax1 = plt.subplots()
		plt.plot(time,intensity,color='0.8')
		if x_axis_calibrated:
			x_axis_text = 'Time [fs]'
		else:
			x_axis_text = 'Number of data points [uncalibrated]'
		if plot_fit:
			plt.plot(time_mesh,SechSqr(time_mesh,*filtered_params))
			if x_axis_calibrated:
				x_axis_text += '\nAutocorrelator sech$^2$ FWHM '+"{:.1f}".format(FWHM)+' fs\nCorresponding pulse FWHM '+"{:.1f}".format(FWHM/1.54)+' fs'
			else:
				x_axis_text += '\nAutocorrelator sech$^2$ FWHM '+"{:.1f}".format(FWHM)+' data points\nCorresponding pulse FWHM '+"{:.1f}".format(FWHM/1.54)+' data points'
		plt.xlabel(x_axis_text)
		plt.ylabel('Intensity [A.U.]')
		plt.title(device_name)
	else:
		raise Exception(colour.red+colour.alert+"The autocorrelation fit type should be low_pass or envelope, but was "+str(fit_type)+colour.end)
	return [fig,FWHM/1.54]

def loading_bar(ratio_complete,total_length=50,terminate=False):
	if ratio_complete<0 or ratio_complete>1:
		raise Exception(colour.red+colour.alert+"The argument of loading_bar should be between 0 and 1, but was "+str(ratio_complete)+colour.end)
	if terminate == True:
		end_line="\n"
	else:
		end_line="\r"
	complete_length = int(total_length*ratio_complete)
	bar = '█' * complete_length + '-' * (total_length - complete_length)
	print(f'\r |{bar}| {int(ratio_complete*100)}%', end=end_line)
	# Print New Line on Complete
	if ratio_complete == 1: 
		print()

#Move to common functions when done
def BluePSGButton(text):
	rounded_blue_button = b'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/GMzLdsAAFTiaVRYdFhNTDpjb20uYWRvYmUueG1wAAAAAAA8P3hwYWNrZXQgYmVnaW49Iu+7vyIgaWQ9Ilc1TTBNcENlaGlIenJlU3pOVGN6a2M5ZCI/Pgo8eDp4bXBtZXRhIHhtbG5zOng9ImFkb2JlOm5zOm1ldGEvIiB4OnhtcHRrPSJBZG9iZSBYTVAgQ29yZSA1LjYtYzE0NSA3OS4xNjIzMTksIDIwMTgvMDIvMTUtMjA6Mjk6NDMgICAgICAgICI+CiAgIDxyZGY6UkRGIHhtbG5zOnJkZj0iaHR0cDovL3d3dy53My5vcmcvMTk5OS8wMi8yMi1yZGYtc3ludGF4LW5zIyI+CiAgICAgIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiCiAgICAgICAgICAgIHhtbG5zOnhtcD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLyIKICAgICAgICAgICAgeG1sbnM6eG1wTU09Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9tbS8iCiAgICAgICAgICAgIHhtbG5zOnN0RXZ0PSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VFdmVudCMiCiAgICAgICAgICAgIHhtbG5zOnBob3Rvc2hvcD0iaHR0cDovL25zLmFkb2JlLmNvbS9waG90b3Nob3AvMS4wLyIKICAgICAgICAgICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICAgICAgICAgICB4bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyIKICAgICAgICAgICAgeG1sbnM6ZXhpZj0iaHR0cDovL25zLmFkb2JlLmNvbS9leGlmLzEuMC8iPgogICAgICAgICA8eG1wOkNyZWF0b3JUb29sPkFkb2JlIFBob3Rvc2hvcCBFbGVtZW50cyAxNy4wIChXaW5kb3dzKTwveG1wOkNyZWF0b3JUb29sPgogICAgICAgICA8eG1wOkNyZWF0ZURhdGU+MjAyMC0xMC0wM1QxMTowOTowOS0wNDowMDwveG1wOkNyZWF0ZURhdGU+CiAgICAgICAgIDx4bXA6TWV0YWRhdGFEYXRlPjIwMjAtMTAtMDNUMTE6MDk6MDktMDQ6MDA8L3htcDpNZXRhZGF0YURhdGU+CiAgICAgICAgIDx4bXA6TW9kaWZ5RGF0ZT4yMDIwLTEwLTAzVDExOjA5OjA5LTA0OjAwPC94bXA6TW9kaWZ5RGF0ZT4KICAgICAgICAgPHhtcE1NOkluc3RhbmNlSUQ+eG1wLmlpZDowNDFhMDAwNy1lMGJlLTk4NGYtODNlMy01ZGQxZTk2NjI5ZWQ8L3htcE1NOkluc3RhbmNlSUQ+CiAgICAgICAgIDx4bXBNTTpEb2N1bWVudElEPmFkb2JlOmRvY2lkOnBob3Rvc2hvcDo1YjgyOTQ2Mi0wNThhLTExZWItOTQ3ZC04N2E5Njc3OWZkYzU8L3htcE1NOkRvY3VtZW50SUQ+CiAgICAgICAgIDx4bXBNTTpPcmlnaW5hbERvY3VtZW50SUQ+eG1wLmRpZDoxMWMzOWY4MS0xM2VmLWIzNGMtYWNkMy0xZTVjMTI5OWNmMGM8L3htcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD4KICAgICAgICAgPHhtcE1NOkhpc3Rvcnk+CiAgICAgICAgICAgIDxyZGY6U2VxPgogICAgICAgICAgICAgICA8cmRmOmxpIHJkZjpwYXJzZVR5cGU9IlJlc291cmNlIj4KICAgICAgICAgICAgICAgICAgPHN0RXZ0OmFjdGlvbj5jcmVhdGVkPC9zdEV2dDphY3Rpb24+CiAgICAgICAgICAgICAgICAgIDxzdEV2dDppbnN0YW5jZUlEPnhtcC5paWQ6MTFjMzlmODEtMTNlZi1iMzRjLWFjZDMtMWU1YzEyOTljZjBjPC9zdEV2dDppbnN0YW5jZUlEPgogICAgICAgICAgICAgICAgICA8c3RFdnQ6d2hlbj4yMDIwLTEwLTAzVDExOjA5OjA5LTA0OjAwPC9zdEV2dDp3aGVuPgogICAgICAgICAgICAgICAgICA8c3RFdnQ6c29mdHdhcmVBZ2VudD5BZG9iZSBQaG90b3Nob3AgRWxlbWVudHMgMTcuMCAoV2luZG93cyk8L3N0RXZ0OnNvZnR3YXJlQWdlbnQ+CiAgICAgICAgICAgICAgIDwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpIHJkZjpwYXJzZVR5cGU9IlJlc291cmNlIj4KICAgICAgICAgICAgICAgICAgPHN0RXZ0OmFjdGlvbj5zYXZlZDwvc3RFdnQ6YWN0aW9uPgogICAgICAgICAgICAgICAgICA8c3RFdnQ6aW5zdGFuY2VJRD54bXAuaWlkOjA0MWEwMDA3LWUwYmUtOTg0Zi04M2UzLTVkZDFlOTY2MjllZDwvc3RFdnQ6aW5zdGFuY2VJRD4KICAgICAgICAgICAgICAgICAgPHN0RXZ0OndoZW4+MjAyMC0xMC0wM1QxMTowOTowOS0wNDowMDwvc3RFdnQ6d2hlbj4KICAgICAgICAgICAgICAgICAgPHN0RXZ0OnNvZnR3YXJlQWdlbnQ+QWRvYmUgUGhvdG9zaG9wIEVsZW1lbnRzIDE3LjAgKFdpbmRvd3MpPC9zdEV2dDpzb2Z0d2FyZUFnZW50PgogICAgICAgICAgICAgICAgICA8c3RFdnQ6Y2hhbmdlZD4vPC9zdEV2dDpjaGFuZ2VkPgogICAgICAgICAgICAgICA8L3JkZjpsaT4KICAgICAgICAgICAgPC9yZGY6U2VxPgogICAgICAgICA8L3htcE1NOkhpc3Rvcnk+CiAgICAgICAgIDxwaG90b3Nob3A6RG9jdW1lbnRBbmNlc3RvcnM+CiAgICAgICAgICAgIDxyZGY6QmFnPgogICAgICAgICAgICAgICA8cmRmOmxpPjAwMDE1N0JCNEVDNjZDODMyQ0VBN0Q0OTgxOEYyQkI3PC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+MEQyMERDMEVCMTBDQkE5Njg5N0M2NzNCRjkwNDI5ODQ8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT4xRDk5RjMzMUY1RkMyOUU0ODU5MkI1OERENENCRkUzMzwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPjI2QzMwRDNBRTREQjZERTFFN0Y2M0JCQUE4NjBGNEI0PC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+MkFFRkE4NTk0ODJBRTMxMEYwOEYxNEVCQkU3MUEyNTU8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT4zNDBDQUZCNkZCMzIwRDRGREVEMjc0M0ExRjUwNUI2ODwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPjQ4NTVBMzI3NzUwOTIzODkwMzQ5NjIwRkU2NUYzNjkxPC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+NjZBREMzOThERjcwMDQ1RDgxMkU4OUMwNDIzRkFGNTA8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT42QjI5MkM4MDQyRTY1QTcxMkZGMTk4NTdEMjhGQTZCRTwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPjczNzQ2N0JGQzU2QkFDNTk2Q0M4QkNEOUUzNjk2QUU1PC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+NzNDMEVENEM3ODE0RTg4RjlBMjQ3NzRFRjdGMTBBODk8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT44MUU0QzY3QjQ5QkFCMzlDNkU5QzExRjQxNUNEMTgyRTwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPkEzQ0M2RjFEQTFDMTFBMDZDOUExOTEyQURDRDBFRjQ3PC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+QTQ3QkZCNkY5NkMxRjBGMjhDMTI5RENCQkZBODRGNkQ8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT5BNTlDQUU4ODNCMzU0RjgyMEQ3OTFEODJCREVGRjE2MDwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPkFGREUyQkMyMzA1QkUyRTc2Q0RCNTdBNDAwNzM3MEQyPC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+Q0Q4RTcxRkQ1REQ3RkM5MjcyNkZFREQ5NDRBREEyMTE8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT5GM0Y5OURGQjBFMzE5QzUwQzRGNEQ2NUZCM0U1QjU5MzwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPkY4REE4QjZDRUM5MDI5OTgzMzUxQkEzQzUyQTVCNzREPC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+YWRvYmU6ZG9jaWQ6cGhvdG9zaG9wOjMyMjNhYzg2LWVkZTYtMTFkOS1hZGRiLWNiMWQ2NjAxOWMxNzwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPmFkb2JlOmRvY2lkOnBob3Rvc2hvcDo2YjM0YmVlZi1mNDg2LTExZDktOWFiYy1mNmY3MDc0YjFkN2E8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT5hZG9iZTpkb2NpZDpwaG90b3Nob3A6NmNjNzJkZDQtYzEyMi0xMWRhLTllYTAtYjQxMDIxN2JjNjA0PC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+YWRvYmU6ZG9jaWQ6cGhvdG9zaG9wOjc4ZTg3ZmZlLWY5NWEtMTFkYi1hZmE5LWY3OGRhN2FiODZmZjwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPmFkb2JlOmRvY2lkOnBob3Rvc2hvcDo5NWFkMzRlOC01MTQwLTExZGEtOGFmNi1iNjQ4NmE1YjIwYjI8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT5hZG9iZTpkb2NpZDpwaG90b3Nob3A6YmViNmY0N2UtMjIzNS0xMWRjLWE0NGUtZjZiOGI4MzA4MWQ1PC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+YWRvYmU6ZG9jaWQ6cGhvdG9zaG9wOmU3ZmI1OGNhLTk2NDItMTFkZC04MWEyLWRkMTQxMDNmNDUxNTwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnV1aWQ6MDFGMUEwRjYxMUVGMTFEQjg4MUVBNkJFMDVFMjc2RDE8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT51dWlkOjA2MDFFMzM5QkFGMkREMTE5QTlEOTEwOTg5NjI4QzVGPC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+dXVpZDoxODkyOTc1OTlFNUREQzExOEQxOUJGODREMUU2QjZEQTwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnV1aWQ6MTk1MDE1MDhFMkVGMTFERDhCRUNDQjZCNDU1MkJFQTc8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT51dWlkOjJBNTJBMDEwMENGNERDMTFBQTAzRUZBRjc4RDI5ODlDPC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+dXVpZDozMEMyMzlCODJFM0JERDExQjY1MUMwNzNDODY5RDI3MzwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnV1aWQ6MzUwMEIwQ0M2QzUwMTFEQ0E1OEE4MUNDRUFFQjk2N0Q8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT51dWlkOjRBMzhCMjREN0NCNkREMTE5ODk5OUZCM0IyMkVFNUNFPC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+dXVpZDo1MDg1RkUxQzVDRjFEQzExODQ5OTlCMkQ0NzNCNDBDNTwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnV1aWQ6NTY5OTMxQUNFRTgyREMxMTk4NkVFQTgzNjFGMTQ3MTE8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT51dWlkOjU3RDRENjNDMDUzN0UwMTFBNjM1RUJFMzgyMzBCODQxPC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+dXVpZDo1RjgzOTA1RDExRUYxMURCODgxRUE2QkUwNUUyNzZEMTwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnV1aWQ6NjI1OTE1RTFEMEYyREQxMUIyQUVGODg5ODVDQTU4Njg8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT51dWlkOjcwNkY4OEYyMzAzQkREMTFCNjUxQzA3M0M4NjlEMjczPC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+dXVpZDo5MEFERjdENTM5OEExMURGODYxMTk0MzZBMTdDQjIyNzwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnV1aWQ6QTFFMjhDNEM1NjI5REMxMTlDNzZCNzZDOEFBMDk4NzQ8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT51dWlkOkE5Rjg5MTI5M0IxQzExREFCNTVCQzI1REIzOTc4NjA2PC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+dXVpZDpCNTdGQjJFRUM4MEJEQzExOURCQThEMjJDNkE3OUM0NzwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnV1aWQ6QkQ1NkJGM0FGQzM4REIxMUEwNzhFRjBBNDMwOTAyRDU8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT51dWlkOkJFREZCQTY5MEM2OERCMTE5NEE0RkFCMjk1MERCMjQ1PC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+dXVpZDpDQUQxM0U4ODMwM0JERDExQjY1MUMwNzNDODY5RDI3MzwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnV1aWQ6RDlGRkY3NkJDMThBRTAxMTk3RTJFNkIyMDZFQUIzOTU8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT51dWlkOkU0NUNENDFBNzdEN0REMTE4NkRFREQ1OEI3N0JFMDkxPC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+dXVpZDpGNkFBNkUxMThCNURFMTExOTE0MUJBNTI3OTk1MzhGMDwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnhtcC5kaWQ6MDE4MDExNzQwNzIwNjgxMTg3MUZFNEFENzFFRTI1QzA8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT54bXAuZGlkOjAxODAxMTc0MDcyMDY4MTE4NzFGRUVCNTZEMUU3NDNCPC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+eG1wLmRpZDowMTgwMTE3NDA3MjA2ODExOEY2MkVCMkFERTQ2RDI3MzwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnhtcC5kaWQ6MDE4MDExNzQwNzIwNjgxMTkxMDlGQTI5N0E3QTU5MDQ8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT54bXAuZGlkOjAxODAxMTc0MDcyMDY4MTE5MkIwQkFBOTA0REUwRjhEPC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+eG1wLmRpZDowMTgwMTE3NDA3MjA2ODExOTdBNURBRjI1ODNBMEE0QjwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnhtcC5kaWQ6MDE4MDExNzQwNzIwNjgxMUFCMDhFOEU4RUUzRjAyODk8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT54bXAuZGlkOjAyODAxMTc0MDcyMDY4MTE4OEM2QTI5ODQ0M0YxMEFDPC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+eG1wLmRpZDowMjgwMTE3NDA3MjA2ODExOTEwOUM2NUE3MDQwMTM0MDwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnhtcC5kaWQ6MEEwOEJDOTI2MUEyREYxMUJCQjVDMUZFMzRDNjY0OEM8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT54bXAuZGlkOjFDOEU5N0FBOEI0QkRGMTE4OTQxQjEwMTZEQkYxRDE0PC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+eG1wLmRpZDoxRjgzQ0M1NjM2RTFFMDExQjc1MzgyQTY2NTdEMjA4RDwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnhtcC5kaWQ6MzE5RTE0NkRCNDM3RTIxMThENjBEQkI0MTU3NjYyQkU8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT54bXAuZGlkOjM2RThEMTc2QkM3QURGMTFBM0M4QzZFMjExRUE4QkJGPC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+eG1wLmRpZDo0RDVFODcxRTE1MTFFMjExOTU1M0RENDcyOUEyMzZDRjwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnhtcC5kaWQ6NTE0MDRGNDMzOTQ0RTIxMUEyMzlDMDRBRkQ0NDQ4MUU8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT54bXAuZGlkOjUxNTQ2RkREMTMyMDY4MTE5MkIwQkFBOTA0REUwRjhEPC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+eG1wLmRpZDo1NDU0NkZERDEzMjA2ODExOTJCMEJBQTkwNERFMEY4RDwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnhtcC5kaWQ6NjM4ODgwRTgwOTIwNjgxMTkyQjBCQUE5MDRERTBGOEQ8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT54bXAuZGlkOjY0ODg4MEU4MDkyMDY4MTE5MkIwQkFBOTA0REUwRjhEPC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+eG1wLmRpZDo2NERGNTM3NjM1RTFFMDExQjc1MzgyQTY2NTdEMjA4RDwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnhtcC5kaWQ6NjY4ODgwRTgwOTIwNjgxMTkyQjBCQUE5MDRERTBGOEQ8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT54bXAuZGlkOjY3ODg4MEU4MDkyMDY4MTE5MkIwQkFBOTA0REUwRjhEPC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+eG1wLmRpZDo2RUQ1RTlDRDZGQzRERjExQjc1QzlCRTFENUIxNkVBMzwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnhtcC5kaWQ6NzNGREFEODU3RUNCRTExMUI1MUVCRkE3RDIwMUNDNEI8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT54bXAuZGlkOjk2MkFGRDIxNjgzOUUyMTE4NzA1ODUzNjA1RUY2MEJBPC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+eG1wLmRpZDpBMzQ3Q0E3MUNFRENFMTExOUJFN0Y0NzJGQzQyQzU4NTwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnhtcC5kaWQ6QTY1Q0FDMUZDOTM3RTIxMThENjBEQkI0MTU3NjYyQkU8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT54bXAuZGlkOkE5Q0NBNkFGRkI0M0UxMTE5RURCRjYzRTA1ODA0MzA0PC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+eG1wLmRpZDpCMjQwMUYyQjk2MzhFMjExQTY2MkI0N0U5QjhENzE0RTwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnhtcC5kaWQ6QkIzNTY1RTgxNTIwNjgxMTkyQjBCQUE5MDRERTBGOEQ8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT54bXAuZGlkOkMyMzU2NUU4MTUyMDY4MTE5MkIwQkFBOTA0REUwRjhEPC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+eG1wLmRpZDpDMzczQ0VDMDM2MjA2ODExOEY2MkQwRjcwMTBBQzAyRjwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnhtcC5kaWQ6Q0I1NzY4QzhGQjNBRTIxMUFBNDNGMUNGRTNEMkUyNTM8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT54bXAuZGlkOkNGMEY3NzJFOUY5MkUwMTFCMDBBQjc4N0Y4ODIyQjQ2PC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+eG1wLmRpZDpEMDczREU4OURFM0VFMjExQkM2QUZERjZBNEZEMTc1RjwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnhtcC5kaWQ6RDQwNTRFQzExOTIwNjgxMTkyQjBCQUE5MDRERTBGOEQ8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT54bXAuZGlkOkRBQTQ4QUM0NzYzRkUyMTE4M0EyQkZEMTQ2NjBDQTJGPC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+eG1wLmRpZDpFMEE0OEFDNDc2M0ZFMjExODNBMkJGRDE0NjYwQ0EyRjwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnhtcC5kaWQ6Rjc1RDkxOEExMTIwNjgxMTkyQjA4QkVFMjlDNzVERDI8L3JkZjpsaT4KICAgICAgICAgICAgICAgPHJkZjpsaT54bXAuZGlkOkY3N0YxMTc0MDcyMDY4MTE4MDgzRUI4M0M2MkJEN0MxPC9yZGY6bGk+CiAgICAgICAgICAgICAgIDxyZGY6bGk+eG1wLmRpZDpGNzdGMTE3NDA3MjA2ODExOTEwOUY4RkUyNzcxOEQ1QTwvcmRmOmxpPgogICAgICAgICAgICAgICA8cmRmOmxpPnhtcC5kaWQ6RkJDNEQyMDQwQTIwNjgxMTkxMDlDQzY0MkM0NEVDMEM8L3JkZjpsaT4KICAgICAgICAgICAgPC9yZGY6QmFnPgogICAgICAgICA8L3Bob3Rvc2hvcDpEb2N1bWVudEFuY2VzdG9ycz4KICAgICAgICAgPHBob3Rvc2hvcDpDb2xvck1vZGU+MzwvcGhvdG9zaG9wOkNvbG9yTW9kZT4KICAgICAgICAgPHBob3Rvc2hvcDpJQ0NQcm9maWxlPnNSR0IgSUVDNjE5NjYtMi4xPC9waG90b3Nob3A6SUNDUHJvZmlsZT4KICAgICAgICAgPGRjOmZvcm1hdD5pbWFnZS9wbmc8L2RjOmZvcm1hdD4KICAgICAgICAgPHRpZmY6T3JpZW50YXRpb24+MTwvdGlmZjpPcmllbnRhdGlvbj4KICAgICAgICAgPHRpZmY6WFJlc29sdXRpb24+NzIwMDAwLzEwMDAwPC90aWZmOlhSZXNvbHV0aW9uPgogICAgICAgICA8dGlmZjpZUmVzb2x1dGlvbj43MjAwMDAvMTAwMDA8L3RpZmY6WVJlc29sdXRpb24+CiAgICAgICAgIDx0aWZmOlJlc29sdXRpb25Vbml0PjI8L3RpZmY6UmVzb2x1dGlvblVuaXQ+CiAgICAgICAgIDxleGlmOkNvbG9yU3BhY2U+MTwvZXhpZjpDb2xvclNwYWNlPgogICAgICAgICA8ZXhpZjpQaXhlbFhEaW1lbnNpb24+MTA5PC9leGlmOlBpeGVsWERpbWVuc2lvbj4KICAgICAgICAgPGV4aWY6UGl4ZWxZRGltZW5zaW9uPjM4PC9leGlmOlBpeGVsWURpbWVuc2lvbj4KICAgICAgPC9yZGY6RGVzY3JpcHRpb24+CiAgIDwvcmRmOlJERj4KPC94OnhtcG1ldGE+CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgCjw/eHBhY2tldCBlbmQ9InciPz4BWge9AAAAIGNIUk0AAHolAACAgwAA+f8AAIDpAAB1MAAA6mAAADqYAAAXb5JfxUYAAAHGSURBVHja7Nu9ihNRHIbx5/xnJpOZaAKbXWIjwUULkTU2rqgoYqM2FnaWfqAXYGWpjbjVegFiue028aPbzgURFuxUtNMNYkSLOJsx59joPZzA+1zC++PMnOa4EAKA3Xq0ceLd59HaZDo746FARVHiqIos2V451Lv39P71HcC7EII9ePbq+Obr91sha3aSrIEz01qRFLxnVk+hrn5eXT188eHtKzsp0Hrzcfexa+7rNIoSS1JwTmtFoxbwsz/UVdp5+2m0BlwzoPfjtz+bFSWWZgKLLeewNCNrlown/jTQM6BbzVzLJakGitkuSZliJbBgQO6SBKcTFvmBczhLAHIDdOuYr3RNnEs1TSA0JTQlNKEpoSmhCU0JTQlNaEpoSmhKaEJTQlNCE5oSmhKa0JTQlNCEpuYIzbfLfKop4m9/0agBb8DeoN/98u9xoYq0EAIr/e5XYM+A73cuD4bt3GaaJt7aufm7lwZDYGzA6OjBxedPbp5/sbrcrZqpfnMxlafGyeXFav3GuZfH+ktDYORCCAYsAaeAC8ARoAXo7VMEX0VgAnwAtoBt4Jv7/1AeaAMHgAUgE1o0aDUwBnaBX4D/CwAA//8DAOgHcZ21310BAAAAAElFTkSuQmCC'
	return psg.Button(text, font=('Tahoma', 12), image_data=rounded_blue_button, button_color=('black', psg.theme_background_color()), mouseover_colors=('#303030', psg.theme_background_color()), border_width=0)

def ordinal_indicator(num):
	if num%10 == 1 and num%100 != 11:
		return 'st'
	elif num%10 == 2 and num%100 != 12:
		return 'nd'
	elif num%10 == 3 and num%100 != 13:
		return 'rd'
	else:
		return 'th'

def matmul2x2(A,B):
	if len(A) == 2 and len(B) == 2:
		if len(A[0]) == 2 and len(A[1]) == 2 and len(B[0]) == 2 and len(B[1]) == 2:
			return [[A[0][0]*B[0][0]+A[0][1]*B[1][0],A[0][0]*B[0][1]+A[0][1]*B[1][1]],[A[1][0]*B[0][0]+A[1][1]*B[1][0],A[1][0]*B[0][1]+A[1][1]*B[1][1]]]
	else:
		raise Exception("A and B must both be 2x2 matrices (as nested lists)")

def calculate_reflectivity(n_vector,d_vector,lambda_vector):
	#Calculates the reflectivity for a wave travelling at normal incidence
	r = [0 for _ in lambda_vector]
	for j in range(len(lambda_vector)):
		k0 = 2*math.pi/lambda_vector[j]
		k_vector = [k0*n for n in n_vector]
		M = [[1,0],[0,1]]
		for i in range(1,len(n_vector)-1):
			k = k_vector[i]
			d = d_vector[i]
			M = matmul2x2(M,[[math.cos(k*d),-1/k*math.sin(k*d)],[k*math.sin(k*d),math.cos(k*d)]])
		gamma_s = k_vector[0]/1j
		gamma_t = k_vector[-1]/1j
		r[j] = (gamma_s*M[0][0]-gamma_s*gamma_t*M[0][1]+M[1][0]-gamma_t*M[1][1])/(gamma_s*M[0][0]-gamma_s*gamma_t*M[0][1]-M[1][0]+gamma_t*M[1][1])
	return r