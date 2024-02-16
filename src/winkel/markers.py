import enum


class Marker(int, enum.Enum):
    null = 1
    drop = 2
    required = 3
    missing = 4
