import gpiozero
from Enums import Input

#TODO: loggare pressione pulsanti
#TODO: implementare lettura nuovi pulsanti

class GpioUpdater:
    def __init__(self, pin_factory=None):
        self.__changes_registry = []
        self.__main_line = gpiozero.Button(pin=5, pull_up=False, pin_factory=pin_factory)
        self.__low_battery = gpiozero.Button(pin=6, pull_up=False, pin_factory=pin_factory)
        self.__play_pause = gpiozero.Button(pin=12, pin_factory=pin_factory)
        self.__next_station = gpiozero.Button(pin=13, pin_factory=pin_factory)
        self.__prev_station = gpiozero.Button(pin=16, pin_factory=pin_factory)
        self.__volume_up = gpiozero.Button(pin=20, pin_factory=pin_factory)
        self.__volume_down = gpiozero.Button(pin=26, pin_factory=pin_factory)
        self.__old_main_line = None
        self.__old_low_battery = None
    def update(self):
        if self.__main_line.is_pressed != self.__old_main_line:
            self.__old_main_line = self.__main_line.is_pressed
            self.__notify_changes(Input.PowerState)
        if self.__low_battery.is_pressed != self.__old_low_battery:
            self.__old_low_battery = self.__low_battery.is_pressed
            self.__notify_changes(Input.PowerState)
    def __notify_changes(self, prop_name):
        for func in self.__changes_registry:
            func(prop_name)
    def register_for_changes(self, func):
        self.__changes_registry.append(func)
    @property
    def power_status(self):
        if self.__main_line.is_pressed:
            return 'main-line'
        elif not self.__low_battery.is_pressed:
            return 'battery-low'
        else:
            return 'battery-full'