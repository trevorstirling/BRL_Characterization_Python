#########################################################################
# Script to reconstruct density matrix using maximum likelihood         #
# from Quantum State Tomography data                                    #
#                                                                       #
# Author: Zach Leger, edited by Trevor Stirling                         #
# Date: May 30, 2024                                                    #
#                                                                       #
# Input files must all have the same name except for the polarization   #
# Names must include bin_width= and int_time= indicating the bin width  #
# in ps and the integration time in s                                   #
#########################################################################

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import QuantumTomography as qKLib
import seaborn as sns

font = {'family':'sans-serif', 'weight':'bold', 'size':14}
plt.rc('font', **font)

### File Information

# main_directory = '/Volumes/macOS Mojave/Users/trevorstirling/Documents/Trevor/Research/Characterization/Data/2024_05_29/QST/Prepped Data'     # Data directory
# device_name_start = "BRL9_AS-SG-G1_T=32C_56mA_"                           # Data name up to polarization
# device_name_end = "_bin_width=50_int_time=10"                             # Data name from polarization onwards (excluding extension)
# main_directory = '/Volumes/macOS Mojave/Users/trevorstirling/Documents/Trevor/Research/Characterization/Data/2024_05_30/QST/Data'     # Data directory
# device_name_start = "BRL9_M-AL_A2_5_154mA_-1.4V_"                         # Data name up to polarization
# device_name_end = "_bin_width=50_num_bins=2000_int_time=5_1"              # Data name from polarization onwards (excluding extension)
main_directory = '/Volumes/macOS Mojave/Users/trevorstirling/Documents/Trevor/Research/Characterization/Data/2024_05_31/QST/Data'     # Data directory
device_name_start = "BRL9_M-AL_A2_5_10C_121mA_unbiased_"                  # Data name up to polarization
device_name_end = "_bin_width=50_num_bins=2000_int_time=10_1"             # Data name from polarization onwards (excluding extension)
peak_width_bins = 2                                                       # Width of coincidence peak [bins]
polarizations = 'HVRD'                                                    # List four polarizations used from H V L R D A
peak_polarization = 'VH'                                                  # Which polarization to use to find the peak
### Options
coincidence_type = 'Raw Coincidences' # Raw Coincidences, Coincidences Less Accidentals
counts_plot = True
show_figs = True
save_figs = False
pulsed = False # Not yet configured for pulsed = True

#Functions
def fidelty(theta, rho):
	# Finds fidelity of density matrix rho
	psi = np.array([0,1,np.cos(theta)-1j*np.sin(theta),0]) # HV + e^(i*phi)VH
	fid = 0.5*np.matmul(np.matmul(psi,rho),psi.conj())
	#For an arbitrary density matrix rho_2:
	# fid = ( np.trace( la.sqrtm( np.matmul( np.matmul(la.sqrtm(rho_2), rho), la.sqrtm(rho_2) ) ) ) )**2
	return fid.real

def max_fidelity(rho):
	theta = np.linspace(-np.pi,np.pi,10000)
	fid = [fidelty(i,rho) for i in theta]
	imax = np.argmax(fid)
	return fid[imax], theta[imax]*180/np.pi #max_fidelity, theta_max_fidelity_degrees

def HV_basis(polarization):
	# Returns comma separated string for polarization in H,V basis
	if polarization == 'H':
		return "1,0"
	elif polarization == 'V':
		return "0,1"
	elif polarization == 'D':
		return "0.7071,0.7071"
	elif polarization == 'A':
		return "0.7071,-0.7071"
	elif polarization == 'R':
		return "0.7071,0.7071j"
	elif polarization == 'L':
		return "0.7071,-0.7071j"
	else:
		raise Exception(polarization+" is not a valid polarization")

def Tomo_Input(polarization_vector, coincidence_vector, intensity_vector):
	#Formats data for tomography file
	intensity = "np.array(["
	tomo_input = "np.array(["
	for i in range(len(polarization_vector)):
		polarization = polarization_vector[i]
		coinc_count = int(coincidence_vector[i])
		intensity += str(intensity_vector[i])+','
		tomo_input += "[1,0,0,"+str(coinc_count)+","+HV_basis(polarization[0])+","+HV_basis(polarization[1])+"],"
	intensity = intensity[:-1]+"])"
	tomo_input = tomo_input[:-1]+"])"
	tomography_file_data = "conf['NQubits'] = 2\nconf['NDetectors'] = 1\nconf['Crosstalk'] = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]\nconf['UseDerivative'] = 0\nconf['Bellstate'] = 0\nconf['DoErrorEstimation'] = 0\nconf['DoDriftCorrection'] = 'no'\nconf['Window'] = 0\nconf['Efficiency'] = [1,1,1,1]\n"
	tomography_file_data += "tomo_input="+str(tomo_input)+"\nintensity="+str(intensity)
	return tomography_file_data

