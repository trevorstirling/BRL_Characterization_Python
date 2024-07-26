#########################################################################
# Script to run Quantum State Tomography GUI                            #
# QST code from Zach Leger                                              #
#                                                                       #
# Author: Trevor Stirling                                               #
# Date: July 24, 2024                                                   #
#########################################################################

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import sys, os
import time
from GUI_common_functions import BluePSGButton,enforce_number,get_file_locations_GUI
import PySimpleGUI as psg

if sys.platform == "win32":
	import TimeTagger
	import PyQt5
	matplotlib.use('Qt5Agg')
else:
	print('Time Tagger is only configured for Windows.')

font = 'Tahoma'
GUI_defaults_dir = os.path.join(os.path.dirname(__file__),"GUI Defaults")
GUI_file = os.path.basename(__file__).replace(" GUI.py",".txt")
text_width = 8
input_width = 8

def GUI(debug=True):
	polarization_list = ['HH', 'HV', 'HR', 'HD', 'VH', 'VV', 'VR', 'VD', 'RH', 'RV', 'RR', 'RD', 'DH', 'DV', 'DR', 'DD']
	#Options
	psg.set_options(font=(font, 16))
	psg.theme('DarkBlue14')
	#Define layout
	if debug:
		print_window = []
	else:
		print_window = [psg.Output(size=(10,5), expand_x=True, expand_y=True, key='output')]
	layout = [[psg.Text('Your Name:'), psg.InputText('', key='User_name', size=(30,1), expand_x=True), psg.Text('(for data saving)')],
	[psg.Text('Device Name:'), psg.InputText('', key='Device_name', size=(30,1), expand_x=True)],
	[psg.Text('Name Appendix:'), psg.InputText('1', key='appendix', size=(3,1)), psg.Text('Integration Time:'), psg.InputText('5', key='int_time', size=(3,1), enable_events=True), psg.Text('s')],
	[psg.Text('Number of Bins:'), psg.InputText('2000', key='num_bins',  size=(5,1), enable_events=True), psg.Text('Bin Width:'), psg.InputText('50', key='bin_width',  size=(4,1), enable_events=True), psg.Text('ps')],
	[psg.Text('Polarization:'), psg.Combo(polarization_list, default_value='HH', size=(5,1), enable_events=True, readonly=True, key='Polarization'), psg.Text('Signal Channel:'), psg.Combo([1,2,3,4], default_value=1, size=(3,1), readonly=True, key='signal_channel'), psg.Text('Idler Channel:'), psg.Combo([1,2,3,4], default_value=3, size=(3,1), readonly=True, key='idler_channel')],
	[BluePSGButton('Alignment'), psg.Push(), psg.Checkbox('Display', size=(8,1), key='Display_fig', default=True), psg.Checkbox('Save', size=(6,1), key='Save_fig', default=True), BluePSGButton('Collect Counts'), BluePSGButton('Exit')], #push adds flexible whitespace
	[psg.Text('', size=(10,1)), psg.Text('λ/4 #1', size=(text_width,1), justification='center'), psg.Text('λ/2 #1', size=(text_width,1), justification='center'), psg.Text('λ/4 #2', size=(text_width,1), justification='center'), psg.Text('λ/2 #2', size=(text_width,1), justification='center')],
	[psg.Text('H Angles:', size=(10,1)), psg.InputText('0', key='Q1_H', size=(input_width,1), enable_events=True, justification='right'), psg.InputText('0', key='H1_H', size=(input_width,1), enable_events=True, justification='right'), psg.InputText('0', key='Q2_H', size=(input_width,1), enable_events=True, justification='right'), psg.InputText('0', key='H2_H', size=(input_width,1), enable_events=True, justification='right')],
	[psg.Text('V Angles:', size=(10,1)), psg.Text('0', size=(text_width,1), key='Q1_V', justification='right'), psg.Text('0', size=(text_width,1), key='H1_V', justification='right'), psg.Text('0', size=(text_width,1), key='Q2_V', justification='right'), psg.Text('0', size=(text_width,1), key='H2_V', justification='right')],
	[psg.Text('R Angles:', size=(10,1)), psg.Text('0', size=(text_width,1), key='Q1_R', justification='right'), psg.Text('0', size=(text_width,1), key='H1_R', justification='right'), psg.Text('0', size=(text_width,1), key='Q2_R', justification='right'), psg.Text('0', size=(text_width,1), key='H2_R', justification='right')],
	[psg.Text('D Angles:', size=(10,1)), psg.Text('0', size=(text_width,1), key='Q1_D', justification='right'), psg.Text('0', size=(text_width,1), key='H1_D', justification='right'), psg.Text('0', size=(text_width,1), key='Q2_D', justification='right'), psg.Text('0', size=(text_width,1), key='H2_D', justification='right')],
	print_window]
	#Create window
	window = psg.Window('QST',layout, resizable=True)
	window.finalize() #need to finalize window before editing it in any way
	#Set default values
	if os.path.isfile(os.path.join(GUI_defaults_dir,GUI_file)):
		with open(os.path.join(GUI_defaults_dir, GUI_file),"r") as f:
			data = f.read()
			data = data.split("\n")
			for line in data[:-1]:
				key, value = line.split(": ")
				if value == "True":
					value = True
				elif value == "False":
					value = False
				window[key].update(value=value)
				#Update GUI based on selections
				if key == 'Polarization':
					highlight_angles(window,value)
				elif key == 'Q1_H':
					angle_Q1 = value
				elif key == 'H1_H':
					angle_H1 = value
				elif key == 'Q2_H':
					angle_Q2 = value
				elif key == 'H2_H':
					angle_H2 = value
		calculate_angles(window,angle_Q1,angle_H1,angle_Q2,angle_H2)
	else:
		calculate_angles(window,0,0,0,0)
		highlight_angles(window,'HH')
	#Poll for events
	while True: 
		event, values = window.read()
		if event == psg.WIN_CLOSED or event == 'Exit':
			break
		elif event == 'Polarization':
			highlight_angles(window,values[event])
		elif event == 'Alignment':
			Alignment(window,values)
		elif event == 'Collect Counts':
			QST_Scan(window,values)
		#data validation
		elif event in ['bin_width', 'num_bins', 'int_time']:
			enforce_number(window,values,event, decimal_allowed=False)
		elif event in ['Q1_H', 'H1_H', 'Q2_H', 'H2_H']:
			enforce_number(window,values,event,negative_allowed=True)
			calculate_angles(window,values['Q1_H'],values['H1_H'],values['Q2_H'],values['H2_H'])
	window.close()

