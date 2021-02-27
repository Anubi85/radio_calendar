from Enums import StationTag, StrEnum
import mpd
import tinydb

#TODO: implementare dummy per test
#TODO: loggare

class MpdStateTag(StrEnum):
    State = 'state'
    Volume = 'volume'
    Title = 'title'

class MpdCommand(StrEnum):
    Play = 'play'
    Stop = 'stop'
    ClearUrl = 'clear'
    AddUrl = 'add'
    Volume = 'volume'
    SetVolume = 'setvol'
    GetState = 'state'
    GetSongInfo = 'playlistid'

class Radio:
    def __init__(self, stations_db):
        self.__mpd_client = mpd.MPDClient()
        self.__stations_db = stations_db
        self.__current_pos = None

#mpc private methods
    def __exec_mpd_command(self, cmd, *cmd_args):
        return getattr(self.__mpd_client, cmd)(*cmd_args)
    def __exec_func(self, func, *func_args):
        try:
            self.__mpd_client.connect('/run/mpd/socket')
            return func(*func_args)
        except:
            return None
        finally:
            self.__mpd_client.disconnect()
    @staticmethod
    def __limit_value(value, min_value, max_value):
        return max(min_value, min(max_value, value))
    def __play(self, url):
        self.__exec_mpd_command(MpdCommand.Stop)
        self.__exec_mpd_command(MpdCommand.ClearUrl)
        self.__exec_mpd_command(MpdCommand.AddUrl, url)
        self.__exec_mpd_command(MpdCommand.Play)
    def __stop(self):
        self.__exec_mpd_command(MpdCommand.Stop)
        self.__exec_mpd_command(MpdCommand.ClearUrl)
    def __change_volume(self, delta):
        delta = Radio.__limit_value(delta, -100, 100)
        self.__exec_mpd_command(MpdCommand.AddUrl, delta)
    def __set_volume(self, volume):
        volume = Radio.__limit_value(volume, 0, 100)
        self.__exec_mpd_command(MpdCommand.SetVolume, volume)
    def __get_state(self):
        state = {}
        mpd_state = self.__exec_mpd_command(MpdCommand.GetState)
        state[MpdStateTag.State] = mpd_state.get('state', 'unknown')
        state[MpdStateTag.Volume] = mpd_state.get('volume', -1)
        song_id = mpd_state.get('songid', None)
        if song_id:
            song_info = self.__exec_mpd_command(MpdCommand.GetSongInfo, song_id)
            state[MpdStateTag.Title] = song_info.get('title', None)
        else:
            state[MpdStateTag.Title] = None
        return state
    def __is_playing(self):
        state = self.__exec_mpd_command(MpdCommand.GetState)
        return state.get('state', None) == 'play'

#mpc public methods
    def play(self):
        url = self.__get_current_station_url()
        if url:
            self.__exec_func(self.__play, url)
    def stop(self):
        self.__exec_func(self.__stop)
    def change_volume(self, delta):
        self.__exec_func(self.__change_volume, delta)
    def set_volume(self, volume):
        self.__exec_func(self.__set_volume)
    def get_state(self):
        mpc_state = self.__exec_func(self.__get_state)
        current_station = self.get_station(self.__current_pos)
        state = {}
        state['state'] = mpc_state[MpdStateTag.State]
        state['volume'] = mpc_state[MpdStateTag.Volume]
        station_info = {}
        station_info['position'] = current_station[StationTag.Position]
        station_info['name'] = current_station[StationTag.DisplayName]
        station_info['url'] = current_station[StationTag.StreamUrl]
        station_info['image'] = current_station[StationTag.Image]
        station_info['title'] = mpc_state[MpdStateTag.Title]
        state['station'] = station_info
        return state
    def is_current(self, pos):
        return self.__current_pos == pos
    def set_current(self, pos):
        self.__current_pos = pos
    def is_playing(self):
        return self.__exec_func(self.__is_playing)

#station database private methods
    def __get_station_filtered(self, pos, idx, filter_func):
        station = None
        if self.__has_stations() and self.position_exists(pos):
            stations = self.get_stations()
            station = stations[idx]
            filt_stations = list(filter(filter_func, stations))
            if filt_stations:
                station = filt_stations[idx]
        return station
    def __has_stations(self):
        return len(self.__stations_db) != 0
    def __get_current_station_url(self):
        if self.__current_pos:
            current_station = self.__stations_db.get(tinydb.where(StationTag.Position)==self.__current_pos)
            if current_station:
                return current_station[StationTag.StreamUrl]
        return None

#station database public methods
    def position_exists(self, pos):
        return self.__stations_db.get(tinydb.where(StationTag.Position)==pos) != None
    def get_stations(self):
        stations = self.__stations_db.all()
        stations.sort(key=lambda item: item[StationTag.Position])
        return stations
    def get_station(self, pos):
        return self.__stations_db.get(tinydb.where(StationTag.Position)==pos)
    def get_next_station(self, pos):
        filter_func = lambda item: item[StationTag.Position] > pos
        return self.__get_station_filtered(pos, 0, filter_func)
    def get_prev_station(self, pos):
        filter_func = lambda item: item[StationTag.Position] < pos
        return self.__get_station_filtered(pos, -1, filter_func)
    def add_station(self, data):
        id = self.__stations_db.insert(data)
        return self.__stations_db.get(doc_id=id)
    def update_station(self, pos, data):
        old_data = self.get_station(pos)
        id  = self.__stations_db.update(data, doc_ids=[old_data.doc_id])
        return self.__stations_db.get(doc_id=id)
    def delete_station(self, pos):
        old_data = self.get_station(pos)
        self.__stations_db.remove(doc_ids=[old_data.doc_id])
        return old_data