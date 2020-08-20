#! /usr/bin/python3
from SensorUpdater import SensorUpdater
from DBWriter import DBWriter, ConnectionInfo
from HapPublisher import HapPublisher
import signal
import logging
import sys
import os
import time

#configure logging
log_file = sys.argv[0].replace('.py', '.log')
db_settings_file = os.path.join(os.path.dirname(sys.argv[0]), 'db_settings.json')
if '-d' in sys.argv:
    log_level = logging.DEBUG
else:
    log_level = logging.WARNING

logging.basicConfig(filename=log_file, level=log_level, format='%(asctime)s %(name)-16s %(levelname)-8s %(message)s')

#signal handler
def signal_handler(sig_num, stack_frame):
    if sig_num == signal.SIGINT or sig_num == signal.SIGTERM:
        updater.stop()
        writer.stop()
        hap_publisher.stop()

#register the signal handler for SIGINT and SIGTERM
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

#initialize treads
updater = SensorUpdater(2)
db_settings = ConnectionInfo.from_file(db_settings_file)
writer = DBWriter(db_settings, 5, updater.bme280)
hap_publisher = HapPublisher(updater.bme280)
    
#start threads
updater.start()
writer.start()
hap_publisher.start()

#wait for threads to exit
updater.join()
writer.join()

#thread per web radio