from inky import InkyPHAT
from PIL import Image
import time
import os
import re

class Font:
    def __init__(self, masks_path):
        self.__masks = {int(''.join([c for c in f if c.isdigit()])):Image.open(masks_path + '/' + f) for f in os.listdir(masks_path) if f.endswith('.png')}
        size = next(iter(self.__masks.values())).size
        self.__clear = Image.new('P', size, InkyPHAT.BLACK)
        self.__draw = Image.new('P', size, InkyPHAT.YELLOW)
    def __getitem__(self, key):
        if key == 'clear':
            return self.__clear
        elif key == 'draw':
            return self.__draw
        elif type(key) is int and key in self.__masks.keys():
            return self.__masks[key]
        else:
            return None

class Icon:
    def __init__(self, icon_path):
        self.__icon = Image.open(icon_path)
        self.__clear = Image.new('P', self.__icon.size, InkyPHAT.BLACK)
    def __getitem__(self, key):
        if key == 'draw':
            return self.__icon
        elif key == 'clear':
            return self.__clear
        else:
            return None

class DisplayUpdater:
    __SENSOR_FONT1 = 0
    __SENSOR_FONT2 = 1
    __TIME_FONT1 = 2
    __TIME_FONT2 = 3
    __TIME_FONT3 = 4
    __DATE_FONT1 = 5
    __DATE_FONT2 = 6
    __MONTH_FONT = 7
    __WEEK_DAY_FONT = 8

    def __init__(self, display_resources, bme280, weather_info, audio_controller):
        super().__init__()
        self.__resources = display_resources
        self.__bme280 = bme280
        self.__weather_info = weather_info
        self.__audio_controller = audio_controller
        self.__display = InkyPHAT('yellow')
        self.__display.set_border(InkyPHAT.BLACK)
        self.__screen_image = Image.open(self.__resources['background'])
        self.__fonts = []
        for font in self.__resources['fonts']:
            self.__fonts.append(Font(font))
        self.__weather_icons_day = {}
        self.__weather_icons_night = {}
        for icon in self.__resources['weather-icons']:
            day = Icon(icon['day'])
            night = Icon(icon['night'])
            for code in icon['codes']:
                self.__weather_icons_day[code] = day
                self.__weather_icons_night[code] = night
        self.__alarm_icon = Icon(self.__resources['alarm-icon'])
        self.__old_temperature = None
        self.__old_humidity = None
        self.__old_pressure = None
        self.__old_time_date = None
        self.__old_sunset_time = None
        self.__old_sunrise_time = None
        self.__old_today_forecast = None
        self.__old_tomorrow_forecast = None
        self.__old_is_alarm_set = None

    @staticmethod
    def __get_digits(value, length, is_integer):
        res = []
        if is_integer:
            string_value = '{v:0>{l}d}'.format(v=value,l=length)
        else:
            string_value = '{v:*>{l}.1f}'.format(v=value,l=length+1)
        for c in string_value:
            if c != '.':
                if c == '*':
                    res.append(None)
                else:
                    res.append(int(c))
        return res[:length]
    def __refresh_temperature(self):
        res = False
        tmp = round(self.__bme280.temperature, 1)
        if tmp != self.__old_temperature:
            #draw new value
            digits = DisplayUpdater.__get_digits(tmp, 3, False)
            self.__draw_digit(self.__fonts[DisplayUpdater.__SENSOR_FONT1], (164, 2), 8, digits[0])
            self.__draw_digit(self.__fonts[DisplayUpdater.__SENSOR_FONT1], (180, 2), 8, digits[1])
            self.__draw_digit(self.__fonts[DisplayUpdater.__SENSOR_FONT2], (199,18), 8, digits[2])
            res = True
        self.__old_temperature = tmp
        return res
    def __refresh_humidity(self):
        res = False
        tmp = round(self.__bme280.humidity, 1)
        if tmp != self.__old_humidity:
            #draw new value
            digits = DisplayUpdater.__get_digits(tmp, 4, False)
            self.__draw_digit(self.__fonts[DisplayUpdater.__SENSOR_FONT1], (148,37), 1, digits[0])
            self.__draw_digit(self.__fonts[DisplayUpdater.__SENSOR_FONT1], (164,37), 8, digits[1])
            self.__draw_digit(self.__fonts[DisplayUpdater.__SENSOR_FONT1], (180,37), 8, digits[2])
            self.__draw_digit(self.__fonts[DisplayUpdater.__SENSOR_FONT2], (199,53), 8, digits[3])
            res = True
        self.__old_humidity = tmp
        return res
    def __refresh_pressure(self):
        res = False
        tmp = round(self.__bme280.pressure, 1)
        if tmp != self.__old_pressure:
            #draw new value
            digits = DisplayUpdater.__get_digits(tmp, 5, False)
            self.__draw_digit(self.__fonts[DisplayUpdater.__SENSOR_FONT1], (132,72), 1, digits[0])
            self.__draw_digit(self.__fonts[DisplayUpdater.__SENSOR_FONT1], (148,72), 8, digits[1])
            self.__draw_digit(self.__fonts[DisplayUpdater.__SENSOR_FONT1], (164,72), 8, digits[2])
            self.__draw_digit(self.__fonts[DisplayUpdater.__SENSOR_FONT1], (180,72), 8, digits[3])
            self.__draw_digit(self.__fonts[DisplayUpdater.__SENSOR_FONT2], (199,88), 8, digits[4])
            res = True
        self.__old_pressure = tmp
        return res
    def __refresh_time_date(self):
        res = False
        tmp = time.localtime(time.time())
        if tmp.tm_hour != getattr(self.__old_time_date, 'tm_hour', None):
            #draw new hour value
            h = DisplayUpdater.__get_digits(tmp.tm_hour, 2, True)
            self.__draw_digit(self.__fonts[DisplayUpdater.__TIME_FONT1], (72,19), 8, h[0])
            self.__draw_digit(self.__fonts[DisplayUpdater.__TIME_FONT1], (84,19), 8, h[1])
            res = True
        if tmp.tm_min != getattr(self.__old_time_date, 'tm_min', None):
            #draw new minute value
            m = DisplayUpdater.__get_digits(tmp.tm_min, 2, True)
            self.__draw_digit(self.__fonts[DisplayUpdater.__TIME_FONT1], (100,19), 8, m[0])
            self.__draw_digit(self.__fonts[DisplayUpdater.__TIME_FONT1], (112,19), 8, m[1])
            res = True
        if tmp.tm_sec != getattr(self.__old_time_date, 'tm_sec', None):
            #draw new second value
            s = DisplayUpdater.__get_digits(tmp.tm_sec, 2, True)
            self.__draw_digit(self.__fonts[DisplayUpdater.__TIME_FONT2], (126,37), 8, s[0])
            self.__draw_digit(self.__fonts[DisplayUpdater.__TIME_FONT2], (133,37), 8, s[1])
            res = True
        if tmp.tm_year != getattr(self.__old_time_date, 'tm_year', None):
            #draw new year value
            y = DisplayUpdater.__get_digits(tmp.tm_year, 4, True)
            self.__draw_digit(self.__fonts[DisplayUpdater.__DATE_FONT2], (105,86), 8, y[0])
            self.__draw_digit(self.__fonts[DisplayUpdater.__DATE_FONT2], (114,86), 8, y[1])
            self.__draw_digit(self.__fonts[DisplayUpdater.__DATE_FONT2], (123,86), 8, y[2])
            self.__draw_digit(self.__fonts[DisplayUpdater.__DATE_FONT2], (132,86), 8, y[3])
            res = True
        if tmp.tm_mon != getattr(self.__old_time_date, 'tm_mon', None):
            #draw new mounth value
            self.__draw_label(self.__fonts[DisplayUpdater.__MONTH_FONT], (41, 58), tmp.tm_mon)
            res = True
        if tmp.tm_mday != getattr(self.__old_time_date, 'tm_mday', None):
            #draw new day value
            d = DisplayUpdater.__get_digits(tmp.tm_mday, 2, True)
            self.__draw_digit(self.__fonts[DisplayUpdater.__DATE_FONT1], ( 1,60), 8, d[0])
            self.__draw_digit(self.__fonts[DisplayUpdater.__DATE_FONT1], (21,60), 8, d[1])
            res = True
        if tmp.tm_wday != getattr(self.__old_time_date, 'tm_wday', None):
            #draw new week day value
            self.__draw_label(self.__fonts[DisplayUpdater.__WEEK_DAY_FONT], (71, 0), tmp.tm_wday + 1)
            res = True
        self.__old_time_date = tmp
        return res
    def __refresh_sun_times(self):
        res = False
        #sunrise
        tmp_rise = self.__weather_info.sunrise_time
        if tmp_rise.tm_hour != getattr(self.__old_sunrise_time, 'tm_hour', None):
            #draw new hour value
            h = DisplayUpdater.__get_digits(tmp_rise.tm_hour, 2, True)
            self.__draw_digit(self.__fonts[DisplayUpdater.__TIME_FONT3], (48,96), 8, h[0])
            self.__draw_digit(self.__fonts[DisplayUpdater.__TIME_FONT3], (53,96), 8, h[1])
            res = True
        if tmp_rise.tm_min != getattr(self.__old_sunrise_time, 'tm_min', None):
            #draw new minute value
            m = DisplayUpdater.__get_digits(tmp_rise.tm_min, 2, True)
            self.__draw_digit(self.__fonts[DisplayUpdater.__TIME_FONT3], (60,96), 8, m[0])
            self.__draw_digit(self.__fonts[DisplayUpdater.__TIME_FONT3], (65,96), 8, m[1])
            res = True
        self.__old_sunrise_time = tmp_rise
        #sunset
        tmp_set = self.__weather_info.sunset_time
        if tmp_set.tm_hour != getattr(self.__old_sunset_time, 'tm_hour', None):
            #draw new hour value
            h = DisplayUpdater.__get_digits(tmp_set.tm_hour, 2, True)
            self.__draw_digit(self.__fonts[DisplayUpdater.__TIME_FONT3], (76,96), 8, h[0])
            self.__draw_digit(self.__fonts[DisplayUpdater.__TIME_FONT3], (81,96), 8, h[1])
            res = True
        if tmp_set.tm_min != getattr(self.__old_time_date, 'tm_min', None):
            #draw new minute value
            m = DisplayUpdater.__get_digits(tmp_set.tm_min, 2, True)
            self.__draw_digit(self.__fonts[DisplayUpdater.__TIME_FONT3], (88,96), 8, m[0])
            self.__draw_digit(self.__fonts[DisplayUpdater.__TIME_FONT3], (93,96), 8, m[1])
            res = True
        self.__old_sunset_time = tmp_set
        return res
    def __refresh_weather_icons(self):
        res = False
        #today forecast
        tmp_today = self.__weather_info.today_forecast
        if tmp_today != self.__old_today_forecast:
            #draw new icon
            if self.__weather_info.is_daytime:
                self.__draw_icon(self.__weather_icons_day[tmp_today]['draw'], (1,24))
            else:
                self.__draw_icon(self.__weather_icons_night[tmp_today]['draw'], (1,24))
            res = True
        self.__old_today_forecast = tmp_today
        #tomorrow forecast
        tmp_tomorrow = self.__weather_info.tomorrow_forecast
        if tmp_tomorrow != self.__old_tomorrow_forecast:
            #draw new icon
            self.__draw_icon(self.__weather_icons_day[tmp_tomorrow]['draw'], (37,24))
            res = True
        self.__old_tomorrow_forecast = tmp_tomorrow
        return res
    def __refresh_alarm_icon(self):
        res = False
        tmp = self.__audio_controller.is_alarm_set
        if tmp != self.__old_is_alarm_set:
            if tmp:
                self.__draw_icon(self.__alarm_icon['draw'], (126,21))
            else:
                self.__draw_icon(self.__alarm_icon['clear'], (126,21))
        self.__old_is_alarm_set = tmp
        return res
    def __draw_digit(self, font, position, clean_value, value):
        self.__screen_image.paste(font['clear'], position, font[clean_value])
        if value != None:
            self.__screen_image.paste(font['draw'], position, font[value])
    def __draw_label(self, font, position, value):
        self.__screen_image.paste(font['clear'], position)
        if value != None:
            self.__screen_image.paste(font['draw'], position, font[value])
    def __draw_icon(self, icon, position):
        self.__screen_image.paste(icon, position)
    def update(self):
        refresh_needed = False
        refresh_needed |= self.__refresh_temperature()
        refresh_needed |= self.__refresh_humidity()
        refresh_needed |= self.__refresh_pressure()
        refresh_needed |= self.__refresh_time_date()
        refresh_needed |= self.__refresh_sun_times()
        refresh_needed |= self.__refresh_weather_icons()
        refresh_needed |= self.__refresh_alarm_icon()
        if refresh_needed:
            self.__display.set_image(self.__screen_image)
            self.__display.show()
