import pyhap.accessory as hap_accessory
import pyhap.accessory_driver as hap_accessory_driver
import pyhap.const as hap_const
import logging

class HapBME280(hap_accessory.Accessory):
    category = hap_const.CATEGORY_SENSOR
    def __init__(self, driver, sensor):
        super().__init__(driver, 'BME280')
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.set_info_service(firmware_revision='1.0.0', manufacturer='Pimoroni', model='BME280', serial_number='A-0x76')
        self.__sensor = sensor
        self.__temperature_service = self.add_preload_service('TemperatureSensor')
        self.__humidity_service = self.add_preload_service('HumiditySensor')
        self.__temperature_characteristic = self.__temperature_service.configure_char('CurrentTemperature')
        self.__humidity_characteristic = self.__humidity_service.configure_char('CurrentRelativeHumidity')

    @hap_accessory.Accessory.run_at_interval(5)
    async def run(self):
        try:
            self.__logger.debug('Updating BME280 data')
            self.__temperature_characteristic.set_value(self.__sensor.bme280_temperature)
            self.__humidity_characteristic.set_value(self.__sensor.bme280_humidity)
        except Exception as ex:
            self.__logger.error('Fail to update BME280 data with error {0}'.format(ex))

class HapPublisher(hap_accessory_driver.AccessoryDriver):
    def __init__(self, sensor):
        super().__init__()
        self.__logger = logging.getLogger(self.__class__.__class__)
        bridge = hap_accessory.Bridge(self, 'RadioAlarmClock')
        bridge.set_info_service(firmware_revision='1.0.0', manufacturer='Anubi', model='rpi-zw', serial_number=self.__get_pi_serial())
        bridge.add_accessory(HapBME280(self, sensor))
        self.add_accessory(bridge)

    def __get_pi_serial(self):
        cpuserial = "0000000000000000"
        try:
            f = open('/proc/cpuinfo','r')
            for line in f:
                if line[0:6]=='Serial':
                    cpuserial = line[10:26]
        except Exception as ex:
            self.__logger.error('Fail to retrieve CPU serial number with error {0}'.format(ex))
            cpuserial = "ERROR000000000"
        return cpuserial

    def start(self):
        self.__logger('Start serving Apple HomeKit requests')
        super().start()
    def stop(self):
        super().stop()
        self.__logger('Stop serving Apple HomeKit requests')
