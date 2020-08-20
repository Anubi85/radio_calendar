import threading
import influxdb_client as influxdb2
import datetime
import json

class ConnectionInfo():
    def __init__(self, url, user=None, password=None, token=None):
        self.__url = url
        self.__user = user
        self.__password = password
        if user and password:
            self.__token = f'{user}:{password}'
        elif token:
            self.__token = token
        else:
            raise ValueError('One of user and password or token must be provided')
    @property
    def url(self):
        return self.__url
    @property
    def user(self):
        return self.__user
    @property
    def password(self):
        return self.__password
    @property
    def token(self):
        return self.__token
    @staticmethod
    def from_file(file_name):
        with open(file_name) as f:
            data = json.load(f)
            return ConnectionInfo(
                data['url'], 
                data.get('user', None), 
                data.get('password', None), 
                data.get('token', None))
    def to_file(self, file_name):
        with open(file_name, 'w') as f:
            data = {
                'url':self.url,
                'user':self.user,
                'password':self.password,
                'token':self.token
            }
            json.dump(data, f, indent=4)

class DBWriter(threading.Thread):
    def __init__(self, connection_info, sample_time, bme280):
        super().__init__()
        self.__influx_db_client = influxdb2.InfluxDBClient(
            url=connection_info.url,
            token=connection_info.token,
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