import threading
import smbus2
import bme280
import time
import logging

class SensorUpdater(threading.Thread):
    def __init__(self, sample_time):
        super().__init__()
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__i2c_bus = smbus2.SMBus(1)
        self.__bme280 = bme280.BME280(i2c_dev=self.__i2c_bus)
        #first time we need to update the sensor, wait a little bit and then update again
        #otherwise the sensor produces uncorrect values
        self.__bme280.update_sensor()
        time.sleep(0.1)
        self.__bme280.update_sensor()
        self.__sample_time = sample_time
        self.__stop = threading.Event()

    def run(self):
        while not self.__stop.is_set():
            try:
                self.__bme280.update_sensor()
                self.__stop.wait(self.__sample_time)
            except Exception as ex:
                #some error occured, log the exception and keep trying
                self.__logger.error(ex)
    def stop(self):
        self.__stop.set()
        self.__i2c_bus.close()

    @property
    def bme280(self):
        return self.__bme280