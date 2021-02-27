#! /usr/bin/python3
from UpdateScheduler import UpdateScheduler
from SensorUpdater import SensorUpdater
from DatabaseUpdater import DatabaseUpdater
from HapPublisher import HapPublisher
from Radio import Radio
from RadioApiController import RadioApiController
from WeatherUpdater import WeatherUpdater
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
    log_level = logging.INFO

formatter = logging.Formatter('%(asctime)s %(name)-16s %(levelname)-8s %(message)s')
handler = logging.handlers.RotatingFileHandler(filename=log_file, maxBytes=2**22, backupCount=2)
handler.setFormatter(formatter)
handler.setLevel(log_level)
main_logger = logging.getLogger()
main_logger.addHandler(handler)

db = tinydb.TinyDB(db_file, indent=4)
main_logger.debug('Database initialized')

#signal handler
def signal_handler(sig_num, stack_frame):
    if sig_num == signal.SIGINT or sig_num == signal.SIGTERM:
        main_logger.info('Exiting application due to {0} event'.format(sig_num))
        hap_publisher.stop()
        api_manager.stop()
        update_scheduler.stop()

#register the signal handler for SIGINT and SIGTERM
signal.signal(signal.SIGINT, signal_handler)
main_logger.debug('Add handler for SIGINT event')
signal.signal(signal.SIGTERM, signal_handler)
main_logger.debug('Add handler for SIGTERM event')

try:
    main_logger.debug('Initializing components')
    #initialize radio instance
    radio = Radio(db.table('radio-stations'))
    main_logger.debug('Create {0} instance'.format(Radio.__name__))
    #initialize audio controller
    radio_api_controller = RadioApiController(radio)
    main_logger.debug('Create {0} instance'.format(RadioApiController.__name__))
    #initialize updaters
    sensor_updater = SensorUpdater()
    main_logger.debug('Create {0} instance'.format(SensorUpdater.__name__))
    database_updater = DatabaseUpdater(db.table('influxdb-connection').get(doc_id=1), sensor_updater)
    main_logger.debug('Create {0} instance'.format(DatabaseUpdater.__name__))
    weather_updater = WeatherUpdater(db.table('owm-info').get(doc_id=1))
    main_logger.debug('Create {0} instance'.format(WeatherUpdater.__name__))
    moon_updater = MoonUpdater()
    main_logger.debug('Create {0} instance'.format(MoonUpdater.__name__))
    gpio_updater = GpioUpdater()
    main_logger.debug('Create {0} instance'.format(GpioUpdater.__name__))
    display_updater = DisplayUpdater(db.table('display-resources').get(doc_id=1), sensor_updater, weather_updater, moon_updater, gpio_updater)
    main_logger.debug('Create {0} instance'.format(DisplayUpdater.__name__))
    #initialize other tasks
    update_scheduler = UpdateScheduler()
    main_logger.debug('Create {0} instance'.format(UpdateScheduler.__name__))
    update_scheduler.add_task(2, sensor_updater)
    update_scheduler.add_task(5, database_updater)
    update_scheduler.add_task(60 * 60 * 3, weather_updater) #3 hours
    update_scheduler.add_task(60 * 60 * 3, moon_updater) #3 hours
    update_scheduler.add_task(0.25, gpio_updater)
    update_scheduler.add_task(5 * 60, display_updater) #5 minutes
    main_logger.debug('Add tasks to task scheduler')
    #initialize homekit publisher
    hap_publisher = HapPublisher(sensor_updater)
    main_logger.debug('Create {0} instance'.format(HapPublisher.__name__))
    #initialize REST API server
    api_manager = ApiManager(radio_api_controller)
    main_logger.debug('Create {0} instance'.format(ApiManager.__name__))
    main_logger.debug('Components initialized')
except Exception as ex:
    main_logger.critical('Components initialization failed with error {0}'.format(ex))
    return
    
#start tasks
try:
    main_logger.info('Start serving requests')
    update_scheduler.start()
    api_manager.start()
    hap_publisher.start() #this call is blocking, must be last
    #wait for threads to exit
    api_manager.join()
    main_logger.info('Exit completed')
except Exception as ex:
    main_logger.critical('Unespected error {0}'.format(ex))