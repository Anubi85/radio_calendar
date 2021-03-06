from inky import InkyPHAT
from PIL import Image
import time
import os
import logging
import gpiozero

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
    BATTERY_LOW = 'battery-low'
    BATTERY_FULL = 'battery-full'
    MAIN_LINE = 'main-line'
    def __init__(self, display_resources, sensors, weather_info, moon_info):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__resources = display_resources
        self.__sensors = sensors
        self.__weather_info = weather_info
        self.__moon_info = moon_info
        self.__display = InkyPHAT('yellow')
        self.__display.set_border(InkyPHAT.BLACK)
        self.__screen_image = Image.open(self.__resources['background'])
        self.__digit_fonts = {}
        for name, font in self.__resources['digit-fonts'].items():
            self.__digit_fonts[name] = Font(font)
        self.__labels = {}
        for name, label in self.__resources['labels'].items():
            self.__labels[name] = Font(label)
        self.__weather_icons_day = {}
        self.__weather_icons_night = {}
        for _, icon in self.__resources['weather-icons'].items():
            day = Icon(icon['day'])
            night = Icon(icon['night'])
            for code in icon['codes']:
                self.__weather_icons_day[code] = day
                self.__weather_icons_night[code] = night
        self.__moon_icons = {}
        for name, icon in self.__resources['moon-icons'].items():
            self.__moon_icons[name] = Icon(icon)
        self.__power_icons = {}
        for name, icon in self.__resources['power-icons'].items():
            self.__power_icons[name] = Icon(icon)
        self.__old_temperature = None
        self.__old_humidity = None
        self.__old_pressure = None
        self.__old_date = None
        self.__old_sunset_time = None
        self.__old_sunrise_time = None
        self.__old_today_forecast = None
        self.__old_tomorrow_forecast = None
        self.__old_is_daytime = None
        self.__old_next_moon_phase = None
        self.__old_next_moon_phase_date = None
        self.__old_uv_index = None
        #initialize gpio ofr power monitoring
        self.__main_line = gpiozero.Button(pin=5, pull_up=False)
        self.__main_line.when_activated = self.__on_power_state_changed
        self.__main_line.when_deactivated = self.__on_power_state_changed
        self.__battery_low = gpiozero.Button(pin=6, pull_up=False)
        self.__battery_low.when_activated = self.__on_power_state_changed
        self.__battery_low.when_deactivated = self.__on_power_state_changed
        #set default power icon icon (battery low)
        self.__power_state = None
        self.__on_power_state_changed()

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
        tmp = round(self.__sensors.bme280_temperature, 1)
        if tmp != self.__old_temperature:
            #draw new value
            digits = DisplayUpdater.__get_digits(tmp, 3, False)
            self.__draw_digit(self.__digit_fonts['large'], (164, 2), 8, digits[0])
            self.__draw_digit(self.__digit_fonts['large'], (180, 2), 8, digits[1])
            self.__draw_digit(self.__digit_fonts['small'], (199,18), 8, digits[2])
            res = True
            self.__logger.debug('Image update triggered by temperature change')
        self.__old_temperature = tmp
        return res
    def __refresh_humidity(self):
        res = False
        tmp = round(self.__sensors.bme280_humidity, 1)
        if tmp != self.__old_humidity:
            #draw new value
            digits = DisplayUpdater.__get_digits(tmp, 4, False)
            self.__draw_digit(self.__digit_fonts['large'], (148,37), 1, digits[0])
            self.__draw_digit(self.__digit_fonts['large'], (164,37), 8, digits[1])
            self.__draw_digit(self.__digit_fonts['large'], (180,37), 8, digits[2])
            self.__draw_digit(self.__digit_fonts['small'], (199,53), 8, digits[3])
            res = True
            self.__logger.debug('Image update triggered by humidity change')
        self.__old_humidity = tmp
        return res
    def __refresh_pressure(self):
        res = False
        tmp = round(self.__sensors.bme280_pressure, 1)
        if tmp != self.__old_pressure:
            #draw new value
            digits = DisplayUpdater.__get_digits(tmp, 5, False)
            self.__draw_digit(self.__digit_fonts['large'], (132,72), 1, digits[0])
            self.__draw_digit(self.__digit_fonts['large'], (148,72), 8, digits[1])
            self.__draw_digit(self.__digit_fonts['large'], (164,72), 8, digits[2])
            self.__draw_digit(self.__digit_fonts['large'], (180,72), 8, digits[3])
            self.__draw_digit(self.__digit_fonts['small'], (199,88), 8, digits[4])
            res = True
            self.__logger.debug('Image update triggered by pressure change')
        self.__old_pressure = tmp
        return res
    def __refresh_date(self):
        res = False
        tmp = time.localtime(time.time())
        if tmp.tm_year != getattr(self.__old_date, 'tm_year', None):
            #draw new year value
            y = DisplayUpdater.__get_digits(tmp.tm_year, 4, True)
            self.__draw_digit(self.__digit_fonts['small'], (105,18), 8, y[0])
            self.__draw_digit(self.__digit_fonts['small'], (114,18), 8, y[1])
            self.__draw_digit(self.__digit_fonts['small'], (123,18), 8, y[2])
            self.__draw_digit(self.__digit_fonts['small'], (132,18), 8, y[3])
            res = True
            self.__logger.debug('Image update triggered by year change')
        if tmp.tm_mon != getattr(self.__old_date, 'tm_mon', None):
            #draw new mounth value
            self.__draw_label(self.__labels['month'], (78, 2), tmp.tm_mon)
            res = True
            self.__logger.debug('Image update triggered by month change')
        if tmp.tm_mday != getattr(self.__old_date, 'tm_mday', None):
            #draw new day value
            d = DisplayUpdater.__get_digits(tmp.tm_mday, 2, True)
            self.__draw_digit(self.__digit_fonts['large'], (45,2), 8, d[0])
            self.__draw_digit(self.__digit_fonts['large'], (61,2), 8, d[1])
            #draw new week day value
            self.__draw_label(self.__labels['week'], (78, 21), tmp.tm_wday + 1)
            res = True
            self.__logger.debug('Image update triggered by day change')
        self.__old_time_date = tmp
        return res
    def __refresh_sun_times(self):
        res = False
        #sunrise
        if self.__weather_info.sunrise_time.hour != getattr(self.__old_sunrise_time, 'hour', None):
            #draw new hour value
            h = DisplayUpdater.__get_digits(self.__weather_info.sunrise_time.hour, 2, True)
            self.__draw_digit(self.__digit_fonts['small'], (59,45), 8, h[0])
            self.__draw_digit(self.__digit_fonts['small'], (68,45), 8, h[1])
            res = True
            self.__logger.debug('Image update triggered by sunrise hour change')
        if self.__weather_info.sunrise_time.minute != getattr(self.__old_sunrise_time, 'minute', None):
            #draw new minute value
            m = DisplayUpdater.__get_digits(self.__weather_info.sunrise_time.minute, 2, True)
            self.__draw_digit(self.__digit_fonts['small'], (79,45), 8, m[0])
            self.__draw_digit(self.__digit_fonts['small'], (88,45), 8, m[1])
            res = True
            self.__logger.debug('Image update triggered by sunrise minute change')
        self.__old_sunrise_time = self.__weather_info.sunrise_time
        #sunset
        if self.__weather_info.sunset_time.hour != getattr(self.__old_sunset_time, 'hour', None):
            #draw new hour value
            h = DisplayUpdater.__get_digits(self.__weather_info.sunset_time.hour, 2, True)
            self.__draw_digit(self.__digit_fonts['small'], (59,62), 8, h[0])
            self.__draw_digit(self.__digit_fonts['small'], (68,62), 8, h[1])
            res = True
            self.__logger.debug('Image update triggered by sunset hour change')
        if self.__weather_info.sunset_time.minute != getattr(self.__old_sunset_time, 'minute', None):
            #draw new minute value
            m = DisplayUpdater.__get_digits(self.__weather_info.sunset_time.minute, 2, True)
            self.__draw_digit(self.__digit_fonts['small'], (79,62), 8, m[0])
            self.__draw_digit(self.__digit_fonts['small'], (88,62), 8, m[1])
            res = True
            self.__logger.debug('Image update triggered by sunset minute change')
        self.__old_sunset_time = self.__weather_info.sunset_time
        return res
    def __refresh_weather_icons(self):
        res = False
        #today forecast
        if self.__weather_info.today_forecast != self.__old_today_forecast or \
            self.__weather_info.is_daytime != self.__old_is_daytime:
            #draw new icon
            if self.__weather_info.is_daytime:
                self.__draw_icon(self.__weather_icons_day[self.__weather_info.today_forecast]['draw'], (6,47))
            else:
                self.__draw_icon(self.__weather_icons_night[self.__weather_info.today_forecast]['draw'], (6,47))
            res = True
            self.__logger.debug('Image update triggered by today forecast change')
        self.__old_today_forecast = self.__weather_info.today_forecast
        #tomorrow forecast
        if self.__weather_info.tomorrow_forecast != self.__old_tomorrow_forecast or \
            self.__weather_info.is_daytime != self.__old_is_daytime:
            #draw new icon
            if self.__weather_info.is_daytime:
                self.__draw_icon(self.__weather_icons_day[self.__weather_info.tomorrow_forecast]['draw'], (106,47))
            else:
                self.__draw_icon(self.__weather_icons_night[self.__weather_info.tomorrow_forecast]['draw'], (106,47))
            res = True
            self.__logger.debug('Image update triggered by tomorrow forecast change')
        self.__old_tomorrow_forecast = self.__weather_info.tomorrow_forecast
        self.__old_is_daytime = self.__weather_info.is_daytime
        return res
    def __refresh_moon_phase(self):
        res = False
        if self.__moon_info.next_moon_phase != self.__old_next_moon_phase:
            self.__draw_icon(self.__moon_icons[self.__moon_info.next_moon_phase]['draw'], (38,83))
            res = True
            self.__logger.debug('Image update triggered by moon phase change')
        self.__old_next_moon_phase = self.__moon_info.next_moon_phase
        if self.__moon_info.next_moon_phase_date != self.__old_next_moon_phase_date:
            d = self.__get_digits(self.__moon_info.next_moon_phase_date.day, 2, True)
            self.__draw_digit(self.__digit_fonts['small'], (60,86), 8, d[0])
            self.__draw_digit(self.__digit_fonts['small'], (69,86), 8, d[1])
            self.__draw_label(self.__labels['month'], (79,86), self.__moon_info.next_moon_phase_date.month)
            res = True
            self.__logger.debug('Image update triggered by moon phase date change')
        self.__old_next_moon_phase_date = self.__moon_info.next_moon_phase_date
        return res
    def __refresh_uv_index(self):
        res = False
        if self.__weather_info.uv_index != self.__old_uv_index:
            idx = self.__get_digits(int(self.__weather_info.uv_index), 2, True)
            self.__draw_digit(self.__digit_fonts['small'], (18,86), 8, idx[0])
            self.__draw_digit(self.__digit_fonts['small'], (27,86), 8, idx[1])
            res = True
            self.__logger.debug('Image update triggered by uv index change')
        self.__old_uv_index = self.__weather_info.uv_index
        return res
    def __on_power_state_changed(self):
        main_line = self.__main_line.is_pressed
        battery_full = self.__battery_low.is_pressed
        self.__logger.debug('Power Source: {0}'.format('Main Line' if main_line else 'Battery'))
        self.__logger.debug('Battery State: {0}'.format('Full' if battery_full else 'Low'))
        if main_line:
            new_power_state = DisplayUpdater.MAIN_LINE
        elif battery_full:
            new_power_state = DisplayUpdater.BATTERY_FULL
        else:
            new_power_state = DisplayUpdater.BATTERY_LOW
        if new_power_state != self.__power_state:
            self.__logger.debug('Image update triggered by power state change')
            self.__power_state = new_power_state
            try:
                self.__draw_icon(self.__power_icons[self.__power_state]['draw'], (2,8))
                self.__refresh_display()
            except Exception as ex:
                self.__logger.error('Fail to update image due to a power state change with error {0}'.format(ex))
                self.__logger.exception(ex)
    def __draw_digit(self, font, position, clean_value, value):
        try:
            self.__screen_image.paste(font['clear'], position, font[clean_value])
            if value != None:
                self.__screen_image.paste(font['draw'], position, font[value])
        except Exception as ex:
            self.__logger.error('Fail to draw digit with error {0}'.format(ex))
            self.__logger.exception(ex)
    def __draw_label(self, font, position, value):
        try:
            self.__screen_image.paste(font['clear'], position)
            if value != None:
                self.__screen_image.paste(font['draw'], position, font[value])
        except Exception as ex:
            self.__logger.error('Fail to draw label with error {0}'.format(ex))
            self.__logger.exception(ex)
    def __draw_icon(self, icon, position):
        try: 
            self.__screen_image.paste(icon, position)
        except Exception as ex:
            self.__logger.error('Fail to draw icon with error {0}'.format(ex))
            self.__logger.exception(ex)
    def __refresh_display(self):
        try:
            self.__display.set_image(self.__screen_image)
            self.__display.show()
        except Exception as ex:
            self.__logger.error('Fail to refresh display with error {0}'.format(ex))
            self.__logger.exception(ex)
    def update(self):
        self.__logger.debug('Check for display image update')
        refresh_needed = False
        refresh_needed |= self.__refresh_temperature()
        refresh_needed |= self.__refresh_humidity()
        refresh_needed |= self.__refresh_pressure()
        refresh_needed |= self.__refresh_date()
        refresh_needed |= self.__refresh_sun_times()
        refresh_needed |= self.__refresh_weather_icons()
        refresh_needed |= self.__refresh_moon_phase()
        refresh_needed |= self.__refresh_uv_index()
        if refresh_needed:
            self.__logger.debug('Updating display image')
            self.__refresh_display()
        else:
            self.__logger.debug('Update not required for display image')
