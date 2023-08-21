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
		#return Newport_Piezo_Interface.Newport_piezo(rm,port,channel)
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
	for i in range(y_max_index-1,-1,-1):
		if y[i]<=width_y:
			FW_start = x[i+1]
			break
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

def SechSqr(x, offset, amplitude, center, width):
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