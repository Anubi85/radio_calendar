import threading
import falcon
import wsgiref.simple_server

class ApiManager(threading.Thread):
    def __init__(self, audio_controller):
        super().__init__()
        #initialize REST API
        api = falcon.API()
        api.add_route('/v1/radio/stations', audio_controller, suffix='stations')
        api.add_route('/v1/radio/stations/{id:int}', audio_controller, suffix='stations_id')
        api.add_route('/v1/radio/status', audio_controller, suffix='status')
        self.__server = wsgiref.simple_server.make_server('0.0.0.0', 8585, api)
    def run(self):
        self.__server.serve_forever()
    def stop(self):
        self.__server.shutdown()