"""Hauptfunktion zur Ansteuerung eines RC-Modells mithilfe des Raspberry Pi.
"""

__email__ = "teamprojekt@tuhh.de"
__copyright__ = "Technische Universitaet Hamburg, Institut fuer Kunststoffe und Verbundwerkstoffe"
__version__ = "2023.1.0"

from esc import Esc
from servo import Servo
from dev import Controller
from evdev import list_devices, InputDevice, categorize, ecodes, ff
import sys
import os
from threading import Timer

SERVO_RANGE = 90   # Konstante für die Winkelanpassung des Servos

class Speed:        # Klasse, wo alle Funktionen für die Geschwindigkeitsanpassung und Lenkung enthalten sind
    def __init__(self, dev: Controller):
        self.speed_P1 = 1500    # Konstanten die verwendet werden
        self.speed_P2 = 1500
        self.LT_value = 0
        self.RT_value = 0
        self.dev = dev

        self.esc1 = Esc(gpio = 10, pw_stop = 1500, pw_min = 1200, pw_max = 1800)   # Objekt der Klasse Esc erstellen
        self.esc2 = Esc(gpio = 24, pw_stop = 1500, pw_min = 1200, pw_max = 1800)   # Objekt der Klasse Esc erstellen

    def update(self, event):
        if event.code == self.dev.ABS_LSY:   # Zuordnung des linken Joysticks, der die Beschleunigung für Motor1 anpasst
            stick_value = - event.value / self.dev.max_value_stick
            max_speed = self.esc1.pw_stop - self.esc1.pw_min if stick_value < 0 else self.esc1.pw_max - self.esc1.pw_stop
            self.speed_P1 = (stick_value * max_speed) + self.esc1.pw_stop
            if self.speed_P1 >= 1450 and self.speed_P1 <= 1550:
                self.speed_P1 = 1500

        if event.code == self.dev.ABS_LSY:   # Zuordnung des linken Joysticks, der die Beschleunigung für Motor2 anpasst
            stick_value = - event.value / self.dev.max_value_stick
            max_speed = self.esc2.pw_stop - self.esc2.pw_min if stick_value < 0 else self.esc2.pw_max - self.esc2.pw_stop
            self.speed_P2 = (stick_value * max_speed) + self.esc2.pw_stop
            if self.speed_P2 >= 1450 and self.speed_P2 <= 1550:
                self.speed_P2 = 1500

        if event.code == self.dev.ABS_LT:   # Zuordnung des linken Triggers, um Lenkung nach oben und unten zu verursachen
            trigger_value = event.value / self.dev.max_value_trigger
            self.LT_value = trigger_value
            print("Trigger 1 ", trigger_value)

        if event.code == self.dev.ABS_RT:   # Zuordnung des rechten Triggers, um Lenkung nach oben und unten zu verursachen
            trigger_value = event.value / self.dev.max_value_trigger
            self.RT_value = trigger_value
            print("Trigger 2 ", trigger_value)

        
    def write_speed(self):      # Funktion, um die Geschwindigkeit zu berechnen
        speed1 = self.speed_P1 - self.LT_value * (self.speed_P1 - self.esc1.pw_stop)
        self.esc1.esc_write(int(speed1), True)

        speed2 = self.speed_P2 - self.RT_value * (self.speed_P2 - self.esc2.pw_stop)
        self.esc2.esc_write(int(speed2), True)

        print("Speed1: ", speed1, "   Speed2: ", speed2)

button_timer = {}

def on_hold(dev: Controller, event, press_time, callback):  # Die Funktion on_hold überwacht, wie lange ein bestimmter Knopf auf dem Controller gedrückt wird
    if event.value == 1:        
        dev.rumble(length_ms = 200) 
        button_timer[dev.BTN_START] = Timer(press_time, callback, [dev])    
        button_timer[dev.BTN_START].start()
    elif not button_timer[dev.BTN_START] is None:
        button_timer[dev.BTN_START].cancel()
        button_timer[dev.BTN_START] = None

def restart_pi(dev: Controller):    # Funktion, um den Pi neuzustarten
    print("Restarting Pi...")
    dev.rumble()
    os.system("sudo reboot")

def shutdown_pi(dev: Controller):   # Funktion, um den Pi herunterzufahren
    print("Shutting down Pi...")
    dev.rumble()
    os.system("sudo shutdown -h now")

def main():
    servo1 = Servo(gpio = 18, deg_min = 0, deg_max = SERVO_RANGE * 2, deg_start = SERVO_RANGE) # Objekt der Klasse Servo erstellen
    servo2 = Servo(gpio = 27, deg_min = -90, deg_max = SERVO_RANGE * 2, deg_start = SERVO_RANGE) # Objekt der Klasse Servo erstellen

    print("Connecting controller...")
    dev = Controller()
    speed_controller = Speed(dev)
    print("Controller connected")

    for event in dev.dev.read_loop():
        if event.code == dev.BTN_START: # Zuordnung des Start-Knopfs, der den Pi restartet
            on_hold(dev, event, 2, restart_pi)
            print("START Button: ", event.value)

        if event.code == dev.BTN_BACK:  # Zuordnung des Back-Knopfs, der den Pi herunterfährt
            on_hold(dev, event, 2, shutdown_pi)
            print("BACK Button: ", event.value)

        if event.code == dev.BTN_B: # Zuordnung des B-Knopfs, der main.py neustartet
            print("Restarting program...")
            sys.stdout.flush()
            os.execv(sys.executable, ["python3"] + sys.argv)

        speed_controller.update(event)
        speed_controller.write_speed()
        
        if event.code == dev.ABS_RSX:   # Zuordnung des rechten Joysticks, der für die Lenkung zuständig ist.
            deg = event.value / dev.max_value_stick * SERVO_RANGE + SERVO_RANGE
            servo1.servo_write(deg)
            print("Servowinkel 1: ", deg)

        if event.code == dev.ABS_RSX:   # Zuordnung des rechten Joysticks, der für die Lenkung zuständig ist.
            deg = event.value / dev.min_value_stick * SERVO_RANGE + SERVO_RANGE
            servo2.servo_write(deg)
            print("Servowinkel 2: ", deg)

        if event.code == dev.BTN_A:     # Zuordnung des A-Knopfs, der den momentanen Winkel als Trimmwinkel speichert.
           servo1.servo_trim()

        if event.code == dev.BTN_A:     # Zuordnung des A-Knopfs, der den momentanen Winkel als Trimmwinkel speichert.
           servo2.servo_trim()

if __name__ == "__main__":
    main()
