import threading
import time

class WetherUpdater(threading.Thread):
    def __init__(self, refresh_time):
        super().__init__()
        self.__refresh_time = refresh_time
        self.__stop = threading.Event()
        self.sunset_time = time.localtime(0)
        self.sunrise_time = time.localtime(0)
        self.today_forecast = 800
        self.tomorrow_forecast = 800
        self.is_daytime = False
    def run(self):
        while not self.__stop.is_set():
            self.__stop.wait(self.__refresh_time)
    def stop(self):
        self.__stop.set()