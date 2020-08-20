import pyhap.accessory as hap_accessory
import pyhap.accessory_driver as hap_accessory_driver
import pyhap.const as hap_const

class HapBME280(hap_accessory.Accessory):
    category = hap_const.CATEGORY_SENSOR
    def __init__(self, driver, bme280):
        super().__init__(driver, 'BME280')
        self.set_info_service(firmware_revision='1.0.0', manufacturer='Pimoroni', model='BME280', serial_number='A-0x76')
        self.__bme280 = bme280
        self.__temperature_service = self.add_preload_service('TemperatureSensor')
        self.__humidity_service = self.add_preload_service('HumiditySensor')
        self.__temperature_characteristic = self.__temperature_service.configure_char('CurrentTemperature')
        self.__humidity_characteristic = self.__humidity_service.configure_char('CurrentRelativeHumidity')

    @hap_accessory.Accessory.run_at_interval(5)
    async def run(self):
        self.__temperature_characteristic.set_value(self.__bme280.temperature)
        self.__humidity_characteristic.set_value(self.__bme280.humidity)

class HapPublisher(hap_accessory_driver.AccessoryDriver):
    def __init__(self, bme280):
        super().__init__()
        bridge = hap_accessory.Bridge(self, 'RadioAlarmClock')
        bridge.set_info_service(firmware_revision='1.0.0', manufacturer='Anubi', model='rpi-zw', serial_number=self.__get_pi_serial())
        bridge.add_accessory(HapBME280(self, bme280))
        self.add_accessory(bridge)

    @staticmethod
    def __get_pi_serial():
        cpuserial = "0000000000000000"
        try:
            f = open('/proc/cpuinfo','r')
            for line in f:
                if line[0:6]=='Serial':
                    cpuserial = line[10:26]
        except:
            cpuserial = "ERROR000000000"
        return cpuserial
