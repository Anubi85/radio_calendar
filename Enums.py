from enum import Enum

class StrEnum(Enum, str):
    def __new__(cls, value):
        return str.__new__(cls, value)

class Input(StrEnum):
    PowerState = 'power-state'
    Play = 'play-pressed'
    Stop = 'stop-pressed'
    Next = 'next-pressed'
    Prev = 'previous-pressed'
    VolUp = 'volume-up-pressed'
    VolDown = 'volume-down-pressed'

class StationTag(StrEnum):
    Position = 'position'
    DisplayName = 'display-name'
    StreamUrl = 'stream-url'
    Image = 'image'