#########################################################################
# Script to take spectrum at different current values using	various lab #
# equipment                                                             #
#                                                                       #
# Author: Trevor Stirling                                               #
# Date: Aug 23, 2024                                                    #
#########################################################################

import numpy as np
import matplotlib.pyplot as plt
import sys, os
import time
from GUI_common_functions import BluePSGButton,enforce_number,plus_button,minus_button,get_file_locations_GUI,connect_to_GPIB,plot_spectrum
import PySimpleGUI as psg

font = 'Tahoma'
GUI_defaults_dir = os.path.join(os.path.dirname(__file__),"GUI Defaults")
GUI_file = os.path.basename(__file__).replace(" GUI.py",".txt")

def GUI(debug=False):
	#Options
	psg.set_options(font=(font, 16))
	psg.theme('DarkBlue14')
	num_sources = 1
	#Define layout
	if debug:
		print_window = []
	else:
		print_window = [psg.Multiline(size=(10,5), expand_x=True, expand_y=True, key='output', reroute_stdout=True)]
	layout = [[psg.Text('Your Name:'), psg.InputText('', key='User_name', size=(30,1), expand_x=True), psg.Text('(for data saving)')],
	[psg.Text('Device Name:'), psg.InputText('', key='Device_name', size=(30,1), expand_x=True)],
	[psg.Button('', image_data=minus_button, image_subsample=12, button_color=('black', psg.theme_background_color()), border_width=0, enable_events=True, key='remove_source'), psg.Text('Add or Remove Sources'), psg.Button('', image_data=plus_button, image_subsample=12, button_color=('black', psg.theme_background_color()), border_width=0, enable_events=True, key='add_source')],
	[psg.Push(),psg.Text('--------------- Spectrum Analyzer Options ---------------',font=(font, 20)),psg.Push()],
	[psg.Text('Spectrum Analyzer:'), psg.Combo(['A86146B', 'A86142A', 'AQ6317B', 'AQ6374', 'E4407B'], default_value='AQ6374', size=(8,1), enable_events=True, readonly=True, key='Spectrum_analyzer'), psg.Text('Channel:'), psg.Combo(['A', 'B', 'C', 'D', 'E', 'F', 'G'], default_value='A', size=(2,1), readonly=True, key='Channel')],
	[psg.Checkbox('Show FWHM', size=(12,1), key='FWHM', default=False),psg.Checkbox('Show SMSR', size=(12,1), key='SMSR', default=False),psg.Checkbox('Track Peak', size=(11,1), key='adjust_center', default=False)],
	[psg.Push(),psg.pin(psg.Column(current_source_title(1),key='source_1_title',visible=True)),psg.Push()],
	[psg.pin(psg.Column(current_source_layout(1),key='source_1_options',visible=True))],
	[psg.Push(),psg.pin(psg.Column(current_source_title(2),key='source_2_title',visible=False)),psg.Push()],
	[psg.pin(psg.Column(current_source_layout(2),key='source_2_options',visible=False))],
	[psg.Push(),psg.pin(psg.Column(current_source_title(3),key='source_3_title',visible=False)),psg.Push()],
	[psg.pin(psg.Column(current_source_layout(3),key='source_3_options',visible=False))],
	[psg.Push(),psg.pin(psg.Column(current_source_title(4),key='source_4_title',visible=False)),psg.Push()],
	[psg.pin(psg.Column(current_source_layout(4),key='source_4_options',visible=False))],
	[psg.Push(),psg.pin(psg.Column(current_source_title(5),key='source_5_title',visible=False)),psg.Push()],
	[psg.pin(psg.Column(current_source_layout(5),key='source_5_options',visible=False))],
	[BluePSGButton('Ω Check'), psg.Push(), psg.Checkbox('Display', size=(8,1), key='Display_fig', default=False), psg.Checkbox('Save', size=(6,1), key='Save_fig', default=True), BluePSGButton('Capture Sweep'), BluePSGButton('Exit')], #push adds flexible whitespace
	print_window]
	#Create window
	window = psg.Window('Spectrum Current Sweep',layout, resizable=True)
	window.finalize() #need to finalize window before editing it in any way
	#Set default values
	num_sources = 0
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
				if key == 'Spectrum_analyzer':
					update_SA_channel(window, value)
				elif key in ['source_'+str(i+1) for i in range(5)] and value != 'OFF':
					num_sources += 1
					update_channel(window,value,key.split("_")[1])
				elif key in ['source_'+str(i+1)+'_mode' for i in range(5)]:
					switch_v_i_text(window,key.split("_")[1],value)
				elif key in ['pulsed_'+str(i+1) for i in range(5)]:
					update_is_pulsed(window,key.split("_")[1],value)
	num_sources = max(num_sources,1)
	update_source_visibility(window,num_sources)
	#Poll for events
	while True: 
		event, values = window.read()
		if event == psg.WIN_CLOSED or event == 'Exit':
			break
		elif event in ['pulsed_'+str(i+1) for i in range(5)]:
			num = event.split('_')[1]
			update_is_pulsed(window,num,values[event])
		elif event == 'add_source':
			num_sources = min(num_sources+1,5)
			update_source_visibility(window,num_sources)
		elif event == 'remove_source':
			num_sources = max(num_sources-1,1)
			update_source_visibility(window,num_sources)
		elif event in ['source_'+str(i+1) for i in range(5)]:
			update_channel(window,values[event],event[-1])
		elif event in ['source_'+str(i+1)+'_mode' for i in range(5)]:
			num = event.split('_')[1]
			switch_v_i_text(window,num,values[event])
		#data validation
		elif event == 'Capture Sweep':
			Spectrum_Analyzer_Capture_Source_Sweep(window,values)
		elif event == 'Ω Check':
			resistance_check(window, values)
		elif event == 'Spectrum_analyzer':
			update_SA_channel(window, values[event])
		#data validation
		elif event == 'device_length':
			enforce_number(window,values,event)
		elif event == 'device_width':
			enforce_number(window,values,event)
		elif event == 'pause_interval':
			enforce_number(window,values,event)
		elif event in ['protection_'+str(i+1) for i in range(5)]:
			enforce_number(window,values,event,negative_allowed=True)
		elif event in ['start_'+str(i+1) for i in range(5)]:
			enforce_number(window,values,event,negative_allowed=True)
		elif event in ['step_'+str(i+1) for i in range(5)]:
			enforce_number(window,values,event,negative_allowed=True)
		elif event in ['stop_'+str(i+1) for i in range(5)]:
			enforce_number(window,values,event,negative_allowed=True)
		elif event in ['pulse_width_'+str(i+1) for i in range(5)]:
			enforce_number(window,values,event,decimal_allowed=False)
		elif event in ['pulse_delay_'+str(i+1) for i in range(5)]:
			enforce_number(window,values,event,decimal_allowed=False)
	window.close()

