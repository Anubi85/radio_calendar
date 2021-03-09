import smbus2
import bme280
import time
import logging

class SensorUpdater:
    def __init__(self, compensation_data):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__i2c_bus = smbus2.SMBus(1)
        self.__bme280 = bme280.BME280(i2c_dev=self.__i2c_bus)
        self.__compensation_data = compensation_data
        self.__cpu_temperature_buffer = []
        self.__cpu_temperature = 0
        #first time we need to update the sensor, wait a little bit and then update again
        #otherwise the sensor produces uncorrect values
        self.__bme280.update_sensor()
        time.sleep(0.1)
        self.__bme280.update_sensor()
    def update(self):
        try:
            self.__logger.debug('Updating BME280 data')
            cpu_temp = self.__get_cpu_temperature()
            if cpu_temp:
                self.__cpu_temperature_buffer.append(cpu_temp)
            else:
                self.__logger.warning('CPU temperature not updated, keep using last value')
                self.__cpu_temperature_buffer.append(self.__cpu_temperature_buffer[-1])
            if len(self.__cpu_temperature_buffer) > 15:
                self.__cpu_temperature_buffer.pop(0)
                self.__cpu_temperature = sum(self.__cpu_temperature_buffer)/len(self.__cpu_temperature_buffer)
            self.__bme280.update_sensor()
        except Exception as ex:
            #some error occured, log the exception and keep trying
            self.__logger.error('Sensor update fail with error {0}'.format(ex))
            self.__logger.exception(ex)
    @property
    def bme280_temperature(self):
        if self.__cpu_temperature != 0:
            delta = self.__compute_compendation(self.__cpu_temperature, 'bme280', 'temperature')
            return self.__bme280.temperature + delta
        else:
            return self.__bme280.temperature
    @property
    def bme280_humidity(self):
        if self.__cpu_temperature != 0:
            delta = self.__compute_compendation(self.__cpu_temperature, 'bme280', 'humidity')
            return self.__bme280.humidity + delta
        else:
            return self.__bme280.humidity
    @property
    def bme280_pressure(self):
        return self.__bme280.pressure

    def __get_cpu_temperature(self):
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                return float(f.readline()) / 1000.0
        except Exception as ex:
            self.__logger.error('Fail to retrieve cpu temperature with error {0}'.format(ex))
            return None
    def __compute_compendation(self, x, sensor, measure):
        res = 0
        for deg, coef in enumerate(self.__compensation_data[sensor][measure]):
            res += coef * x**deg
        return res