def calculate_angles(window,q1,h1,q2,h2):
	if q1 == '' or q1 == '-':
		q1 = 0
	else:
		q1 = float(q1)
	angle_format(window,'Q1_V',q1)
	angle_format(window,'Q1_D',q1+45)
	angle_format(window,'Q1_R',q1)
	if h1 == '' or h1 == '-':
		h1 = 0
	else:
		h1 = float(h1)
	angle_format(window,'H1_V',h1+45)
	angle_format(window,'H1_D',h1+22.5)
	angle_format(window,'H1_R',h1+22.5)
	if q2 == '' or q2 == '-':
		q2 = 0
	else:
		q2 = float(q2)
	angle_format(window,'Q2_V',q2)
	angle_format(window,'Q2_D',q2+45)
	angle_format(window,'Q2_R',q2)
	if h2 == '' or h2 == '-':
		h2 = 0
	else:
		h2 = float(h2)
	angle_format(window,'H2_V',h2+45)
	angle_format(window,'H2_D',h2+45+22.5)
	angle_format(window,'H2_R',h2+45+22.5)

def highlight_angles(window,polarization):
	for wp in ['Q','H']:
		for i in range(2):
			window[wp+str(i+1)+'_'+polarization[i]].update(background_color='White', text_color='Black')
			for p in ['H','V','D','R']:
				if p != polarization[i]:
					window[wp+str(i+1)+'_'+p].update(background_color='Black', text_color='White')

