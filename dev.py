#!/usr/bin/env python3
"""Klasse und Testfunktion zur Ansteuerung eines Xbox-Controllers mithilfe des Raspberry Pi.
"""

__email__ = "teamprojekt@tuhh.de"
__copyright__ = "Technische Universitaet Hamburg, Institut fuer Kunststoffe und Verbundwerkstoffe"
__version__ = "2023.1.0"

from evdev import list_devices, InputDevice, categorize, ecodes, ff
import sys
import time
import logging
import traceback

class Controller():
	def __init__(self, setup:bool=False, device_name:str='Xbox Wireless Controller', controller_driver:str='xpadneo'):
		"""Klasse zur Ansteuerung eines Xbox-Controllers mithilfe des Raspberry Pi.
		Args:
			setup (bool, optional): Weitere Informationen bei der Einrichtung des Controllers anzeigen. Defaults to False.
			device_name (str, optional): Bezeichnung des zu verbindenen Controllers. Defaults to 'Xbox Wireless Controller'.
			controller_driver (str, optional): Installierter Controller-Treibername. Defaults to 'xpadneo'.
		"""
		self.setup = setup
		self.device_name = device_name
		self.controller_driver = controller_driver
		self.dev = self.device_select()
		self.device_setup()
		self.rumble(length_ms=200, delay_ms=100, repeat_count=2)

	def device_select(self):
		"""Auswahl des Controllers aus den verbundenen Geraeten.
		Anzeigen aller verbundenen Geraete im Setup Modus.
		Errormeldung falls der Controller nicht gefunden werden kann.
		Returns:
			InputDevice: Ausgewaelter Xbox Controller
		"""
		device_selected = None
		if self.setup:
			print('Available devices:')
			devices = [InputDevice(path) for path in list_devices()]
			for idx, device in enumerate(devices):
				print('{} -  path: {}, name: {}, phys: {}'.format(idx, device.path, device.name, device.phys))
			device_id = int(input('Select your device [0-{}]: '.format(idx)))
			if device_id in range(idx + 1):
				device_selected = InputDevice(list_devices()[device_id])
				print('Device connected: {}'.format(device_selected))
				return device_selected
		else:
			timeout = time.time() + 60*2
			while True:
				devices = [InputDevice(path) for path in list_devices()]
				if time.time() > timeout:
					break
				for device in devices:
					if self.device_name == device.name:
						device_selected = InputDevice(device)
						print('Device connected: {}'.format(device_selected))
						return device_selected
				time.sleep(5)
		if device_selected is None:
			sys.exit('Error: No valid device selected/connected.')

	def device_setup(self):
		"""Zuweisung aller Controller Funktionen abhaengig vom gewaehlten Treibertyp.
		"""
		if self.setup:
			print('Device capabilities: {}'.format(self.dev.capabilities(verbose=True)))
			print('Device LEDs: {}'.format(self.dev.leds(verbose=True)))
		if self.controller_driver == 'xpadneo':
			# Button, Values: 0; 1
			self.BTN_A = 304	# A
			self.BTN_B = 305	# B
			self.BTN_X = 307	# X
			self.BTN_Y = 308	# Y
			self.BTN_START = 315	# Start
			self.BTN_BACK = 314	# Back
			self.BTN_LB = 310	# Left Bumper
			self.BTN_RB = 311	# Right Bumper
			self.BTN_LS = 317	# Left Stick
			self.BTN_RS = 318	# Right Stick
			# D-Pad, Values: 0; -1; 1
			self.ABS_DX = 16	# D-Pad, X-Axis
			self.ABS_DY = 17	# D-Pad, Y-Axis
			# Joystick, Values: -32767-32767
			self.min_value_stick = -32767	# Min Value, Joystick
			self.max_value_stick = 32767	# Max Value, Joystick
			self.ABS_LSX = 0	# Left Stick, X-Axis
			self.ABS_LSY = 1	# Left Stick, Y-Axis
			self.ABS_RSX = 3	# Right Stick, X-Axis
			self.ABS_RSY = 4	# Right Stick, Y-Axis
			# Trigger, Werte: 0-1023
			self.min_value_trigger = 0      # Min Value Trigger
			self.max_value_trigger = 1023	# Max Value Trigger
			self.ABS_RT = 5	# Rechter Trigger
			self.ABS_LT = 2	# Linker Trigger
			# Kombinierte Trigger, Werte: -1023-1023
			self.ABS_RTLT = 40	# Kombinierter Linker+Rechter Trigger
		else:
			sys.exit('Error: Please select/define your own controller driver.')

	def rumble(self, length_ms:int=1000, delay_ms:int=0, repeat_count:int=1):
		"""Aktivierung der Vibrationsfunktion am Controller.
		Args:
			length_ms (int, optional): Vibrationsdauer. Defaults to 1000.
			delay_ms (int, optional): Zeit zwischen Vibrationen. Defaults to 0.
			repeat_count (int, optional): Anzahl der Wiederholungen. Defaults to 1.
		"""
		rumble = ff.Rumble(0x0000, 0xffff)
		effect_type = ff.EffectType(ff_rumble_effect=rumble)
		effect = ff.Effect(
				ecodes.FF_RUMBLE, -1, 0,
				ff.Trigger(0, 0),
				ff.Replay(length_ms, delay_ms),
				effect_type
			)
		effect_id = self.dev.upload_effect(effect)
		self.dev.write(ecodes.EV_FF, effect_id, repeat_count)

def controller_test(setup=False):
	"""Controller-Testfunktion
	"""
	logging.basicConfig(filename='dev.log', encoding='utf-8', filemode='w', level=logging.DEBUG)
	try:
		dev = Controller(setup=setup)
		for event in dev.dev.read_loop():
			if event.type == ecodes.EV_KEY or event.type == ecodes.EV_ABS:
				print('Type: ', event.type, 'ID: ', event.code, 'Value: ',  event.value)
	except Exception as e:
		print(traceback.print_exc())
		logging.error(e, exc_info=True)

if __name__ == "__main__":
	controller_test()
