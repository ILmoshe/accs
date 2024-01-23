# Here we talk about the Gondola
# For the beginning we will take into account just the range
# The best resolution will be near it
from dataclasses import dataclass
from enum import Enum


class SensorType(Enum):
    EO = "EO"
    SAR = "SAR"
    IR = "IR"


@dataclass
class Gondola:
    GSD: float
    sensor_type: SensorType
    available_azimuth: ""