def plot_counts(polarizations, counts, coincidence_type):
	N = len(polarizations)
	z_max = max(counts)
	### Determine tick labels
	xTicks = [x for x in polarizations]
	yTicks = [x for x in polarizations]
	### Set widths of bars
	dx = [0.9 for _ in range(N**2)]
	dy = [0.9 for _ in range(N**2)]
	### Find locations for bar origins
	xpos = [0 for _ in range(N**2)]
	ypos = [0 for _ in range(N**2)]
	zpos = [0 for _ in range(N**2)]
	for i in range(N**2):
		xpos[i] = (i-i%4)/4+0.5
		ypos[i] = i%4+0.5
	### Plot figure
	fig = plt.figure()
	ax1 = fig.add_subplot(projection = '3d')
	colourMap = sns.color_palette("Spectral_r", as_cmap=True)
	ax1.bar3d(xpos, ypos, zpos, dx, dy, counts, color = colourMap(counts/z_max), alpha=0.75, edgecolor=sns.color_palette('pastel',8)[3], shade=False)
	### Format figure
	plt.title(coincidence_type, fontsize=18)
	plt.xlabel("Channel 1")
	plt.ylabel("Channel 2")
	ax1.axes.set_xticks(range(1, N+1), xTicks)
	ax1.axes.set_yticks(range(1, N+1), yTicks)
	sns.set_theme()
	sns.set_style("white")
	### Add Colour Bar
	fig.subplots_adjust(bottom = 0.2)
	colourbar_area = fig.add_axes([0.2, 0.10, 0.7, 0.065])
	norm = mpl.colors.Normalize(vmin = 0, vmax = z_max)
	mpl.colorbar.ColorbarBase(colourbar_area, cmap = colourMap, norm = norm, orientation = 'horizontal')
	return fig

def plot_density_matrix(rho):
	z_max = 0.6
	z_min = -z_max
	N = 2**int(np.log2(rho.shape[0]))
	re_rho = np.real(rho).flatten().astype(float)
	im_rho = np.imag(rho).flatten().astype(float)
	### Determine tick labels
	ticks = []
	tickBase = ["H", "V"]
	for p1 in tickBase:
		for p2 in tickBase:
			ticks.append(p1+p2)
	xTicks = [x for x in ticks]
	yTicks = [x for x in ticks]
	zTicksLoc = np.linspace(-0.5,0.5,5)
	zTicks = [np.round(zTicksLoc[i],2) for i in range(len(zTicksLoc))]
	### Set widths of bars
	dx = [0.9 for _ in range(N**2)]
	dy = [0.9 for _ in range(N**2)]
	### Find locations for bar origins
	xpos = [0 for _ in range(N**2)]
	ypos = [0 for _ in range(N**2)]
	zpos = [0 for _ in range(N**2)]
	for i in range(N**2):
		xpos[i] = (i-i%4)/4+0.5
		ypos[i] = i%4+0.5
	### Plot figure
	fig = plt.figure()
	ax1 = fig.add_subplot(121, projection = '3d')
	ax2 = fig.add_subplot(122, projection = '3d')
	colourMap = sns.color_palette("Spectral_r", as_cmap=True)
	ax1.bar3d(xpos, ypos, zpos, dx, dy, re_rho, color = colourMap((re_rho-z_min)/(z_max-z_min)), alpha=0.75, edgecolor=sns.color_palette('pastel',8)[3], shade=False)
	ax2.bar3d(xpos, ypos, zpos, dx, dy, im_rho, color = colourMap((im_rho-z_min)/(z_max-z_min)), alpha=0.75, edgecolor=sns.color_palette("pastel",8)[3], shade=False)
	### Format figure
	ax1.set_title(r"$Re(\rho)$", fontsize=18)
	ax2.set_title(r"$Im(\rho)$", fontsize=18)
	ax1.axes.set_xticks(range(1, N+1), xTicks)
	ax1.axes.set_yticks(range(1, N+1), yTicks)
	ax1.axes.set_zticks(zTicksLoc, zTicks)
	ax2.axes.set_xticks(range(1, N+1), xTicks)
	ax2.axes.set_yticks(range(1, N+1), yTicks)
	ax2.axes.set_zticks(zTicksLoc, zTicks)
	ax1.axes.set_zlim3d(z_min, z_max)
	ax2.axes.set_zlim3d(z_min, z_max)
	sns.set_theme()
	sns.set_style("white")
	### Add Colour Bar
	fig.subplots_adjust(bottom = 0.1)
	colourbar_area = fig.add_axes([0.2, 0.10, 0.7, 0.065])
	norm = mpl.colors.Normalize(vmin = 0, vmax = z_max)
	mpl.colorbar.ColorbarBase(colourbar_area, cmap = colourMap, norm = norm, orientation = 'horizontal')
	return fig

