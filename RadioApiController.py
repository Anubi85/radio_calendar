from Enums import StationTag
import falcon
import json
import logging

class RadioApiController:
    def __init__(self, radio):
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.__radio = radio
    
    def __error(self, error):
        self.__logger.error(error)
        return json.dumps({'error':error})
    def __warning(self, warning):
        self.__logger.warning(warning)
        return json.dumps({'warning':warning})
    def __get_int_parameter(self, params, par_name):
        par = params.get(par_name, None)
        if par:
            try:
                par = int(par)
            except:
                self.__logger.error('Parameter {0} is not an integer (value={1})'.format(par_name, par))
                par = None
        self.__logger.error('Parameter {0} not found'.format(par_name))
        return par
    def __parse_station_data(self, req):
        data = json.loads(req.stream.read(req.content_length))
        res = len(data) == len(StationTag)
        if not res:
            self.__logger.error('Unexpected data length, expected {0} fields, found {1}'.format(len(StationTag), len(data)))
        for tag in StationTag:
            if not (tag in data):
                res = False
                self.__logger.error('Tag {0} not found'.format(tag))
        return data if res else None
    
#/stations
    def on_get_stations(self, req, resp):
        self.__logger.debug('GET request on /stations endpoint received')
        stations = self.__radio.get_stations()
        resp.body = json.dumps(stations)
    def on_post_stations(self, req, resp):
        self.__logger.debug('POST request on /stations endpoint received')
        data = self.__parse_station_data(req)
        if data:
            #check if new position already exists
            pos = data[StationTag.Position]
            if not self.__radio.position_exists(pos):
                #everithing ok, return inserted data
                inserted = self.__radio.add_station(data)                
                resp.body = json.dumps(inserted)
                resp.status = falcon.HTTP_201
                self.__logger.debug('Station data {0} added to database'.format(resp.body))
            else:
                resp.body = self.__error('position {0} already exists'.format(data[StationTag.Position]))
                resp.status = falcon.HTTP_400
        else:
            resp.body = self.__error('malformed request content')
            resp.status = falcon.HTTP_400
#/stations/{pos:int}
    def on_get_stations_pos(self, req, resp, pos):
        self.__logger.debug('GET request on /stations/{pos:int} endpoint received')
        station = self.__radio.get_station(pos)
        if station:
            resp.body = json.dumps(station)
        else:
            resp.body = self.__error('position {0} not found'.format(pos))
            resp.status = falcon.HTTP_404
    def on_put_stations_pos(self, req, resp, pos):
        self.__logger.debug('PUT request on /stations/{pos:int} endpoint received')
        data = self.__parse_station_data(req)
        if data:
            #check if pos is valie
            if self.__radio.position_exists(pos):
                #check if new position exists
                new_pos = data[StationTag.Position]
                if pos == new_pos:
                    old_data = self.__radio.update_station(pos, data)
                    resp.body = json.dumps({'old':old_data,'new':data})
                    self.__logger.debug('station {0} updated with new data {1}'.format(pos, resp.body))
                    radio_update_required = self.__radio.is_playing() and \
                        self.__radio.is_current(new_pos) and \
                        (old_data[StationTag.StreamUrl] != data[StationTag.StreamUrl])
                    if radio_update_required:
                        self.__logger.debug('Restarting mpd due to station data update')
                        #update the playing url
                        self.__radio.stop()
                        self.__radio.play()
                else:
                    resp.body = self.__error('position cannot be changed')
                    resp.status = falcon.HTTP_400
            else:
                resp.body = self.__error('position {0} not found'.format(pos))
                resp.status = falcon.HTTP_404
        else:
            resp.body = self.__error('malformed request content')
            resp.status = falcon.HTTP_400
    def on_delete_stations_pos(self, req, resp, pos):
        self.__logger.debug('DEL request on /stations/{pos:int} endpoint received')
        if self.__radio.position_exists(pos):
            deleted = self.__radio.delete_station(pos)
            resp.body = json.dumps(deleted)
            if self.__radio.is_playing() and self.__radio.is_current(pos):
                self.__logger.debug('Stopping mpd due to station deletion')
                self.__radio.stop()
        else:
            resp.body = self.__error('position {0} not found'.format(pos))
            resp.status = falcon.HTTP_404
