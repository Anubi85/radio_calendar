import threading
import influxdb_client as influxdb2
import datetime
import json

class DBWriter(threading.Thread):
    def __init__(self, connection_info, sample_time, bme280):
        super().__init__()
        self.__influx_db_client = influxdb2.InfluxDBClient(
            url=connection_info['url'],
            token=connection_info['token'],
            org='Anubi')
        write_opt = influxdb2.client.write_api.WriteOptions(batch_size=10)
        point_opt = influxdb2.client.write_api.PointSettings(**{'Device':'rpi-zw', 'Location':'Bedroom'})
        self.__db_writer = self.__influx_db_client.write_api(write_options=write_opt, point_settings=point_opt)
        self.__bme280 = bme280
        self.__sample_time = sample_time
        self.__stop = threading.Event()

    def run(self):
        while not self.__stop.is_set():
            p = influxdb2.Point('BME280') \
                .field('temperature', self.__bme280.temperature) \
                .field('humidity', self.__bme280.humidity) \
                .field('pressure', self.__bme280.pressure)
            self.__db_writer.write('sensors/monthly', record=[p])
            self.__stop.wait(self.__sample_time)

    def stop(self):
        self.__stop.set()
        self.__influx_db_client.close()