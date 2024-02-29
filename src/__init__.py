import os.path
from typing import NamedTuple, TypedDict

import numpy as np
import requests
from pydantic import BaseModel, Field

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

