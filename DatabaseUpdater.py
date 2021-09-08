import influxdb_client as influxdb2
import datetime
import json
import logging

class DatabaseUpdater:
    def __init__(self, connection_info, sensors):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__influx_db_client = None
        self.__db_writer = None
        self.__connect_to_db(connection_info['url'], connection_info['token'])
        self.__sensors = sensors

    def __connect_to_db(self, url, token):
        if self.__db_writer:
            self.__db_writer.close()
        if self.__influx_db_client:
            self.__influx_db_client.close()
        self.__influx_db_client = influxdb2.InfluxDBClient(
            url=url,
            token=token,
            org='Anubi')
        write_opt = influxdb2.client.write_api.WriteOptions(batch_size=10)
        point_opt = influxdb2.client.write_api.PointSettings(**{'Device':'rpi-zw', 'Location':'Bedroom'})
        self.__db_writer = self.__influx_db_client.write_api(write_options=write_opt, point_settings=point_opt)
        if self.__is_db_connected:
            self.__logger.info('Connected to database ' + url)

    @property
    def __is_db_connected(self):
        return self.__influx_db_client.health().status == 'pass'

    def update(self):
        self.__logger.debug('Writing data to InfluxDB')
        p = influxdb2.Point('BME280') \
            .field('temperature', self.__sensors.bme280_temperature) \
            .field('humidity', self.__sensors.bme280_humidity) \
            .field('pressure', self.__sensors.bme280_pressure)
        if not self.__is_db_connected:
            self.__logger.error('Lost connection with database. Try to reconnect')
            self.__connect_to_db(self.__influx_db_client.url, self.__influx_db_client.token)
        self.__db_writer.write('sensors/monthly', record=[p])