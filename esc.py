#!/usr/bin/env python3
"""Klasse und Testfunktion zur Ansteuerung eines RC-Reglers und Motors mithilfe des Raspberry Pi.
"""

__email__ = "teamprojekt@tuhh.de"
__copyright__ = "Technische Universitaet Hamburg, Institut fuer Kunststoffe und Verbundwerkstoffe"
__version__ = "2023.1.2"

import pigpio
import logging
import traceback
import time

class Esc:
	def __init__(self, gpio:int=13, pw_min:int=1000, pw_max:int=2000, pw_stop:int=1500, pw_freq:int=50):
		"""Klasse zur Ansteuerung eines RC-Reglers und Motors mithilfe des Raspberry Pi.
		Args:
			gpio (int, optional): 	Hardware PWM Kanal 1: GPIO 12 oder 18.
									Hardware PWM Kanal 2: GPIO 13 oder 19. Defaults to 13.
									Pro Kanal kann nur ein Signal zur Zeit gesendet werden.
									Software PWM: GPIO pin ohne spezifische Funktion wählen.
			pw_min (int, optional): Minimale Steuerpulsweite (min:500, safe: 1000). Defaults to 1000.
			pw_max (int, optional): Maximale Steuerpulsweite (max:2500, safe: 2000). Defaults to 2000.
									Bei Änderung von pw_min, pw_max muss der esc neu programmiert werden.
			pw_stop (int, optional): Steuerpulsweite fuer Motorstillstand. Defaults to 1500.
		"""
		hpwm_pin=[12,13,18,19]
		if gpio in hpwm_pin:
			self.hpwm=True
		else:
			self.hpwm=False
		self.gpio = gpio
		self.pw_min = pw_min
		self.pw_max = pw_max
		self.pw_freq = pw_freq
		self.pw_stop = pw_stop
		self.pw_val = None
		self.esc = pigpio.pi()
		self.esc.set_mode(self.gpio, pigpio.OUTPUT)
		self.esc_write(self.pw_stop)
		time.sleep(2)

	def __del__(self):
		"""Destruktor zum Loeschen der RC-Regler-Objektreferenzen, z.B. beim Beenden des Programms.
		Sicheres Stoppen des Motors.
		"""
		self.esc_write(self.gpio, self.pw_stop)
		self.esc.stop()

	def esc_write(self, pw_val:int, safety:bool=False):
		"""Einstellen einer vorgegebenen Pulsweite am RC-Regler.
		Args:
			pw_val (int): Zielpulsweite
			safety (bool, optional): Langsames Anfahren und Bremsen um Spannungsspitzen zu vermeiden. Defaults to False.
		"""
		if self.pw_val == pw_val:
			return
		if (self.pw_min <= pw_val <= self.pw_max) and pw_val != self.pw_stop:
			if safety:
				if (pw_val < self.pw_stop and self.pw_val > self.pw_stop) or (pw_val > self.pw_stop and self.pw_val < self.pw_stop):
					self.__write(self.pw_stop)
					self.pw_val = self.pw_stop
					time.sleep(1)
				self.esc_safe_acceleration(pw_val)
			else:
				self.__write(pw_val)
			self.pw_val = pw_val
		else:
			self.__write(self.pw_stop)
			self.pw_val = self.pw_stop

	def esc_safe_acceleration(self, pw_val: int):
		"""Langsames Anfahren und Bremsen um Spannungsspitzen zu vermeiden.
		Args:
			pw_val (int): Zielpulsweite
		"""
		if pw_val > self.pw_val:
			pw_range = range(self.pw_val, pw_val + 1, 10)
		else:
			pw_range = range(self.pw_val, pw_val -1 , -10)
		for pw in pw_range:
			self.__write(pw)
			time.sleep(0.01)
	def __write(self, pw_val:int):
		"""[Private] Passt Output an verwendeten Pin an. Nicht Standalone verwenden!
		Args:
			pw_val (int): Zielpulsweite
		"""
		try:
			if self.hpwm:
				conv=pw_val*self.pw_freq
				self.esc.hardware_PWM(self.gpio, self.pw_freq, conv)
			else:
				self.esc.set_servo_pulsewidth(self.gpio, pw_val)
			return True
		except Exception as e:
			print(e)
			return False

	def program_esc(self):
		"""ESC Programmieren
		"""
		print("ESC Programmieren")
		print("Make sure the motor and all other components are secured, before you continue!")
		input("Disconnect battery from ESC! (press Enter to continue)")
		pw=int(input("Enter max pulsewidth (min 1600, max 2500): "))
		while 1600<pw or pw>2500:
			pw=int(input("Out of Range! Enter max pulsewidth (min 1600, max 2500): "))
		self.__write(pw)
		input("Connect battery to ESC! (press Enter to continue)")
		input("Wait for beep (press Enter when the motor beeped)")
		self.__write(self.pw_stop)
		print("If everything worked, the motor should beep positively")


def esc_test():
	"""RC-Regler-Testfunktion
	"""
	logging.basicConfig(filename='esc.log', encoding='utf-8', filemode='w', level=logging.DEBUG)
	pin=int(input("ESC Pin: "))
	try:
		print("Make sure the motor and all other components are secured, before you continue!")
		esc = Esc(gpio=pin)
		while True:
			pwm_value = int(input('Enter motor speed [min: {} (backwards), max: {} (forward), {} (stop)], Abbort with [Strg][C]: '.format(esc.pw_min, esc.pw_max, esc.pw_stop)))
			esc.esc_write(pwm_value)
	except Exception as e:
		print(traceback.print_exc())
		logging.error(e, exc_info=True)

if __name__ == "__main__":
	"""zum ESC programmieren esc_test() mit
	esc=Esc(gpio=)
	esc.program_esc() ersetzen
	"""
	esc_test()
