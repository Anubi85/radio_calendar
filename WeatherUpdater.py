import pyowm
import datetime
import logging

class WeatherUpdater:
    def __init__(self, owm_info):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__owm = pyowm.OWM(owm_info['api-key'])
        reg = self.__owm.city_id_registry()
        self.__owm_location = reg.locations_for(owm_info['location'], country=owm_info['country'])[0]
        self.sunset_time = None
        self.sunrise_time = None
        self.today_forecast = None
        self.tomorrow_forecast = None
        self.uv_index = None
    def update(self):
        try:
            weather_data = self.__owm.weather_manager().one_call(
                lat=self.__owm_location.lat, lon=self.__owm_location.lon)
            self.uv_index = int(weather_data.current.uvi)
            self.today_forecast = weather_data.current.weather_code
            self.sunrise_time = weather_data.current.sunrise_time('date').astimezone()
            self.sunset_time = weather_data.current.sunset_time('date').astimezone()
            self.tomorrow_forecast = weather_data.forecast_daily[0].weather_code
        except Exception as ex:
            #some error occured, log the exception and keep trying
            self.__logger.error(ex)
    @property
    def is_daytime(self):
        return self.sunrise_time < datetime.datetime.now(self.sunrise_time.tzinfo) < self.sunset_time