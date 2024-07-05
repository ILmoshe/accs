import math
import os.path
from collections import OrderedDict
from typing import Any, NamedTuple, Optional, Sequence, TypedDict

import numpy as np
import requests
from geopy import distance
from loguru import logger
from pydantic import BaseModel, Field, model_validator
from shapely.geometry import Polygon, box
from typing_extensions import Self

from line_of_sight import get_fov_polygon

API_URL = "https://api.open-elevation.com/api/v1/lookup"


def create_grid_polygons(polygon: Polygon | Any, cell_size: float):
    polygon = Polygon(polygon)

    minx, miny, maxx, maxy = polygon.bounds
    grid_polygons = {}

    for x in np.arange(minx, maxx, cell_size):
        for y in np.arange(miny, maxy, cell_size):
            # Define the current cell as a polygon (box)
            cell = box(x, y, x + cell_size, y + cell_size)

            if cell.intersects(polygon):
                # Clip the cell to the input polygon (to handle partial overlaps)
                clipped_cell: Polygon = cell.intersection(polygon)
                lat = clipped_cell.centroid.x
                long = clipped_cell.centroid.y
                [point_with_alt] = get_altitude([Point(lat, long)])
                p_x, p_y, p_z = (
                    point_with_alt.lat,
                    point_with_alt.long,
                    point_with_alt.alt,
                )
                grid_polygons[p_x, p_y, p_z] = {
                    "area": clipped_cell,
                    "GSD": float("inf"),
                    "LOS": False,
                }

    return grid_polygons


class Demand(BaseModel):
    id: str
    polygon: list[tuple[float, float]]
    allowed_azimuth: dict[str, float] = {"from": 0, "to": 360}
    allowed_elevation: dict[str, float] = {"from": -90, "to": 90}

    demand_inner_calculation: Optional[dict[str, dict[str, Any | float | bool]]] = None

    @model_validator(mode="after")
    def prepare_demand(self) -> Self:
        self.demand_inner_calculation = create_grid_polygons(
            self.polygon, 0.015
        )  # we will have to see which size is the appropriate cell size
        return self


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

    def __str__(self):
        return f"{self.lat, self.long, self.alt}"


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


def calculate_gsd_in_cm(sensor: Sensor, focal_point: Sequence[float], point_in_surface: Sequence[float]):
    flat_distance = distance.distance(focal_point[:2], point_in_surface[:2]).meters
    euclidian_distance = math.sqrt(flat_distance**2 + (focal_point[2] - point_in_surface[2]) ** 2)

    GSD = (euclidian_distance * sensor.width_mm) / (sensor.focal_length_mm * sensor.image_width_px)
    return GSD * 100


class Flight(BaseModel):
    id: str = "flight_id"
    height_meters: float
    speed_km_h: float
    path_case: list[list]
    path: list[list]
    camera_azimuth: float
    camera_elevation_start: int
    camera_elevation_end: int
    sensor: Sensor

    # Field which are added with computation
    camera_capability_meters: Optional[float] = None
    gsd: Optional[float] = None
    fov_polygon: Optional[list[list[float]]] = None

    def get_relative_azimuth_to_flight_direction(
        self, p1: tuple[float] | list, p2: tuple[float] | list
    ) -> float:
        from src.angels import calculate_azimuth  # TODO: prevent circular imports

        p1 = Point(lat=p1[0], long=p1[1])
        p2 = Point(lat=p2[0], long=p2[1])
        direction_azimuth = calculate_azimuth(p1, p2)
        relative_azimuth = self.camera_azimuth - direction_azimuth
        relative_azimuth %= 360
        return relative_azimuth

    @model_validator(mode="after")
    def add_relevant_fields(self) -> Self:
        # Norm fields
        self.camera_azimuth = self.camera_azimuth - (self.camera_azimuth * 2)
        self.camera_elevation_start = self.camera_elevation_start - (self.camera_elevation_start * 2)
        self.camera_elevation_end = self.camera_elevation_end - (self.camera_elevation_end * 2)

        focal_point = [*self.path[0], self.height_meters]
        fov_polygon = get_fov_polygon(
            self.sensor, [self.camera_azimuth, self.camera_elevation_start], focal_point
        )
        # self.gsd = calculate_gsd_in_cm(self.sensor, fov_polygon, focal_point)
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


class LRUCache:
    def __init__(self, capacity: int = 10):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key):
        if key not in self.cache:
            return None
        else:
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)


def read_hgt_file(filename):
    logger.info(f"hgt file name {filename}")
    with open(filename, "rb") as f:
        elevation_data = np.fromfile(f, np.dtype(">i2"), -1).reshape((3601, 3601))
    return elevation_data


def get_elevation(lat, lon, elevation_data):
    lat_row = int((1 - (lat - int(lat))) * 3600)
    lon_row = int((lon - int(lon)) * 3600)
    return elevation_data[lat_row, lon_row]


def get_altitude(points, hgt_files_directory="hgt"):
    loaded_hgt = LRUCache(capacity=20)  # Adjust capacity as needed
    elevation_result = []

    for point in points:
        try:
            lat, lon = point.lat, point.long
        except AttributeError:
            lat, lon = (point[0], point[1])
        hgt_file = f"{hgt_files_directory}/N{int(lat):02d}E{int(lon):03d}.hgt"
        if not os.path.isfile(hgt_file):
            elevation_result.append(0.0)
            continue
        elevation_data = loaded_hgt.get(hgt_file)
        if elevation_data is None:
            elevation_data = read_hgt_file(hgt_file)
            loaded_hgt.put(hgt_file, elevation_data)

        elevation_result.append(get_elevation(lat, lon, elevation_data))

    points_result = []
    for point, elevation in zip(points, elevation_result):
        try:
            points_result.append(Point(point.lat, point.long, elevation))
        except AttributeError:
            points_result.append([point[0], point[1], elevation])

    return points_result
