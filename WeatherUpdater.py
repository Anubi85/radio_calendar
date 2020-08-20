import time

class WetherUpdater:
    def __init__(self):
        self.sunset_time = time.localtime(0)
        self.sunrise_time = time.localtime(0)
        self.today_forecast = 800
        self.tomorrow_forecast = 800
        self.is_daytime = False
    def update(self):
        pass