#########################################################################
# Script to set laser diode bias conditions                             #
# using up to five current/voltage sources (various models)             #
#                                                                       #
# Author: Trevor Stirling                                               #
# Date: Aug 23, 2024                                                    #
#########################################################################

import numpy as np
import matplotlib.pyplot as plt
import sys, os
import time
from GUI_common_functions import BluePSGButton,enforce_number,plus_button,minus_button,get_file_locations_GUI,connect_to_PM,connect_to_GPIB,plot_LIV
import PySimpleGUI as psg

font = 'Tahoma'
GUI_defaults_dir = os.path.join(os.path.dirname(__file__),"GUI Defaults")
GUI_file = os.path.basename(__file__).replace(" GUI.py",".txt")

def current_source_title(num):
	return [[psg.Text('--------------- Source '+str(num)+' Options ---------------',font=(font, 20))]]

def current_source_layout(num):
	layout = [[psg.Text('Source:'), psg.Combo(['K2520', 'K2604B', 'B2902A', 'LDC3908', 'LDC3916', 'OFF'], default_value='OFF', size=(8,1), enable_events=True, readonly=True, key='source_'+str(num)), psg.Text('Channel:'), psg.Combo([''], size=(3,1), readonly=True, key='source_'+str(num)+'_channel'),psg.Text('Mode:'), psg.Combo(['Current', 'Voltage'], default_value='Current', size=(8,1), enable_events=True, readonly=True, key='source_'+str(num)+'_mode'), psg.Text('Protection Voltage [V]:',key='protection_'+str(num)+'_text'), psg.InputText('4', key='protection_'+str(num), size=(4,1), enable_events=True)],
	[psg.Text('Bias:'),psg.InputText('1', key='bias_'+str(num), size=(4,1), enable_events=True),psg.Text('[mA]',key='units_'+str(num)),psg.Checkbox('Pulsed', size=(8,1), key='pulsed_'+str(num), default=False, enable_events=True),psg.Text('Pulse Width [μs]:', key='pulse_width_'+str(num)+'_text', visible=False),psg.InputText('8', key='pulse_width_'+str(num), size=(2,1), enable_events=True, visible=False),psg.Text('Pulse Delay [μs]:', key='pulse_delay_'+str(num)+'_text', visible=False),psg.InputText('160', key='pulse_delay_'+str(num), size=(4,1), enable_events=True, visible=False)]]
	return layout

def GUI(debug=False):
	#Options
	psg.set_options(font=(font, 16))
	psg.theme('DarkBlue14')
	default_source = 'B2902A'
	num_sources = 1
	#Define layout
	if debug:
		print_window = []
	else:
		print_window = [psg.Multiline(size=(10,5), expand_x=True, expand_y=True, key='output', reroute_stdout=True)]
	layout = [[psg.Button('', image_data=minus_button, image_subsample=12, button_color=('black', psg.theme_background_color()), border_width=0, enable_events=True, key='remove_source'), psg.Text('Add or Remove Sources'), psg.Button('', image_data=plus_button, image_subsample=12, button_color=('black', psg.theme_background_color()), border_width=0, enable_events=True, key='add_source')],
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
	[BluePSGButton('Ω Check'),BluePSGButton('Zero Bias'), psg.Push(), BluePSGButton('Set Bias'), BluePSGButton('Exit')], #push adds flexible whitespace
	print_window]
	#Create window
	window = psg.Window('Set Bias',layout, resizable=True)
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
				if key in ['source_'+str(i+1) for i in range(5)] and value != 'OFF':
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
		elif event == 'Set Bias':
			Set_Bias(window,values)
		elif event == 'Zero Bias':
			Set_Bias(window,values,True)
		elif event == 'Ω Check':
			resistance_check(window,values)
		#data validation
		elif event in ['protection_'+str(i+1) for i in range(5)]:
			enforce_number(window,values,event,negative_allowed=True)
		elif event in ['bias_'+str(i+1) for i in range(5)]:
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

def update_source_visibility(window,num_sources):
	for i in range(5):
		if i<num_sources:
			window['source_'+str(i+1)+'_title'].update(visible=True)
			window['source_'+str(i+1)+'_options'].update(visible=True)
		else:
			window['source_'+str(i+1)+'_options'].update(visible=False)
			window['source_'+str(i+1)+'_title'].update(visible=False)
			window['source_'+str(i+1)].update(value='OFF')

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
	window.Refresh()
	if not Source_inst:
		return
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