def angle_format(window,key,num):
	string = "{:.1f}".format(num%360)
	window[key].update(string)

def CAR(hist_data,peak_width):
	if max(hist_data) == 0 or peak_width == 0:
		return 0
	else:
		i = np.argmax(hist_data)
	if peak_width%2 == 0:
		#asymmetric about peak, use one extra point before the peak
		counts = sum(hist_data[i-int(peak_width/2):i+int(peak_width/2)])
	else:
		counts = sum(hist_data[i-int(peak_width/2):i+int(peak_width/2)+1])
	if i+100 < len(hist_data):
		accidental_average = np.average(hist_data[i+100:-1])
	else:
		accidental_average = np.average(hist_data[i+1:-1])
	return counts/peak_width/accidental_average

def initialize_TT(signal_channel, idler_channel, bin_width, num_bins):
	if not 'tagger' in globals():
		print("Creating TimeTagger")
		tagger = TimeTagger.createTimeTagger()
		print("TimeTagger Created")
	if not 'histogram' in globals():
		histogram = TimeTagger.Correlation(tagger, signal_channel, idler_channel, bin_width, num_bins)
		print("Histogram Measurement Created")
	if not 'countrate' in globals():
		countrate= TimeTagger.Countrate(tagger,[signal_channel,idler_channel])
		print("Countrate Measurement Created")
	return tagger, histogram, countrate

def Alignment(window,values):
	run_time = 2 #time [s]
	# Pull parameters from GUI
	signal_channel = int(values['signal_channel'])
	idler_channel = int(values['idler_channel'])
	num_bins = int(values['num_bins'])
	bin_width = int(values['bin_width']) # [ps]
	if sys.platform == "win32":
		### Initialize Figure
		tagger, histogram, _ = initialize_TT(signal_channel, idler_channel, bin_width, num_bins)
		# hist_data=np.array([1,1,1,1,1,1])
		time_arr=(np.arange(0,num_bins) - int(num_bins/2) )*bin_width/1000
		#Prepare figure
		fig, ax = plt.subplots()
		plt.xlabel("Time (ns)")
		plt.ylabel("Number of Counts")
		ax.set_ylim(0,1000)
		plotted_previous, = plt.plot(time_arr,np.zeros(num_bins))
		plotted_data, = plt.plot(time_arr,np.zeros(num_bins))
		plot_text_1=plt.text(0.01,0.78,"Idler Channel: "+str(idler_channel) +"\nSignal Channel: "+str(signal_channel)+"\nBin Width (ps): "+str(bin_width)+"\nNumber of Bins: "+str(num_bins)+"\nIntegration Time (s): "+str(run_time),transform = ax.transAxes)
		plot_text_2=plt.text(0.6,0.1,"CAR: {:.2f}".format(0)+"\nMAX: {:n}".format(0), transform = ax.transAxes, fontsize=20)
		plot_text_3=plt.text(0.6,0.75,"Previous\nCAR: {:.2f}".format(0)+"\nMAX: {:n}".format(0), transform = ax.transAxes, fontsize=20)
		plt.ion()
		while True:
        	### Collect new data
			histogram.startFor(int(run_time*1E12))
			time.sleep(0.2)
			hist_data=histogram.getData()
			while histogram.isRunning():
				hist_data=histogram.getData()
				plt.figure(1)
				plt.pause(0.2)
				plotted_data.set_ydata(hist_data)
				plot_text_2.set_text("CAR: {:.2f}".format(CAR(hist_data,1))+"\nMAX: {:n}".format(max(hist_data)))
				if not plt.fignum_exists(fig.number):
					return
				fig.canvas.draw()
				time.sleep(0.0001)
			### Update Figure
			plotted_previous.set_ydata(histogram.getData())
			plot_text_3.set_text("Previous\nCAR: {:.2f}".format(CAR(hist_data,1))+"\nMAX: {:n}".format(max(hist_data)))
			ax.set_ylim(0,max(hist_data)*1.2)
			fig.canvas.draw()

