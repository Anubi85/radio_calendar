import ephem
import logging

class MoonUpdater:
    NEW_MOON = 'new-moon'
    FIRST_QUARTER_MOON = 'first-quarter-moon'
    FULL_MOON = 'full-moon'
    LAST_QUARTER_MOON = 'last-quarter-moon'
    def __init__(self):
        self.__logger = logging.getLogger(self.__class__.__name__)
        #find current moon phase
        now = ephem.now()
        new_date = ephem.next_new_moon(now)
        first_quarter_date = ephem.next_first_quarter_moon(now)
        full_date = ephem.next_full_moon(now)
        last_quarter_date = ephem.next_last_quarter_moon(now)
        delta = float('inf')
        if new_date - now < delta:
            delta = new_date - now
            self.__current_phase = MoonUpdater.LAST_QUARTER_MOON
        if first_quarter_date - now < delta:
            delta = first_quarter_date - now
            self.__current_phase = MoonUpdater.NEW_MOON
        if full_date - now < delta:
            delta = full_date - now
            self.__current_phase = MoonUpdater.FIRST_QUARTER_MOON
        if last_quarter_date - now < delta:
            delta = last_quarter_date - now
            self.__current_phase = MoonUpdater.FULL_MOON
    def update(self):
        self.__logger.debug('Updating moon phase data')
        if ephem.now().datetime().date() >= self.next_moon_phase_date:
            self.__current_phase = self.next_moon_phase
    @property
    def next_moon_phase(self):
        if self.__current_phase == MoonUpdater.NEW_MOON:
            return MoonUpdater.FIRST_QUARTER_MOON
        elif self.__current_phase == MoonUpdater.FIRST_QUARTER_MOON:
            return MoonUpdater.FULL_MOON
        elif self.__current_phase == MoonUpdater.FULL_MOON:
            return MoonUpdater.LAST_QUARTER_MOON
        elif self.__current_phase == MoonUpdater.LAST_QUARTER_MOON:
            return MoonUpdater.NEW_MOON
    @property
    def next_moon_phase_date(self):
        if self.__current_phase == MoonUpdater.NEW_MOON:
            return ephem.next_first_quarter_moon(ephem.now()).datetime().date()
        elif self.__current_phase == MoonUpdater.FIRST_QUARTER_MOON:
            return ephem.next_full_moon(ephem.now()).datetime().date()
        elif self.__current_phase == MoonUpdater.FULL_MOON:
            return ephem.next_last_quarter_moon(ephem.now()).datetime().date()
        elif self.__current_phase == MoonUpdater.LAST_QUARTER_MOON:
            return ephem.next_new_moon(ephem.now()).datetime().date()
        