def Set_Bias(window,values,turn_off_all=False):
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
	Source_bias_1 = float(values['bias_1'])
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
	Source_bias_2 = float(values['bias_2'])
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
	Source_bias_3 = float(values['bias_3'])
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
	Source_bias_4 = float(values['bias_4'])
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
	Source_bias_5 = float(values['bias_5'])
	pulsed_5 = values['pulsed_5']
	if pulsed_5:
		waveform_5 = 'pulsed'
	else:
		waveform_5 = 'DC'
	pulse_width_5 = int(values['pulse_width_5'])*1e-6
	pulse_delay_5 = int(values['pulse_delay_5'])*1e-6
	### Connect to Lab Equipment
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
	### Convert currents
	if Source_1_mode == 'Current':
		Source_bias_1 = Source_bias_1*1e-3
	if Source_2_mode == 'Current':
		Source_bias_2 = Source_bias_2*1e-3
	if Source_3_mode == 'Current':
		Source_bias_3 = Source_bias_3*1e-3
	if Source_4_mode == 'Current':
		Source_bias_4 = Source_bias_4*1e-3
	if Source_5_mode == 'Current':
		Source_bias_5 = Source_bias_5*1e-3
	### Check for turn_off flag
	if turn_off_all:
		Source_bias_1 = 0
		Source_bias_2 = 0
		Source_bias_3 = 0
		Source_bias_4 = 0
		Source_bias_5 = 0
	### Set bias
	if Source_1.lower() != 'off':
		if Source_inst_1.is_on():
			if Source_bias_1 == 0:
				Source_inst_1.safe_turn_off()
			else:
				Source_value = Source_inst_1.read_setting()
				if Source_1_mode == 'Current':
					step = 10e-3
				else:
					step = 0.1
				if Source_bias_1<Source_value:
					step = -1*step
				for bias in np.arange(Source_value,Source_bias_1,step):
					Source_inst_1.set_value(bias)
					time.sleep(0.1)
				Source_inst_1.set_value(Source_bias_1)
		elif Source_bias_1 != 0:
			Source_inst_1.safe_turn_on(Source_bias_1)
		if Source_1_mode == 'Current':
			print(" Source #1 = "+str(round(Source_bias_1*1e3))+" mA")
		else:
			print(" Source #1 = "+str(round(Source_bias_1*10)/10)+" V")
		window.Refresh()
	if Source_2.lower() != 'off':
		if Source_inst_2.is_on():
			if Source_bias_2 == 0:
				Source_inst_2.safe_turn_off()
			else:
				Source_value = Source_inst_2.read_setting()
				if Source_2_mode == 'Current':
					step = 10e-3
				else:
					step = 0.1
				if Source_bias_2<Source_value:
					step = -1*step
				for bias in np.arange(Source_value,Source_bias_2,step):
					Source_inst_2.set_value(bias)
					time.sleep(0.1)
				Source_inst_2.set_value(Source_bias_2)
		elif Source_bias_2 != 0:
			Source_inst_2.safe_turn_on(Source_bias_2)
		if Source_2_mode == 'Current':
			print(" Source #2 = "+str(round(Source_bias_2*1e3))+" mA")
		else:
			print(" Source #2 = "+str(round(Source_bias_2*10)/10)+" V")
		window.Refresh()
	if Source_3.lower() != 'off':
		if Source_inst_3.is_on():
			if Source_bias_3 == 0:
				Source_inst_3.safe_turn_off()
			else:
				Source_value = Source_inst_3.read_setting()
				if Source_3_mode == 'Current':
					step = 10e-3
				else:
					step = 0.1
				if Source_bias_3<Source_value:
					step = -1*step
				for bias in np.arange(Source_value,Source_bias_3,step):
					Source_inst_3.set_value(bias)
					time.sleep(0.1)
				Source_inst_3.set_value(Source_bias_3)
		elif Source_bias_3 != 0:
			Source_inst_3.safe_turn_on(Source_bias_3)
		if Source_3_mode == 'Current':
			print(" Source #3 = "+str(round(Source_bias_3*1e3))+" mA")
		else:
			print(" Source #3 = "+str(round(Source_bias_3*10)/10)+" V")
		window.Refresh()
	if Source_4.lower() != 'off':
		if Source_inst_4.is_on():
			if Source_bias_4 == 0:
				Source_inst_4.safe_turn_off()
			else:
				Source_value = Source_inst_4.read_setting()
				if Source_4_mode == 'Current':
					step = 10e-3
				else:
					step = 0.1
				if Source_bias_4<Source_value:
					step = -1*step
				for bias in np.arange(Source_value,Source_bias_4,step):
					Source_inst_4.set_value(bias)
					time.sleep(0.1)
				Source_inst_4.set_value(Source_bias_4)
		elif Source_bias_4 != 0:
			Source_inst_4.safe_turn_on(Source_bias_4)
		if Source_4_mode == 'Current':
			print(" Source #4 = "+str(round(Source_bias_4*1e3))+" mA")
		else:
			print(" Source #4 = "+str(round(Source_bias_4*10)/10)+" V")
		window.Refresh()
	if Source_5.lower() != 'off':
		if Source_inst_5.is_on():
			if Source_bias_5 == 0:
				Source_inst_5.safe_turn_off()
			else:
				Source_value = Source_inst_5.read_setting()
				if Source_5_mode == 'Current':
					step = 10e-3
				else:
					step = 0.1
				if Source_bias_5<Source_value:
					step = -1*step
				for bias in np.arange(Source_value,Source_bias_5,step):
					Source_inst_5.set_value(bias)
					time.sleep(0.1)
				Source_inst_5.set_value(Source_bias_5)
		elif Source_bias_5 != 0:
			Source_inst_5.safe_turn_on(Source_bias_5)
		if Source_5_mode == 'Current':
			print(" Source #5 = "+str(round(Source_bias_5*1e3))+" mA")
		else:
			print(" Source #5 = "+str(round(Source_bias_5*10)/10)+" V")
		window.Refresh()
	print("")
	Source_inst_1.GPIB.control_ren(0)
	print(" Disconnected from instruments")
	window.Refresh()

if __name__ == "__main__":
	if len(sys.argv)-1 == 1 and (sys.argv[1].lower() == 'debug' or sys.argv[1] == '1'):
		GUI(1)
	else:
		GUI()