import threading
import falcon
import wsgiref.simple_server
import logging

class ApiManager(threading.Thread):
    def __init__(self, audio_controller, update_scheduler_controller):
        super().__init__()
        self.__logger = logging.getLogger(self.__class__.__name__)
        #initialize REST API
        api = falcon.API()
        api.add_route('/v1/radio/stations', audio_controller, suffix='stations')
        api.add_route('/v1/radio/stations/{pos:int}', audio_controller, suffix='stations_pos')
        api.add_route('/v1/radio/state', audio_controller, suffix='state')
        api.add_route('/v1/radio/control/state/{cmd}', audio_controller, suffix='control_state')
        api.add_route('/v1/radio/control/station/{cmd}', audio_controller, suffix='control_station')
        api.add_route('/v1/radio/control/volume/{cmd}', audio_controller, suffix='control_volume')
        api.add_route('/v1/scheduler/diagnostic', update_scheduler_controller, suffix='diagnostic')
        self.__server = wsgiref.simple_server.make_server('0.0.0.0', 8585, api)
    def run(self):
        self.__logger.debug('Starting REST API server')
        self.__server.serve_forever()
    def stop(self):
        self.__server.shutdown()
        self.__logger.debug('REST API server stopped')