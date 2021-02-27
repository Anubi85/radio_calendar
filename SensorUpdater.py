import smbus2
import bme280
import time
import logging

class SensorUpdater:
    def __init__(self):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__i2c_bus = smbus2.SMBus(1)
        self.__bme280 = bme280.BME280(i2c_dev=self.__i2c_bus)
        #first time we need to update the sensor, wait a little bit and then update again
        #otherwise the sensor produces uncorrect values
        self.__bme280.update_sensor()
        time.sleep(0.1)
        self.__bme280.update_sensor()
    def update(self):
        try:
            self.__logger.debug('Updating BME280 data')
            self.__bme280.update_sensor()
        except Exception as ex:
            #some error occured, log the exception and keep trying
            self.__logger.error('Sensor update fail with error {0}'.format(ex))
    @property
    def bme280_temperature(self):
        #TODO: implementare compensazione
        return self.__bme280.temperature
    @property
    def bme280_humidity(self):
        #TODO: implementare compensazione
        return self.__bme280.humidity
    @property
    def bme280_pressure(self):
        return self.__bme280.pressure