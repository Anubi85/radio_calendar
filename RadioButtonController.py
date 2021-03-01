from Enums import Input
import logging

class RadioButtonController:
    def __init__(self, radio, gpio):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__radio = radio
        self.__gpio = gpio
        self.__gpio.register_for_changes(self.__on_button_pressed)
        self.__actions = {}
        self.__actions[Input.Play] = self.__on_play
        self.__actions[Input.Stop] = self.__on_stop
        self.__actions[Input.Next] = self.__on_next
        self.__actions[Input.Prev] = self.__on_prev
        self.__actions[Input.VolUp] = self.__on_volume_up
        self.__actions[Input.VolDown] = self.__on_volume_down
    
    #TODO: implementare funzioni
    def __on_play(self):
        pass
    def __on_stop(self):
        pass
    def __on_next(self):
        pass
    def __on_prev(self):
        pass
    def __on_volume_up(self):
        pass
    def __on_volume_down(self):
        pass

    def __on_button_pressed(self, prop_name):        
        action = self.__actions.get(prop_name, None)
        if action:
            self.__logger.debug('Button {0} pressed'.format(prop_name))
            action()