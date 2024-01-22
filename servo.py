#!/usr/bin/env python3
"""Klasse und Testfunktion zur Ansteuerung eines RC-Servos mithilfe des Raspberry Pi.
"""

__email__ = "teamprojekt@tuhh.de"
__copyright__ = "Technische Universitaet Hamburg, Institut fuer Kunststoffe und Verbundwerkstoffe"
__version__ = "2023.1.2"

import pigpio
import logging
import traceback

class Servo():
	def __init__(self, gpio:int=17, deg_min:float=0., deg_max:float=180., deg_start:float=90., deg_trim:float=0., reverse:bool=False,
	pw_min:int=500, pw_max:int=2400, pw_freq:int=50) -> None:
		"""Klasse zur Ansteuerung eines RC-Servos mithilfe des Raspberry Pi über Software-PWM.
		Args:
			gpio (int, optional):   Hardware PWM Kanal 1: GPIO 12 oder 18.
									Hardware PWM Kanal 2: GPIO 13 oder 19.
									Pro Kanal kann nur ein Signal zur Zeit gesendet werden.
									Software PWM: GPIO pin ohne spezifische Funktion wählen. Defaults to 17.
			deg_min (float, optional): Minimal einstellbarer Winkel. Defaults to 0..
			deg_max (float, optional): Maximal einstellbarer Winkel. Defaults to 180..
			deg_start (float, optional): Startpositionswinkel. Defaults to 90..
			deg_trim (float, optional): Trimmungswinkel. Defaults to 0..
			reverse (bool, optional): Richtungsumkehr. Defaults to False.
			pw_min (int, optional): Minimale Steuerpulsweite (min:500). Defaults to 500.
			pw_max (int, optional): Maximale Steuerpulsweite (max:2500). Defaults to 2400.
		"""
		hpwm_pin=[12,13,18,19]
		if gpio in hpwm_pin:
			self.hpwm=True
		else:
			self.hpwm=False
		self.gpio = gpio
		self.deg_min = deg_min
		self.deg_max = deg_max
		self.deg_start = deg_start
		self.deg_trim = deg_trim
		self.reverse = reverse
		self.pw_min = pw_min
		self.pw_max = pw_max
		self.pw_freq = pw_freq
		self.servo = pigpio.pi()
		self.servo.set_mode(self.gpio, pigpio.OUTPUT)
		self.deg_val = None
		self.servo_write(self.deg_start)

	def __del__(self):
		"""Destruktor zum Loeschen der Servo-Objektreferenzen, z.B. beim Beenden des Programms.
		"""
		self.servo_write(self.deg_start)
		self.servo.stop()

	def servo_reset(self, deg_trim:float=0.):
		"""Zuruecksetzen des Servos: Startpositionswinkel und Trimmungswinkel.
		Args:
			trim (float, optional): Trimmungswinkel. Defaults to 0..
		"""
		self.deg_trim = deg_trim
		self.servo_write(self.deg_start)

	def servo_write(self, deg_val:float):
		"""Einstellen eines vorgegebenen Positionswinkels am Servo.
		Args:
			deg_val (float): Zielpositionswinkel
		"""
		if self.reverse:
			deg_val = self.deg_max - deg_val + self.deg_trim
		else:
			deg_val = deg_val + self.deg_trim
		if deg_val < self.deg_min:
			deg_val = self.deg_min
		elif deg_val > self.deg_max:
			deg_val = self.deg_max
		self.__write(self.deg_2_pw(deg_val))
		self.deg_val = deg_val

	def servo_trim(self):
		"""Aktuellen Positionswinkel als Trimmungswinkel einstellen.
		"""
		self.deg_trim = self.deg_val - self.deg_start

	def deg_2_pw(self, deg_val:float):
		"""Umwandlung eines Positionswinkels in die dazugehoerige Steuerpulsweite.
		Args:
			deg_val (float): Positionswinkel
		Returns:
			int: Steuerpulsweite
		"""
		pw_val = int(self.pw_min + (self.pw_max - self.pw_min) * (deg_val - self.deg_min) / (self.deg_max - self.deg_min))
		return pw_val
	def __write(self, pw_val:int):
		"""[Private] Passt Output an verwendeten Pin an. Nicht Standalone verwenden!
		Args:
			pw_val (int): Zielpulsweite
		"""
		try:
			if self.hpwm:
				conv=pw_val*self.pw_freq
				self.servo.hardware_PWM(self.gpio, self.pw_freq, conv)
			else:
				self.servo.set_servo_pulsewidth(self.gpio, pw_val)
			return True
		except Exception as e:
			print(e)
			return False


def servo_test():
	"""Servo-Testfunktion
	"""
	pin=int(input("Servo GPIO Pin: "))
	logging.basicConfig(filename='servo.log', encoding='utf-8', filemode='w', level=logging.DEBUG)
	try:
		servo = Servo(gpio=pin)
		while True:
			deg_val = float(input('Enter servo motor angle ({} - {}), Abbort with [Strg][C]: '.format(servo.deg_min, servo.deg_max)))
			servo.servo_write(deg_val)
	except Exception as e:
		print(traceback.print_exc())
		logging.error(e, exc_info=True)

if __name__ == "__main__":
	servo_test()