### Main Code
bin_width = int(device_name_end.split("bin_width=")[1].split("_")[0]) #[ps]
collection_time = int(device_name_end.split("int_time=")[1].split("_")[0]) #[s]
device_name = device_name_start+device_name_end[1:]
#Check all files exist
for p1 in polarizations:
	for p2 in polarizations:
		file_name = device_name_start+p1+p2+device_name_end
		file_path = os.path.join(main_directory,file_name+".csv")
		if not os.path.exists(file_path):
			raise Exception("Required Data does not exist: "+file_path)
#Create results directory
results_dir = os.path.join(os.path.dirname(__file__),'Results')
if not os.path.isdir(results_dir):
	os.makedirs(results_dir)
	print(" Created new directory:", results_dir)
#Find coincidence peak location
file_name = device_name_start+peak_polarization+device_name_end
file_path = os.path.join(main_directory,file_name+".csv")
data = np.loadtxt(file_path,delimiter=",")#,skiprows=1) #currently no header, so no need for this   
coincidences = data[:,1]
i_peak = np.argmax(coincidences)
if peak_width_bins%2 == 0:
	#If asymmetric, use an extra point before the peak
	peak_bin_start = i_peak-int(peak_width_bins/2)
	peak_bin_end = i_peak+int(peak_width_bins/2)-1
else:
	peak_bin_start = i_peak-int((peak_width_bins-1)/2)
	peak_bin_end = i_peak+int((peak_width_bins-1)/2)
peak_width = (peak_bin_end-peak_bin_start+1)*bin_width
#Find accidentals range
accidental_bin_start = i_peak+100
accidental_bin_end = len(coincidences-1)
### Loop through files and collect data
polarization_vector = []
coincidence_vector = []
intensity_vector = []
for p1 in polarizations:
	for p2 in polarizations:
		file_name = device_name_start+p1+p2+device_name_end
		file_path = os.path.join(main_directory,file_name+".csv")
		data = np.loadtxt(file_path,delimiter=",",skiprows=1)        
		delay = data[:,0]
		coincidences = data[:,1]
		accidentals = coincidences[accidental_bin_start:accidental_bin_end+1]
		####################################### Pulsed mode not configured #######################################
		if pulsed:
			peak_bin_starting = 130414#
			peak_bin_ending = 130418#
			bin_start = 0 #bins before (inclusive)
			bin_end = 1  #bins after (exclusive)
			bin_diff = 454.5
			peak_bin_start = peak_bin_starting+np.argmax(coincidences[peak_bin_starting:peak_bin_ending])-bin_start
			peak_bin_end = peak_bin_starting+np.argmax(coincidences[peak_bin_starting:peak_bin_ending])+bin_end
			accidentals = np.concatenate([coincidences[peak_bin_start+int(bin_diff*k):peak_bin_end+int(bin_diff*k)] for k in range(1,50)])
		####################################### Pulsed mode not configured #######################################
		total_coincidences = sum(coincidences[peak_bin_start:peak_bin_end+1])
		avg_accidentals = sum(accidentals)/len(accidentals)*(peak_bin_end-peak_bin_start+1)
		if coincidence_type == 'Raw Coincidences':
			coincidence_metric = total_coincidences
		elif coincidence_type == 'Coincidences Less Accidentals':
			coincidence_metric = total_coincidences-avg_accidentals
		else:
			raise Exception("Invalid coincidence type: "+coincidence_type)
		coincidence_vector.append(coincidence_metric)
		intensity_vector.append(avg_accidentals)
		polarization_vector.append(p1+p2)
		print(file_name+" CAR = {:.3f}".format(total_coincidences/avg_accidentals)+", argmax(coinc) = {:n}".format(np.argmax(coincidences))+", "+coincidence_type+" = {:n}".format(coincidence_metric))
intensity_vector = [1 for _ in intensity_vector] # Can use dichroic mirror to monitor pump power and normalize for that here
### Plot Counts
if counts_plot:
	fig = plot_counts(polarizations, coincidence_vector, coincidence_type)
	if save_figs:
		fig.savefig(os.path.join(results_dir, 'Counts_'+device_name+'.png'))
	if show_figs:
		plt.show()
	else:
		plt.close()
### Generate tomography file
output_file = os.path.join(results_dir,'evalfile_'+coincidence_type+"_peak_width="+str(peak_width)+'ns_'+device_name+".txt")
with open(output_file,"w") as f:
	f.write(Tomo_Input(polarization_vector, coincidence_vector, intensity_vector))
	f.close()
### Perform Tomography
[rho,intensity,fvalp] = qKLib.Tomography().importEval(output_file)
### Plot Density Matrix
fig = plot_density_matrix(rho)
if save_figs:
	fig.savefig(os.path.join(results_dir, 'Density_Matrix_'+device_name+'.png'))
if show_figs:
	plt.show()
else:
	plt.close()
### Print results to console
max_fid, phi = max_fidelity(rho)
print('\npurity = {:.2f}%'.format(qKLib.purity(rho)*100))
print('concurrence = {:.2f}%'.format(qKLib.concurrence(rho)*100))
print('Max fidelity = {:.2f}%'.format(max_fid*100)+' at angle phi = {:.2f}'.format(phi)+' degrees')