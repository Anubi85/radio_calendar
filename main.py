#! /usr/bin/python3
from UpdateScheduler import UpdateScheduler
from SensorUpdater import SensorUpdater
from DatabaseUpdater import DatabaseUpdater
from HapPublisher import HapPublisher
from AudioController import AudioController
from WeatherUpdater import WetherUpdater
from MoonUpdater import MoonUpdater
from GpioUpdater import GpioUpdater
from DisplayUpdater import DisplayUpdater
from ApiManager import ApiManager
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
        hap_publisher.stop()
        api_manager.stop()
        update_scheduler.stop()

#register the signal handler for SIGINT and SIGTERM
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

#initialize audio controller
audio_controller = AudioController(db.table('radio-stations'))
#initialize updaters
sensor_updater = SensorUpdater()
database_updater = DatabaseUpdater(db.table('influxdb-connection').get(doc_id=1), sensor_updater.bme280)
weather_updater = WetherUpdater(db.table('owm-info').get(doc_id=1))
moon_updater = MoonUpdater()
gpio_updater = GpioUpdater()
display_updater = DisplayUpdater(db.table('display-resources').get(doc_id=1), sensor_updater.bme280, weather_updater, moon_updater, gpio_updater)
#initialize other tasks
update_scheduler = UpdateScheduler()
update_scheduler.add_task(2, sensor_updater)
update_scheduler.add_task(5, database_updater)
update_scheduler.add_task(60 * 60 * 3, weather_updater) #3 hours
update_scheduler.add_task(60 * 60 * 3, moon_updater) #3 hours
update_scheduler.add_task(0.25, gpio_updater)
update_scheduler.add_task(5 * 60, display_updater) #5 minutes
hap_publisher = HapPublisher(sensor_updater.bme280)
api_manager = ApiManager(audio_controller)
    
#start tasks
update_scheduler.start()
api_manager.start()
hap_publisher.start() #this call is blocking, must be last

#wait for threads to exit
api_manager.join()