def switch_v_i_text(window,num,mode):
	if mode == 'Current':
		window['protection_'+num+'_text'].update(value='Protection Voltage [V]:')
		window['protection_'+num].update(value='4')
		window['units_'+num].update(value='[mA]')
	elif mode == 'Voltage':
		window['protection_'+num+'_text'].update(value='Protection Current [mA]:')
		window['protection_'+num].update(value='100')
		window['units_'+num].update(value='[V]')

def update_is_pulsed(window,num,is_pulsed):
	if is_pulsed:
		window['pulse_width_'+num+'_text'].update(visible=True)
		window['pulse_width_'+num].update(visible=True)
		window['pulse_delay_'+num+'_text'].update(visible=True)
		window['pulse_delay_'+num].update(visible=True)
	else:
		window['pulse_delay_'+num].update(visible=False)
		window['pulse_delay_'+num+'_text'].update(visible=False)
		window['pulse_width_'+num].update(visible=False)
		window['pulse_width_'+num+'_text'].update(visible=False)

def current_source_title(num):
	return [[psg.Text('--------------- Source '+str(num)+' Options ---------------',font=(font, 20))]]

def current_source_layout(num):
	layout = [[psg.Text('Source:'), psg.Combo(['K2520', 'K2604B', 'B2902A', 'LDC3908', 'LDC3916', 'OFF'], default_value='OFF', size=(8,1), enable_events=True, readonly=True, key='source_'+str(num)), psg.Text('Channel:'), psg.Combo([''], size=(3,1), readonly=True, key='source_'+str(num)+'_channel'),psg.Text('Mode:'), psg.Combo(['Current', 'Voltage'], default_value='Current', size=(8,1), enable_events=True, readonly=True, key='source_'+str(num)+'_mode'), psg.Text('Protection Voltage [V]:',key='protection_'+str(num)+'_text'), psg.InputText('4', key='protection_'+str(num), size=(4,1), enable_events=True)],
	[psg.Text('Start:'),psg.InputText('1', key='start_'+str(num), size=(4,1), enable_events=True),psg.Text('Step:'),psg.InputText('1', key='step_'+str(num), size=(4,1), enable_events=True),psg.Text('Stop:'),psg.InputText('100', key='stop_'+str(num), size=(4,1), enable_events=True),psg.Text('[mA]',key='units_'+str(num)),psg.Checkbox('Pulsed', size=(8,1), key='pulsed_'+str(num), default=False, enable_events=True),psg.Text('Pulse Width [μs]:', key='pulse_width_'+str(num)+'_text', visible=False),psg.InputText('8', key='pulse_width_'+str(num), size=(2,1), enable_events=True, visible=False),psg.Text('Pulse Delay [μs]:', key='pulse_delay_'+str(num)+'_text', visible=False),psg.InputText('160', key='pulse_delay_'+str(num), size=(4,1), enable_events=True, visible=False)]]
	return layout

