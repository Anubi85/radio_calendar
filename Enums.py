from enum import Enum

class StrEnum(str, Enum):
    def __new__(cls, value):
        return str.__new__(cls, value)

class StationTag(StrEnum):
    Position = 'position'
    DisplayName = 'display-name'
    StreamUrl = 'stream-url'
    Image = 'image'