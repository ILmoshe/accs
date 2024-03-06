import math
import os.path
from typing import Any, NamedTuple, Optional, TypedDict

import numpy as np
import requests
from geopy import distance
from pydantic import BaseModel, Field, model_validator
from shapely.geometry import Polygon
from typing_extensions import Self

from line_of_sight import get_fov_polygon

API_URL = "https://api.open-elevation.com/api/v1/lookup"


class Demand(BaseModel):
    id: str
    polygon: list[tuple[float, float]]
    allowed_azimuth: dict[str, float] = {"from": 0, "to": 360}
    allowed_elevation: dict[str, float] = {"from": -90, "to": 90}


class DemandCoverage(TypedDict):
    coverage_percent: float
    coverage_intersection: list[tuple[float, float]]
    coverage_leftover: list[tuple[float, float]]


CoverageResult = dict[str, dict[str, DemandCoverage]]


class Params(BaseModel):
    azimuth: float = Field(le=360, ge=0)
    elevation: float = Field(le=90, ge=-90)
    # coverage_percentage: float = Field(le=100, ge=0)
    # coverage_leftover: list[tuple[float, float]]


class Access(BaseModel):
    demand_id: str
    flight_id: str
    start: str
    end: str
    params: Params = None


class Point(NamedTuple):
    lat: float
    long: float
    alt: float = 0


class Sensor(BaseModel):
    name: str = "my_sensor"
    width_mm: float
    height_mm: float
    focal_length_mm: float
    image_width_px: int


def get_max_camera_capability(fov_polygon, focal_point: list[float, float, float]) -> float:
    curr_distance_in_meters = -1
    for point in fov_polygon:
        flat_distance = distance.distance(focal_point[:2], point).meters
        euclidian_distance = math.sqrt(flat_distance**2 + (focal_point[2] - 0) ** 2)
        curr_distance_in_meters = max(curr_distance_in_meters, euclidian_distance)
    return curr_distance_in_meters


def calculate_gsd_in_cm(sensor: Sensor, fov_polygon, focal_point):
    center = Polygon(fov_polygon).centroid  # here maybe call to get elevation
    centroid = Point(lat=center.x, long=center.y)
    [centroid] = get_altitude([centroid])
    flat_distance = distance.distance(focal_point[:2], [centroid.lat, centroid.long]).meters
    euclidian_distance = math.sqrt(flat_distance**2 + (focal_point[2] - centroid[2]) ** 2)

    GSD = (euclidian_distance * sensor.width_mm) / (sensor.focal_length_mm * sensor.image_width_px)
    return GSD * 100


class Flight(BaseModel):
    id: str = "flight_id"
    height_meters: float
    path_with_time: list[tuple[Any, str]]
    path_case: list[list]
    camera_azimuth: float
    camera_elevation: float
    sensor: Sensor

    camera_capability_meters: Optional[float] = None
    gsd: Optional[float] = None
    fov_polygon: Optional[list[list[float]]] = None

    @model_validator(mode="after")
    def add_relevant_fields(self) -> Self:
        focal_point = [*self.path_with_time[0][0], self.height_meters]
        fov_polygon = get_fov_polygon(self.sensor, [self.camera_azimuth, self.camera_elevation], focal_point)

        self.gsd = calculate_gsd_in_cm(self.sensor, fov_polygon, focal_point)
        self.camera_capability_meters = get_max_camera_capability(fov_polygon, focal_point)
        self.fov_polygon = fov_polygon

        return self


def get_elevations(points: list[Point]):
    locations_param = "|".join([f"{point.lat},{point.long}" for point in points])
    url = f"{API_URL}?locations={locations_param}"

    response = requests.get(url)

    if response.status_code == 200:
        elevation_data = response.json().get("results", [])
        result_points: list[Point] = [
            Point(
                data["latitude"],
                data["longitude"],
                data["elevation"],
            )
            for data in elevation_data
        ]
        return result_points
    else:
        print(f"Error: {response.status_code}, {response.text}")
        result_points: list[Point] = [
            Point(
                data.lat,
                data.long,
                alt=0,
            )
            for data in points
        ]
        return result_points


def read_hgt_file(filename):
    """
    Read elevation data from a .hgt file.
    """
    with open(filename, "rb") as f:
        elevation_data = np.fromfile(f, np.dtype(">i2"), -1).reshape((3601, 3601))
    return elevation_data


def get_elevation(lat, lon, elevation_data):
    """
    Get elevation at given latitude and longitude.
    """
    lat_row = int((1 - (lat - int(lat))) * 3600)
    lon_row = int((lon - int(lon)) * 3600)

    return elevation_data[lat_row, lon_row]


def get_altitude(points: list[Point], hgt_files_directory: str = "hgt") -> list[Point]:
    """
    Get altitude at given latitude and longitude using appropriate .hgt file.
    """
    loaded_hgt = {}
    elevation_result = []

    for point in points:
        lat, lon = point.lat, point.long
        hgt_file = f"{hgt_files_directory}/N{int(lat):02d}E{int(lon):03d}.hgt"
        if not os.path.isfile(hgt_file):
            elevation_result.append(0.0)
        if hgt_file in loaded_hgt:
            elevation_data = loaded_hgt[hgt_file]
        else:
            elevation_data = read_hgt_file(hgt_file)
            loaded_hgt[hgt_file] = elevation_data

        elevation_result.append(get_elevation(lat, lon, elevation_data))

    points_result = []
    for point, elevation in zip(points, elevation_result):
        points_result.append(Point(point.lat, point.long, elevation))

    return points_result