def QST_Scan(window, values):
	#Save current settings to default file
	if not os.path.isdir(GUI_defaults_dir):
		os.makedirs(GUI_defaults_dir)
		print(" Created new directory:", GUI_defaults_dir)
		window.Refresh()
	with open(os.path.join(GUI_defaults_dir, GUI_file),"w") as f:
		for field, value in values.items():
			f.write(field+": "+str(value)+"\n")
	# Pull parameters from GUI
	user_name = values['User_name']
	signal_channel = int(values['signal_channel'])
	idler_channel = int(values['idler_channel'])
	num_bins = int(values['num_bins'])
	bin_width = int(values['bin_width']) # [ps]
	run_time = int(values['int_time']) #integration time [s]
	polarization = values['Polarization']
	scan_name = values['Device_name']+'_'+polarization+'_bin_width='+str(bin_width)+'_num_bins='+str(num_bins)+'_int_time='+str(run_time)+'_'+values['appendix']
	save_fig = values['Save_fig']
	display_fig = values['Display_fig']
	save_data = save_fig
	characterization_directory = os.path.join(__file__,'..','..','Data',user_name)
	print(scan_name)
	if sys.platform == "win32":
		### Collect Data
		tagger, histogram, countrate = initialize_TT(signal_channel, idler_channel, bin_width, num_bins)		
		time_arr=(np.arange(0,num_bins) - int(num_bins/2) )*bin_width/1000
		histogram.startFor(int(run_time*1E12))
		countrate.startFor(int(run_time*1E12))
		while histogram.isRunning():
			hist_data=histogram.getData()
			count_1,count_2=countrate.getData()
		peak_width = 1 #number of bins
		car = CAR(hist_data,peak_width)
		print("CAR "+str(car))
		### Plot
		fig, ax = plt.subplots()
		plot_text_1=plt.text(0.01,0.78,"Idler Channel: "+str(idler_channel) +"\nSignal Channel: "+str(signal_channel)+"\nBin Width (ps): "+str(bin_width)+"\nNumber of Bins: "+str(num_bins)+"\nIntegration Time (s): "+str(run_time),transform = ax.transAxes)
		plot_text_2=plt.text(0.60,0.86,"Signal Count: "+str(int(count_1))+ "\nIdler Count: "+str(int(count_2))+ "\nCAR: {:.2f}".format(car),transform = ax.transAxes)
		plt.title(scan_name)
		plt.xlabel("Time (ns)")
		plt.ylabel("Number of Counts")
		plt.plot(time_arr,hist_data)
		### Name Output Files
		[csv_location, png_location, scan_name] = get_file_locations_GUI(save_data, save_fig, characterization_directory, 'QST', scan_name)
		if scan_name == '-NULL-':
			return
		### Save data to file
		if save_data:
			np.savetxt(csv_location, [p for p in zip(time_arr,hist_data)], delimiter=",")
			print(" Data saved to",csv_location)
			window.Refresh()
		### Plot data
		if display_fig or save_fig:
			if save_fig:
				fig.savefig(png_location,bbox_inches='tight')
				# fig.savefig(png_location,dpi='figure')
				print(" Figure saved to",png_location)
				window.Refresh()
			if display_fig:
				print(" Displaying figure. Close figure to resume.")
				window.Refresh()
				plt.show()
			else:
				plt.close()
	polarization_list_optimal_order = ['HH', 'HV', 'HR', 'HD', 'VD', 'VR', 'RR', 'RD', 'DD', 'DR', 'DV', 'DH', 'RH', 'RV', 'VV', 'VH']
	next_pol = polarization_list_optimal_order[(polarization_list_optimal_order.index(polarization)+1)%len(polarization_list_optimal_order)]
	window['Polarization'].update(next_pol)
	highlight_angles(window,next_pol)

if __name__ == "__main__":
	if len(sys.argv)-1 == 1 and (sys.argv[1].lower() == 'debug' or sys.argv[1] == '1'):
		GUI(1)
	else:
		GUI()
