import paho.mqtt.client as mqtt
import datetime
import json
import logging

class MqttUpdater:
    def __init__(self, connection_info, sensors):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__mqtt_client = None
        self.__mqtt_topic = connection_info['topic']
        self.__connect_to_mqtt_broker(connection_info['url'], connection_info['user'], connection_info['password'])
        self.__sensors = sensors

    def __connect_to_mqtt_broker(self, url, user, password):
        if self.__mqtt_client:
            self.__mqtt_client.unsubscribe(self.__mqtt_topic)
            self.__mqtt_client.disconnect()
        self.__mqtt_client = mqtt.Client('radio_calendar')
        self.__mqtt_client.enable_logger(self.__logger)
        self.__mqtt_client.username_pw_set(user, password)
        self.__mqtt_client.connect(url)
        if self.__mqtt_client.is_connected():
            self.__logger.info('Connected to MQTT broker ' + url)

    def update(self):
        self.__logger.debug('Publishing message to MQTT broker')
        payload = {}
        payload['temperature'] = self.__sensors.bme280_temperature
        payload['humidity'] = self.__sensors.bme280_humidity
        payload['pressure'] = self.__sensors.bme280_pressure
        if not self.__mqtt_client.is_connected():
            self.__logger.error('Lost connection MQTT broker. Try to reconnect')
            self.__mqtt_client.reconnect()
        self.__mqtt_client.publish(self.__mqtt_topic, json.dumps(payload))