def update_source_visibility(window,num_sources):
	for i in range(5):
		if i<num_sources:
			window['source_'+str(i+1)+'_title'].update(visible=True)
			window['source_'+str(i+1)+'_options'].update(visible=True)
		else:
			window['source_'+str(i+1)+'_options'].update(visible=False)
			window['source_'+str(i+1)+'_title'].update(visible=False)
			window['source_'+str(i+1)].update(value='OFF')

def update_SA_channel(window, spectrum_analyzer):
	if spectrum_analyzer == 'AQ6317B': 
		window['Channel'].update(values = ['A', 'B', 'C'], value = 'A')
	if spectrum_analyzer == 'A86142A' or spectrum_analyzer == 'A86146B': 
		window['Channel'].update(values = ['A', 'B', 'C', 'D', 'E', 'F'], value = 'A')
	if spectrum_analyzer == 'AQ6374': 
		window['Channel'].update(values = ['A', 'B', 'C', 'D', 'E', 'F', 'G'], value = 'A')
	if spectrum_analyzer == 'E4407B': 
		window['Channel'].update(values = ['1', '2', '3'], value = '1')

def update_channel(window,source,num):
	if source == 'K2520':
		window['source_'+str(num)+'_channel'].update(values = ['A'], value = 'A')
	elif source == 'K2604B':
		window['source_'+str(num)+'_channel'].update(values = ['A','B'], value = 'A')
	elif source == 'B2902A':
		window['source_'+str(num)+'_channel'].update(values = ['1','2'], value = '1')
	elif source == 'LDC3908':
		window['source_'+str(num)+'_channel'].update(values = ['1','2','3','4','5','6','7','8'], value = '1')
	elif source == 'LDC3916':
		window['source_'+str(num)+'_channel'].update(values = ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16'], value = '1')

def resistance_check(window,values):
	# Source
	Source_inst = connect_to_GPIB(values['source_1'],['Current',values['source_1_channel'],4,0.1,'DC',8e-6,160e-6])
	if not Source_inst:
		return
	window.Refresh()
	### Turn on current and measure resistance
	Source_inst.set_value(1e-3)
	Source_inst.set_output('ON')
	time.sleep(0.2)
	resistance = Source_inst.read_value('Resistance')
	window.Refresh()
	Source_inst.set_output('OFF')
	print(" {:.1f} Ohms at 1 mA".format(resistance))
	window.Refresh()
	print(" Disconnected from",values['source_1'])
	window.Refresh()
	Source_inst.GPIB.control_ren(0)

def Spectrum_Analyzer_Capture_Source_Sweep(window, values):
	#Save current settings to default file
	if not os.path.isdir(GUI_defaults_dir):
		os.makedirs(GUI_defaults_dir)
		print(" Created new directory:", GUI_defaults_dir)
		window.Refresh()
	with open(os.path.join(GUI_defaults_dir, GUI_file),"w") as f:
		for field, value in values.items():
			if field != "output":
				f.write(field+": "+str(value)+"\n")
	### Get parameters from GUI
	user_name = values['User_name']
	device_name = values['Device_name']
	show_SMSR = values['SMSR']
	show_FWHM = values['FWHM']
	adjust_center = values['adjust_center']
	display_fig = values['Display_fig']
	save_fig = values['Save_fig']
	save_data = save_fig
	#Spectrum Analyzer
	spectrum_analyzer = values['Spectrum_analyzer']
	spectrum_analyzer_channel = values['Channel']
	#Source 1
	Source_1 = values['source_1']
	Source_1_channel = values['source_1_channel']
	Source_1_mode = values['source_1_mode']
	if Source_1_mode == 'Current':
		protection_voltage_1 = float(values['protection_1'])
		protection_current_1 = 0.1
	else:
		protection_voltage_1 = 4
		protection_current_1 = float(values['protection_1'])*1e-3
	Source_start_1 = float(values['start_1'])
	Source_step_1 = float(values['step_1'])
	Source_stop_1 = float(values['stop_1'])
	pulsed_1 = values['pulsed_1']
	if pulsed_1:
		waveform_1 = 'pulsed'
	else:
		waveform_1 = 'DC'
	pulse_width_1 = int(values['pulse_width_1'])*1e-6
	pulse_delay_1 = int(values['pulse_delay_1'])*1e-6
	#Source 2
	Source_2 = values['source_2']
	Source_2_channel = values['source_2_channel']
	Source_2_mode = values['source_2_mode']
	if Source_2_mode == 'Current':
		protection_voltage_2 = float(values['protection_2'])
		protection_current_2 = 0.1
	else:
		protection_voltage_2 = 4
		protection_current_2 = float(values['protection_2'])*1e-3
	Source_start_2 = float(values['start_2'])
	Source_step_2 = float(values['step_2'])
	Source_stop_2 = float(values['stop_2'])
	pulsed_2 = values['pulsed_2']
	if pulsed_2:
		waveform_2 = 'pulsed'
	else:
		waveform_2 = 'DC'
	pulse_width_2 = int(values['pulse_width_2'])*1e-6
	pulse_delay_2 = int(values['pulse_delay_2'])*1e-6
	#Source 3
	Source_3 = values['source_3']
	Source_3_channel = values['source_3_channel']
	Source_3_mode = values['source_3_mode']
	if Source_3_mode == 'Current':
		protection_voltage_3 = float(values['protection_3'])
		protection_current_3 = 0.1
	else:
		protection_voltage_3 = 4
		protection_current_3 = float(values['protection_3'])*1e-3
	Source_start_3 = float(values['start_3'])
	Source_step_3 = float(values['step_3'])
	Source_stop_3 = float(values['stop_3'])
	pulsed_3 = values['pulsed_3']
	if pulsed_3:
		waveform_3 = 'pulsed'
	else:
		waveform_3 = 'DC'
	pulse_width_3 = int(values['pulse_width_3'])*1e-6
	pulse_delay_3 = int(values['pulse_delay_3'])*1e-6
	#Source 4
	Source_4 = values['source_4']
	Source_4_channel = values['source_4_channel']
	Source_4_mode = values['source_4_mode']
	if Source_4_mode == 'Current':
		protection_voltage_4 = float(values['protection_4'])
		protection_current_4 = 0.1
	else:
		protection_voltage_4 = 4
		protection_current_4 = float(values['protection_4'])*1e-3
	Source_start_4 = float(values['start_4'])
	Source_step_4 = float(values['step_4'])
	Source_stop_4 = float(values['stop_4'])
	pulsed_4 = values['pulsed_4']
	if pulsed_4:
		waveform_4 = 'pulsed'
	else:
		waveform_4 = 'DC'
	pulse_width_4 = int(values['pulse_width_4'])*1e-6
	pulse_delay_4 = int(values['pulse_delay_4'])*1e-6
	#Source 5
	Source_5 = values['source_5']
	Source_5_channel = values['source_5_channel']
	Source_5_mode = values['source_5_mode']
	if Source_5_mode == 'Current':
		protection_voltage_5 = float(values['protection_5'])
		protection_current_5 = 0.1
	else:
		protection_voltage_5 = 4
		protection_current_5 = float(values['protection_5'])*1e-3
	Source_start_5 = float(values['start_5'])
	Source_step_5 = float(values['step_5'])
	Source_stop_5 = float(values['stop_5'])
	pulsed_5 = values['pulsed_5']
	if pulsed_5:
		waveform_5 = 'pulsed'
	else:
		waveform_5 = 'DC'
	pulse_width_5 = int(values['pulse_width_5'])*1e-6
	pulse_delay_5 = int(values['pulse_delay_5'])*1e-6
	### Initialize other parameters
	characterization_directory = os.path.join('..','Data',user_name)
	### Connect to Lab Equipment
	Source_1_mode = Source_1_mode.capitalize()
	Source_2_mode = Source_2_mode.capitalize()
	Source_3_mode = Source_3_mode.capitalize()
	Source_4_mode = Source_4_mode.capitalize()
	Source_5_mode = Source_5_mode.capitalize()
	# Sources
	Source_inst_1 = connect_to_GPIB(Source_1,[Source_1_mode,Source_1_channel,protection_voltage_1,protection_current_1,waveform_1,pulse_delay_1,pulse_width_1])
	window.Refresh()
	Source_inst_2 = connect_to_GPIB(Source_2,[Source_2_mode,Source_2_channel,protection_voltage_2,protection_current_1,waveform_2,pulse_delay_2,pulse_width_2])
	window.Refresh()
	Source_inst_3 = connect_to_GPIB(Source_3,[Source_3_mode,Source_3_channel,protection_voltage_3,protection_current_1,waveform_3,pulse_delay_3,pulse_width_3])
	window.Refresh()
	Source_inst_4 = connect_to_GPIB(Source_4,[Source_4_mode,Source_4_channel,protection_voltage_4,protection_current_1,waveform_4,pulse_delay_4,pulse_width_4])
	window.Refresh()
	Source_inst_5 = connect_to_GPIB(Source_5,[Source_5_mode,Source_5_channel,protection_voltage_5,protection_current_1,waveform_5,pulse_delay_5,pulse_width_5])
	window.Refresh()
	if not Source_inst_1 or not Source_inst_2 or not Source_inst_3 or not Source_inst_4 or not Source_inst_5:
		return
	# Spectrum Analyzer
	spectrum_analyzer_inst = connect_to_GPIB(spectrum_analyzer)
	if not spectrum_analyzer_inst:
		return
	x_is_freq = spectrum_analyzer_inst.isESA
	### Convert from mA to A
	if Source_1_mode == 'Current':
		Source_step_1 = Source_step_1*1e-3
		Source_start_1 = Source_start_1*1e-3
		Source_stop_1 = Source_stop_1*1e-3
	if Source_2_mode == 'Current':
		Source_step_2 = Source_step_2*1e-3
		Source_start_2 = Source_start_2*1e-3
		Source_stop_2 = Source_stop_2*1e-3
	if Source_3_mode == 'Current':
		Source_step_3 = Source_step_3*1e-3
		Source_start_3 = Source_start_3*1e-3
		Source_stop_3 = Source_stop_3*1e-3
	if Source_4_mode == 'Current':
		Source_step_4 = Source_step_4*1e-3
		Source_start_4 = Source_start_4*1e-3
		Source_stop_4 = Source_stop_4*1e-3
	if Source_5_mode == 'Current':
		Source_step_5 = Source_step_5*1e-3
		Source_start_5 = Source_start_5*1e-3
		Source_stop_5 = Source_stop_5*1e-3
	### Sweep current and collect data
	sweep_num = 0
	if Source_1.lower() == 'off':
		psg.popup("Source #1 must be enabled.")
		return
	Source_input_list_1 = [x for x in np.arange(Source_start_1,Source_stop_1+Source_step_1/2,Source_step_1)]
	if Source_2.lower() == 'off':
		Source_input_list_2 = [0]
	else:
		Source_input_list_2 = [x for x in np.arange(Source_start_2,Source_stop_2+Source_step_2/2,Source_step_2)]
	if Source_3.lower() == 'off':
		Source_input_list_3 = [0]
	else:
		Source_input_list_3 = [x for x in np.arange(Source_start_3,Source_stop_3+Source_step_3/2,Source_step_3)]
	if Source_4.lower() == 'off':
		Source_input_list_4 = [0]
	else:
		Source_input_list_4 = [x for x in np.arange(Source_start_4,Source_stop_4+Source_step_4/2,Source_step_4)]
	if Source_5.lower() == 'off':
		Source_input_list_5 = [0]
	else:
		Source_input_list_5 = [x for x in np.arange(Source_start_5,Source_stop_5+Source_step_5/2,Source_step_5)]
	num_sweeps = len(Source_input_list_1)*len(Source_input_list_2)*len(Source_input_list_3)*len(Source_input_list_4)*len(Source_input_list_5)
	for i5 in range(len(Source_input_list_5)):
		if Source_5.lower() != 'off':
			if i5 > 0:
				Source_inst_5.set_value(Source_input_list_5[i5])
			else:
				Source_inst_5.safe_turn_on(Source_input_list_5[i5])
			if Source_5_mode == 'Current':
				print(" Source #5 = "+str(round(Source_input_list_5[i5]*1e3))+" mA")
			else:
				print(" Source #5 = "+str(round(Source_input_list_5[i5]*10)/10)+" V")
			window.refresh()
		for i4 in range(len(Source_input_list_4)):
			if Source_4.lower() != 'off':
				if i4 > 0:
					Source_inst_4.set_value(Source_input_list_4[i4])
				else:
					Source_inst_4.safe_turn_on(Source_input_list_4[i4])
				if Source_4_mode == 'Current':
					print(" Source #4 = "+str(round(Source_input_list_4[i4]*1e3))+" mA")
				else:
					print(" Source #4 = "+str(round(Source_input_list_4[i4]*10)/10)+" V")
				window.refresh()
			for i3 in range(len(Source_input_list_3)):
				if Source_3.lower() != 'off':
					if i3 > 0:
						Source_inst_3.set_value(Source_input_list_3[i3])
					else:
						Source_inst_3.safe_turn_on(Source_input_list_3[i3])
					if Source_3_mode == 'Current':
						print(" Source #3 = "+str(round(Source_input_list_3[i3]*1e3))+" mA")
					else:
						print(" Source #3 = "+str(round(Source_input_list_3[i3]*10)/10)+" V")
					window.refresh()
				for i2 in range(len(Source_input_list_2)):
					if Source_2.lower() != 'off':
						if i2 > 0:
							Source_inst_2.set_value(Source_input_list_2[i2])
						else:
							Source_inst_2.safe_turn_on(Source_input_list_2[i2])
						if Source_2_mode == 'Current':
							print(" Source #2 = "+str(round(Source_input_list_2[i2]*1e3))+" mA")
						else:
							print(" Source #2 = "+str(round(Source_input_list_2[i2]*10)/10)+" V")
						window.refresh()
					for i1 in range(len(Source_input_list_1)):
						if Source_1_mode == 'Current':
							print(" Source #1 = "+str(round(Source_input_list_1[i1]*1e3))+" mA")
						else:
							print(" Source #1 = "+str(round(Source_input_list_1[i1]*10)/10)+" V")
						window.refresh()
						if i1 > 0:
							Source_inst_1.set_value(Source_input_list_1[i1])
						else:
							Source_inst_1.safe_turn_on(Source_input_list_1[i1])
						# Delay to let sources stabilize
						time.sleep(0.1)
						### Collect Spectrum
						sweep_num += 1
						print(" Spectrum Analyzer sweeping "+str(sweep_num)+"/"+str(num_sweeps)+"...")
						print(" Sweeping...")
						window.refresh()
						spectrum_analyzer_inst.sweep(spectrum_analyzer_channel, print_status=False)
						print(" Sweep complete")
						print(" Capturing...")
						window.refresh()
						x_data, power = spectrum_analyzer_inst.capture(spectrum_analyzer_channel, print_status=False)
						print(" Capture complete")
						window.refresh()
						if adjust_center and max(power)>-50:
							spectrum_analyzer_inst.peak_to_center()
						if num_sweeps == 1:
							Source_inst_1.GPIB.control_ren(0)
							print(" Disconnected from instruments")
						### Name Output Files
						scan_name = device_name
						if Source_5.lower() != 'off':
							if Source_5_mode == 'Current':
								scan_name += '_'+str(round(Source_input_list_5[i5]*1e3))+'mA'
							elif Source_5_mode == 'Voltage':
								scan_name += '_'+str(round(Source_input_list_5[i5]*10)/10)+'V'
						if Source_4.lower() != 'off':
							if Source_4_mode == 'Current':
								scan_name += '_'+str(round(Source_input_list_4[i4]*1e3))+'mA'
							elif Source_4_mode == 'Voltage':
								scan_name += '_'+str(round(Source_input_list_4[i4]*10)/10)+'V'
						if Source_3.lower() != 'off':
							if Source_3_mode == 'Current':
								scan_name += '_'+str(round(Source_input_list_3[i3]*1e3))+'mA'
							elif Source_3_mode == 'Voltage':
								scan_name += '_'+str(round(Source_input_list_3[i3]*10)/10)+'V'
						if Source_2.lower() != 'off':
							if Source_2_mode == 'Current':
								scan_name += '_'+str(round(Source_input_list_2[i2]*1e3))+'mA'
							elif Source_2_mode == 'Voltage':
								scan_name += '_'+str(round(Source_input_list_2[i2]*10)/10)+'V'
						if Source_1.lower() != 'off':
							if Source_1_mode == 'Current':
								scan_name += '_'+str(round(Source_input_list_1[i1]*1e3))+'mA'
							elif Source_1_mode == 'Voltage':
								scan_name += '_'+str(round(Source_input_list_1[i1]*10)/10)+'V'
						[csv_location, png_location, scan_name] = get_file_locations_GUI(save_data, save_fig, characterization_directory, 'Spectrum', scan_name)
						if scan_name == '-NULL-':
							return
						#Save data
						if save_data:
							full_data = np.zeros((len(power), 2))
							full_data[:,0] = x_data
							full_data[:,1] = power
							if x_is_freq:
								np.savetxt(csv_location, full_data , delimiter=',', header='Frequency [GHz], Power [dBm]', comments='')
							else:
								np.savetxt(csv_location, full_data , delimiter=',', header='Wavelength [nm], Power [dBm]', comments='')
							print(" Data saved to",csv_location)
							window.refresh()
						#Plot data
						if display_fig or save_fig:
							fig = plot_spectrum(scan_name, x_data, power, x_is_freq=x_is_freq, show_SMSR=show_SMSR, show_FWHM=show_FWHM)[0]
							if save_fig:
								fig.savefig(png_location,bbox_inches='tight')
								print(" Figure saved to",png_location)
								window.refresh()
							if display_fig:
								print(" Displaying figure. Close figure to resume.")
								window.refresh()
								plt.show()
							else:
								plt.close()
						print("")
					Source_inst_1.safe_turn_off()
				if Source_2.lower() != 'off':
					Source_inst_2.safe_turn_off()
			if Source_3.lower() != 'off':
				Source_inst_3.safe_turn_off()
		if Source_4.lower() != 'off':
			Source_inst_4.safe_turn_off()
	if Source_5.lower() != 'off':
		Source_inst_5.safe_turn_off()
	if num_sweeps > 1:
		Source_inst_1.GPIB.control_ren(0)
		print(" Disconnected from instruments")
	window.refresh()

if __name__ == "__main__":
	if len(sys.argv)-1 == 1 and (sys.argv[1].lower() == 'debug' or sys.argv[1] == '1'):
		GUI(1)
	else:
		GUI()