#/state
    def on_get_state(self, req, resp):
        self.__logger.debug('GET request on /state endpoint received')
        state = self.__radio.get_state()
        resp.body = json.dumps(state)
#/control/state/{cmd}
    def on_put_control_state(self, req, resp, cmd):
        self.__logger.debug('PUT request on /control/state/{0} endpoint received'.format(cmd))
        if cmd == 'play':
            self.__logger.debug('Start playing mpd')
            self.__radio.play()
        elif cmd == 'stop':
            self.__logger.debug('Stop playing mpd')
            self.__radio.stop()
        else:
            resp.body = self.__error('command {0} not supported'.format(cmd))
            resp.status = falcon.HTTP_400
#/control/station/{cmd}
    def on_post_control_station(self, req, resp, cmd):
        self.__logger.debug('POST request on /control/station/{0} endpoint received'.format(cmd))
        new_station = None
        if cmd == 'next':
            new_station = self.__radio.get_next_station()
        elif cmd == 'previous':
            new_station = self.__radio.get_prev_station()
        else:
            resp.body = self.__error('command {0} not supported'.format(cmd))
            resp.status = falcon.HTTP_400
            return
        if new_station:
            new_pos = new_station[StationTag.Position]
            self.__radio.set_current(new_pos)
            if self.__radio.is_playing():
                self.__logger.debug('Restarting mpd due to current station update')
                self.__radio.stop()
                self.__radio.play()
        else:
            resp.bidy = self.__warning('unable to find {0} station'.format(cmd))
    def on_put_control_station(self, req, resp, cmd):
        self.__logger.debug('PUT request on /control/station/{0} endpoint received'.format(cmd))
        PAR_NAME = 'station'
        pos = self.__get_int_parameter(req.params, PAR_NAME)
        if cmd == 'set' and pos:
            new_station = self.__radio.get_station(pos)
            if new_station:
                self.__radio.set_current(pos)
                if self.__radio.is_playing():
                    self.__logger.debug('Restarting mpd due to current station update')
                    self.__radio.stop()
                    self.__radio.play()
            else:
                resp.body = self.__error('position {0} not found'.format(pos))
                resp.state = falcon.HTTP_404 
        else:
            if pos:
                resp.body = self.__error('command {0} not supported'.format(cmd))
            elif PAR_NAME in req.params:
                resp.body = self.__error('expected an integer for {0} parameter'.format(PAR_NAME))
            else:
                resp.body = self.__error('{0} parameter is missing'.format(PAR_NAME))
            resp.status = falcon.HTTP_400
#/control/volume/{cmd}
    def on_post_control_volume(self, req, resp, cmd):
        self.__logger.debug('POST request on /control/volume/{0} endpoint received'.format(cmd))
        PARAM_NAME = 'delta'
        if PARAM_NAME in req.params:
            delta = self.__get_int_parameter(req.params, PARAM_NAME)
        else:
            delta = 5
            resp.body = self.__warning('{0} parameter is missing, default value (5) is assumed'.format(PARAM_NAME))
        if delta != None:
            if cmd == 'volume-up':
                self.__radio.change_volume(delta)
            elif cmd == 'volume-down':
                self.__radio.change_volume(-delta)
            else:
                resp.body = self.__error('command {0} not supported'.format(cmd))
        else:
            resp.body = self.__error('expected an integer for {0} parameter'.format(PARAM_NAME))
            resp.status = falcon.HTTP_400
    def on_put_control_volume(self, req, resp, cmd):
        self.__logger.debug('PUT request on /control/volume/{0} endpoint received'.format(cmd))
        PARAM_NAME = 'value'
        value = self.__get_int_parameter(req.params, PARAM_NAME)
        if cmd == 'set' and value:
            self.__radio.set_volume(value)
        else:
            if value:
                resp.body = self.__error('command {0} not supported'.format(cmd))
            elif PARAM_NAME in req.params:
                resp.body = self.__error('expected an integer for {0} parameter'.format(PARAM_NAME))
            else:
                resp.body = self.__error('{0} parameter is missing'.format(PARAM_NAME))
            resp.status == falcon.HTTP_400