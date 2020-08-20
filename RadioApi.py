import falcon
import mpd
import tinydb
import wsgiref.simple_server
import threading
import json

class RadioApi(threading.Thread):
    def __init__(self, stations_db):
        super().__init__()
        api = falcon.API()
        self.__radio = Radio(stations_db)
        api.add_route('/v1/radio/stations', self.__radio, suffix='stations')
        api.add_route('/v1/radio/stations/{id:int}', self.__radio, suffix='stations_id')
        api.add_route('/v1/radio/status', self.__radio, suffix='status')
        self.__server = wsgiref.simple_server.make_server('0.0.0.0', 8585, api)

    def run(self):
        self.__server.serve_forever()

    def stop(self):
        self.__server.shutdown()

class Radio():
    def __init__(self, stations_db):
        self.__station_db = stations_db
        self.__current_station_id = None
        self.__mpc = mpd.MPDClient()
        #must add the volume command since it is not implemented
        def volume_callback(client, value):
            #we do not expect any results
            pass
        self.__mpc.add_command('volume', volume_callback)
        #reset the station list on mpd
        self.__exec_mpd_command('stop')
        self.__exec_mpd_command('clear')
    def __exec_mpd_command(self, cmd, *args):
        self.__mpc.connect('/run/mpd/socket')
        res = getattr(self.__mpc, cmd)(*args)
        self.__mpc.disconnect()
        return res
    #/stations/
    def on_get_stations(self, req, resp):
        stations = {item.doc_id:item for item in self.__station_db.all()}
        resp.body = json.dumps(stations)
    def on_post_stations(self, req, resp):
        data = json.loads(req.stream.read(req.content_length))
        try:
            station_info = RadioStationInfo(**data)
        except:
            resp.status = falcon.HTTP_400
            return
        #check if id and position are valid
        station = tinydb.Query()
        if self.__station_db.count(station.position == station_info.position):
            resp.status = falcon.HTTP_400
            return
        #everithing ok, add data to DB
        station_id = self.__station_db.insert(station_info.to_dict())
        resp.body = json.dumps({station_id:station_info.to_dict()})
    #/stations/id/
    def on_get_stations_id(self, req, resp, id):
        station_info = self.__station_db.get(doc_id=id)
        #check if requested station exists
        if station_info:
            resp.body = json.dumps(station_info)
        else:
            resp.status = falcon.HTTP_404
    def on_put_stations_id(self, req, resp, id):
        station = tinydb.Query()
        old_station_info = self.__station_db.get(doc_id=id)
        data = json.loads(req.stream.read(req.content_length))
        if old_station_info:
            try:
                new_station_info = data
            except:
                resp.status = falcon.HTTP_400
                return
            #check position
            if old_station_info['position'] != new_station_info['position'] and \
                self.__station_db.search(station.position == new_station_info['position']):
                resp.status = falcon.HTTP_400
                return
            self.__station_db.update(new_station_info, doc_ids=[id])
            resp.body = json.dumps(data)
        else:
            resp.status = falcon.HTTP_404
    def on_delete_stations_id(self, req, resp, id):
        if self.__current_station_id == id:
            self.__current_station_id = None
        station_info = self.__station_db.get(doc_id=id)
        if station_info:
            self.__station_db.remove(doc_ids=[id])
            resp.body = json.dumps(station_info)
        else:
            resp.status = falcon.HTTP_404
    #/status/
    def on_get_status(self, req, resp):
        state = {}
        tmp = self.__exec_mpd_command('status')
        state['radio-state'] = tmp['state']
        state['volume'] = tmp['volume']
        if self.__current_station_id:
            state['current-station'] = self.__station_db.get(doc_id=self.__current_station_id)
        else:
            state['current-station'] = None
        resp.body = json.dumps(state)
    def on_put_status(self, req, resp):
        data = json.loads(req.stream.read(req.content_length))
        target = data.get('target', None)
        cmd = data.get('command', None)
        params = data.get('parameters', None)
        if target == 'radio-status':
            self.__handle_radio_status_cmd(resp, cmd, params)
        elif target == 'current-station':
            self.__handle_current_station_cmd(resp, cmd, params)
        elif target == 'volume':
            self.__handle_volume_cmd(resp, cmd, params)
        else:
            resp.status = falcon.HTTP_400
    def __handle_radio_status_cmd(self, resp, cmd, params):
        if cmd == 'play':
            self.__exec_mpd_command('play')
        elif cmd == 'stop':
            self.__exec_mpd_command('stop')
        else:
            resp.status = falcon.HTTP_400
    def __handle_current_station_cmd(self, resp, cmd, params):
        if len(self.__station_db):
            stations = sorted(self.__station_db.all(), key=lambda item: item['position'])
            if cmd == 'next':
                new_station = stations[0]
                if self.__current_station_id:
                    current_pos = self.__station_db.get(doc_id=self.__current_station_id)['position']
                    next_stations = list(filter(lambda s: s['position'] > current_pos, stations))
                    if next_stations:
                        new_station = next_stations[0]
            elif cmd == 'prev':
                new_station = stations[-1]
                if self.__current_station_id:
                    current_pos = self.__station_db.get(doc_id=self.__current_station_id)['position']
                    prev_stations = list(filter(lambda s: s['position'] < current_pos, stations))
                    if prev_stations:
                        new_station = prev_stations[-1]
            elif cmd == 'set':
                try:
                    requested_pos = int(params)
                except:
                    resp.status = falcon.HTTP_400
                    return
                new_station = self.__station_db.get(tinydb.where('position') == requested_pos)
            else:
                resp.status = falcon.HTTP_400
                return
            if new_station:
                self.__current_station_id = new_station.doc_id
                self.__exec_mpd_command('clear')
                self.__exec_mpd_command('add', new_station['stream-url'])
            else:
                resp.status = falcon.HTTP_404
        else:
            resp.status = falcon.HTTP_404
    def __handle_volume_cmd(self, resp, cmd, params):
        if cmd == 'up':
            try:
                val = int(params)
            except:
                val = 1
            self.__exec_mpd_command('volume', max(-100, min(val, 100)))
        elif cmd == 'down':
            try:
                val = int(params)
            except:
                val = 1
            self.__exec_mpd_command('volume', max(-100, min(-val, 100)))
        elif cmd == 'set':
            try:
                val = int(params)
            except:
                val = 50
            self.__exec_mpd_command('setvol', max(0, min(val, 100)))
        else:
            resp.status = falcon.HTTP_400