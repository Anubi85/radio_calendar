import pyowm
import datetime

class WetherUpdater:
    def __init__(self, owm_info):
        self.__owm = pyowm.OWM(owm_info['api-key'])
        reg = self.__owm.city_id_registry()
        self.__owm_location = reg.locations_for(owm_info['location'], country=owm_info['country'])[0]
        self.sunset_time = None
        self.sunrise_time = None
        self.today_forecast = None
        self.tomorrow_forecast = None
    def update(self):
        observation = self.__owm.weather_manager().one_call(
            lat=self.__owm_location.lat, lon=self.__owm_location.lon)
        self.today_forecast = observation.current.weather_code
        self.sunrise_time = observation.current.sunrise_time('date').astimezone()
        self.sunset_time = observation.current.sunset_time('date').astimezone()
        self.tomorrow_forecast = observation.forecast_daily[0].weather_code
    @property
    def is_daytime(self):
        return self.sunrise_time < datetime.datetime.now(datetime.timezone.utc) < self.sunset_time