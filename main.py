#! /usr/bin/python3
from SensorUpdater import SensorUpdater
from DBWriter import DBWriter
from HapPublisher import HapPublisher
from AudioController import AudioController
from WeatherUpdater import WetherUpdater
from DisplayUpdater import DisplayUpdater
import signal
import logging, logging.handlers
import sys
import os
import time
import tinydb

#configure logging
log_file = sys.argv[0].replace('.py', '.log')
db_file = os.path.join(os.path.dirname(sys.argv[0]), 'db.json')

if '-d' in sys.argv:
    log_level = logging.DEBUG
else:
    log_level = logging.WARNING

formatter = logging.Formatter('%(asctime)s %(name)-16s %(levelname)-8s %(message)s')
handler = logging.handlers.RotatingFileHandler(filename=log_file, maxBytes=2**22, backupCount=2)
handler.setFormatter(formatter)
handler.setLevel(log_level)
logging.getLogger().addHandler(handler)

db = tinydb.TinyDB(db_file, indent=4)

#signal handler
def signal_handler(sig_num, stack_frame):
    if sig_num == signal.SIGINT or sig_num == signal.SIGTERM:
        sensor_updater.stop()
        db_writer.stop()
        audio_controller.stop()
        hap_publisher.stop()
        weather_updater.stop()
        display_updater.stop()

#register the signal handler for SIGINT and SIGTERM
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

#initialize treads
sensor_updater = SensorUpdater(2)
db_writer = DBWriter(db.table('influxdb-connection').get(doc_id=1), 5, sensor_updater.bme280)
hap_publisher = HapPublisher(sensor_updater.bme280)
audio_controller = AudioController(db.table('radio-stations'), db.table('alarms'))
weather_updater = WetherUpdater(60 * 60 * 3) # 3 hours
display_updater = DisplayUpdater(0.25, db.table('display-resources').get(doc_id=1), sensor_updater.bme280, weather_updater, audio_controller)
    
#start threads
sensor_updater.start()
db_writer.start()
audio_controller.start()
hap_publisher.start()
weather_updater.start()
display_updater.start()

#wait for threads to exit
sensor_updater.join()
db_writer.join()
audio_controller.join()
weather_updater.join()
display_updater.join()