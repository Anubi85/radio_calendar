#! /usr/bin/python3
from SensorUpdater import SensorUpdater
from DBWriter import DBWriter
from HapPublisher import HapPublisher
from AudioController import AudioController
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
        updater.stop()
        writer.stop()
        audio_controller.stop()
        hap_publisher.stop()

#register the signal handler for SIGINT and SIGTERM
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

#initialize treads
updater = SensorUpdater(2)
writer = DBWriter(db.table('influxdb-connection').get(doc_id=1), 5, updater.bme280)
hap_publisher = HapPublisher(updater.bme280)
audio_controller = AudioController(db.table('radio-stations'))
    
#start threads
updater.start()
writer.start()
audio_controller.start()
hap_publisher.start()

#wait for threads to exit
updater.join()
writer.join()
audio_controller.join()