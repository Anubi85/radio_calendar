import influxdb_client as influxdb2
import datetime
import json
import logging

class DatabaseUpdater:
    def __init__(self, connection_info, sensors):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__influx_db_client = influxdb2.InfluxDBClient(
            url=connection_info['url'],
            token=connection_info['token'],
            org='Anubi')
        write_opt = influxdb2.client.write_api.WriteOptions(batch_size=10)
        point_opt = influxdb2.client.write_api.PointSettings(**{'Device':'rpi-zw', 'Location':'Bedroom'})
        self.__db_writer = self.__influx_db_client.write_api(write_options=write_opt, point_settings=point_opt)
        self.__sensors = sensors
    def update(self):
        self.__logger.debug('Writing data to InfluxDB')
        p = influxdb2.Point('BME280') \
            .field('temperature', self.__sensors.bme280_temperature) \
            .field('humidity', self.__sensors.bme280_humidity) \
            .field('pressure', self.__sensors.bme280_pressure)
        self.__db_writer.write('sensors/monthly', record=[p])