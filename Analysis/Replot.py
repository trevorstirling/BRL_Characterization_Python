#########################################################################
# Script to replot figures for data previously collected 				#
# e.g. to change plotting options like show_best_fit or show_SMSR		#
#																		#
# Author: Trevor Stirling												#
# Date: May 29, 2023													#
#########################################################################

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from common_functions import plot_LIV, plot_spectrum, plot_autocorrelator, get_file_locations, loading_bar

#Run Options
display_fig = False
save_fig = True
whole_directory = True #If true, device_name is ignored
print_figure_locations = False #boolean to output locations figures are saved to terminal
#Define data location
folder_date = '2023_02_14'
device_name = 'MaiTai_792nm_20uW_minG_512Hz_1700Hz_16000pts' #ignored for whole_directory
plot_type = 'LIV' #LIV, Spectrum or Autocorrelation
#LIV specific options
is_PD_current = False #Should always be false except for old K2520 data which measured current instead of power.
show_best_fit = True
show_best_fit_numbers = True
plot_current_density = True
device_length = 1 #length of device [mm], ignored if plot_current_density = False
injection_width = 2 #average via width [um], ignored if plot_current_density = False
responsivity = 1/1.74 #measured photodiode responsivity [A/W]
#Spectrum specific options
show_max=False
show_max_numbers=True
show_SMSR=False
show_FWHM=False
x_is_freq=False
SMSR_peak_width = 15 #Peak must be highest of neighbouring peak_width total points including peak itself
#Autocorrelator specific options
normalize_autocorrelation = True #True/False
plot_envelope = False
plot_fit = True
plot_lower = False
time_scale_factor = 0.057 #[points/fs] 2.199 for 100Hz
calibration_width = 110 #[fs]
envelope_reduction_factor = 20 #only keep max of every envelope_reduction_factor peaks
#Define constants
if sys.platform == "win32":
	characterization_directory = os.path.join('..','Data')
else:
	characterization_directory = '/Volumes/macOS Mojave/Users/trevorstirling/Documents/Trevor/Research/Characterization/Data/'
if print_figure_locations:
	terminate_loading_bar = True
else:
	terminate_loading_bar = False
if whole_directory:
	all_file_directory = os.path.join(characterization_directory,folder_date,plot_type,'Data')
	all_files = os.listdir(all_file_directory)
	all_files = [file for file in all_files if not file.startswith('.')] #remove .DS_Store
	# all_files = [file for file in all_files if file.endswith('1700Hz_16000pts.csv')] #filter
	all_files.sort()
else:
	all_files = [device_name+'.csv']
loading_bar(0,terminate=terminate_loading_bar)
n_files = len(all_files)
for i,file in enumerate(all_files):
	device_name = file.split('.csv')[0]
	#Import and plot data
	data = np.loadtxt(os.path.join(characterization_directory,folder_date,plot_type,'Data',device_name+'.csv'), delimiter=',', skiprows=1)
	[png_location, device_name] = get_file_locations(0, save_fig, characterization_directory, plot_type, device_name, folder_date)[1:3]
	if plot_type == 'LIV':
		current_area = device_length/10*injection_width/10000
		current = data[:,0] #[A]
		if is_PD_current:
			power = data[:,2]/responsivity #[W]
		else:
			power = data[:,2] #[W]
		voltage = data[:,1] #[V]
		fig = plot_LIV(device_name, power, current, voltage, show_best_fit, show_best_fit_numbers, plot_current_density=plot_current_density, current_area=current_area)[0]
	elif plot_type == 'Spectrum':
		wavelength = data[:,0] #[nm]
		power = data[:,1] #[dBm]
		fig = plot_spectrum(device_name, wavelength, power, show_max, show_max_numbers, show_SMSR, SMSR_peak_width, show_FWHM, x_is_freq)[0]
	elif plot_type == 'Autocorrelation':
		time = data[:,0] #[points]
		time = [j/time_scale_factor for j in time] #convert from points to fs
		intensity = data[:,1] #signal from lock-in channel 1 [mV]
		[fig,FWHM] = plot_autocorrelator(device_name, time, intensity, envelope_reduction_factor=envelope_reduction_factor, plot_fit=plot_fit, plot_envelope=plot_envelope, plot_lower=plot_lower, normalize=normalize_autocorrelation)
		if whole_directory == False:
			print("If calibration run, try new calibration factor of","{:.3f}".format(FWHM*time_scale_factor/calibration_width))
	#Save/display figure
	if save_fig:
		fig.savefig(png_location,bbox_inches='tight')
		if print_figure_locations:
			print(" Figure saved to",png_location)
	if display_fig:
		if plot_type == 'Autocorrelation':
			plt.subplots_adjust(bottom=0.2)
		print(" Displaying figure. Close figure to resume.")
		plt.show()
	else:
		plt.close()
	loading_bar((i+1)/n_files,terminate=terminate_loading_bar)
