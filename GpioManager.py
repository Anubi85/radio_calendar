import gpiozero
from Enums import Input
import logging

class GpioManager:
    BATTERY_LOW = 'battery-low'
    BATTERY_FULL = 'battery-full'
    MAIN_LINE = 'main-line'
    def __init__(self, pin_factory=None):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__changes_registry = []
        #main line
        self.__main_line = gpiozero.Button(pin=5, pull_up=False, pin_factory=pin_factory)
        self.__main_line.when_activated = self.__on_power_state_changed
        self.__main_line.when_deactivated = self.__on_power_state_changed
        #battery low
        self.__low_battery = gpiozero.Button(pin=6, pull_up=False, pin_factory=pin_factory)
        self.__low_battery.when_activated = self.__on_power_state_changed
        self.__low_battery.when_deactivated = self.__on_power_state_changed
        #play
        self.__btn_play = gpiozero.Button(pin=12, pin_factory=pin_factory)
        self.__btn_play.when_activated = self.__on_btn_play_activated
        #stop
        self.__btn_stop = gpiozero.Button(pin=25, pin_factory=pin_factory)
        self.__btn_stop.when_activated = self.__on_btn_stop_activated
        #volume up
        self.__btn_volume_up = gpiozero.Button(pin=26, pin_factory=pin_factory)
        self.__btn_volume_up.when_activated = self.__on_btn_volume_up_activated
        #volume down
        self.__btn_volume_down = gpiozero.Button(pin=20, pin_factory=pin_factory)
        self.__btn_volume_down.when_activated = self.__on_btn_volume_down_activated
        #next
        self.__btn_next = gpiozero.Button(pin=16, pin_factory=pin_factory)
        self.__btn_next.when_activated = self.__on_btn_next_activated
        #previous
        self.__btn_previous = gpiozero.Button(pin=13, pin_factory=pin_factory)
        self.__btn_previous.when_activated = self.__on_btn_previous_activated
        self.__power_state = GpioManager.BATTERY_LOW

    def __on_power_state_changed(self):
        main_line = self.__main_line.is_pressed
        full_battery = self.__low_battery.is_pressed
        self.__logger.debug('Power Source: {0}'.format('Main Line' if main_line else 'Battery'))
        self.__logger.debug('Battery State: {0}'.format('Full' if full_battery else 'Low'))
        if main_line:
            new_power_state = GpioManager.MAIN_LINE
        elif full_battery:
            new_power_state = GpioManager.BATTERY_FULL
        else:
            new_power_state = GpioManager.BATTERY_LOW
        if new_power_state != self.__power_state:
            self.__power_state = new_power_state
            self.__notify_changes(Input.PowerState)
    def __on_btn_play_activated(self):
        self.__logger.debug('Play button pressed')
        self.__notify_changes(Input.Play)
    def __on_btn_stop_activated(self):
        self.__logger.debug('Stop button pressed')
        self.__notify_changes(Input.Stop)
    def __on_btn_volume_up_activated(self):
        self.__logger.debug('Volume Up button pressed')
        self.__notify_changes(Input.VolUp)
    def __on_btn_volume_down_activated(self):
        self.__logger.debug('Volume Down button pressed')
        self.__notify_changes(Input.VolDown)
    def __on_btn_next_activated(self):
        self.__logger.debug('Next button pressed')
        self.__notify_changes(Input.Next)
    def __on_btn_previous_activated(self):
        self.__logger.debug('Previous button pressed')
        self.__notify_changes(Input.Prev)
    def __notify_changes(self, prop_name):
        for func in self.__changes_registry:
            self.__logger.debug('Notify change of {0} to {1}'.format(prop_name, repr(func)))
            func(prop_name)
    def register_for_changes(self, func):
        self.__logger.debug('Function {0} registered for input changes notification'.format(repr(func)))
        self.__changes_registry.append(func)
    @property
    def power_state(self):
        return self.__power_state