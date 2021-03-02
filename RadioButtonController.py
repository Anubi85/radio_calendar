from Enums import StationTag
import logging
import gpiozero

class RadioButtonController:
    def __init__(self, radio):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__radio = radio
        #play
        self.__btn_play = gpiozero.Button(pin=12)
        self.__btn_play.when_activated = self.__on_play
        #stop
        self.__btn_stop = gpiozero.Button(pin=25)
        self.__btn_stop.when_activated = self.__on_stop
        #volume up
        self.__btn_volume_up = gpiozero.Button(pin=26)
        self.__btn_volume_up.when_activated = self.__on_volume_up
        #volume down
        self.__btn_volume_down = gpiozero.Button(pin=20)
        self.__btn_volume_down.when_activated = self.__on_volume_down
        #next
        self.__btn_next = gpiozero.Button(pin=16)
        self.__btn_next.when_activated = self.__on_next
        #previous
        self.__btn_previous = gpiozero.Button(pin=13)
        self.__btn_previous.when_activated = self.__on_prev
    
    def __on_play(self):
        self.__logger.debug('Play button pressed')
        self.__radio.play()
    def __on_stop(self):
        self.__logger.debug('Stop button pressed')
        self.__radio.stop()
    def __on_next(self):
        self.__logger.debug('Next button pressed')
        new_station = self.__radio.get_next_station()
        if new_station:
            new_pos = new_station[StationTag.Position]
            self.__radio.set_current(new_pos)
            self.__radio.play()
        else:
            self.__logger.warning('Next station not found')
    def __on_prev(self):
        self.__logger.debug('Previous button pressed')
        new_station = self.__radio.get_prev_station()
        if new_station:
            new_pos = new_station[StationTag.Position]
            self.__radio.set_current(new_pos)
            self.__radio.play()
        else:
            self.__logger.warning('Previous station not found')
    def __on_volume_up(self):
        self.__logger.debug('Volume Up button pressed')
        self.__radio.change_volume(10)
    def __on_volume_down(self):
        self.__logger.debug('Volume Down button pressed')
        self.__radio.change_volume(-10)