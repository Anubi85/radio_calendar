import gpiozero

class GpioUpdater:
    MAIN_LINE = 'main-line'
    BATTERY_LOW = 'battery-low'
    BATTERY_FULL = 'battery-full'
    def __init__(self, pin_factory=None):
        self.__changes_registry = {}
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
            self.__notify_changes('power_status')
        if self.__low_battery.is_pressed != self.__old_low_battery:
            self.__old_low_battery = self.__low_battery.is_pressed
            self.__notify_changes('power_status')
    def __notify_changes(self, prop_name):
        if prop_name in self.__changes_registry:
            for func in self.__changes_registry[prop_name]:
                func()
    def register_for_changes(self, prop_name, func):
        if not prop_name in self.__changes_registry:
            self.__changes_registry[prop_name] = []
        self.__changes_registry[prop_name].append(func)
    @property
    def power_status(self):
        if self.__main_line.is_pressed:
            return GpioUpdater.MAIN_LINE
        elif not self.__low_battery.is_pressed:
            return GpioUpdater.BATTERY_LOW
        else:
            return GpioUpdater.BATTERY_FULL