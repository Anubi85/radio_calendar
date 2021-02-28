import gpiozero
from Enums import Input

#TODO: loggare
#TODO: modificare funzionamento, non serve il polling, non sarà più un updater

class GpioUpdater:
    def __init__(self, pin_factory=None):
        self.__changes_registry = []
        self.__main_line = gpiozero.Button(pin=5, pull_up=False, pin_factory=pin_factory)
        self.__low_battery = gpiozero.Button(pin=6, pull_up=False, pin_factory=pin_factory)
        self.__btn_12 = gpiozero.Button(pin=12, pin_factory=pin_factory)
        self.__btn_12.when_activated = self.__btn_12_press
        self.__btn_13 = gpiozero.Button(pin=13, pin_factory=pin_factory)
        self.__btn_13.when_activated = self.__btn_13_press
        self.__btn_16 = gpiozero.Button(pin=16, pin_factory=pin_factory)
        self.__btn_16.when_activated = self.__btn_16_press
        self.__btn_20 = gpiozero.Button(pin=20, pin_factory=pin_factory)
        self.__btn_20.when_activated = self.__btn_20_press
        self.__btn_25 = gpiozero.Button(pin=25, pin_factory=pin_factory)
        self.__btn_25.when_activated = self.__btn_25_press
        self.__btn_26 = gpiozero.Button(pin=26, pin_factory=pin_factory)
        self.__btn_26.when_activated = self.__btn_26_press
        self.__old_main_line = None
        self.__old_low_battery = None
    def __power_state_changed(self):
        self.__notify_changes(Input.PowerState)
    def __btn_12_press(self):
        print(12)
    def __btn_13_press(self):
        print(13)
    def __btn_16_press(self):
        print(16)
    def __btn_20_press(self):
        print(20)
    def __btn_25_press(self):
        print(25)
    def __btn_26_press(self):
        print(26)
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