import smbus2
import bme280
import time
import logging

class SensorUpdater:
    def __init__(self):
        super().__init__()
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
            self.__bme280.update_sensor()
        except Exception as ex:
            #some error occured, log the exception and keep trying
            self.__logger.error(ex)
    @property
    def bme280(self):
        return self.__bme280