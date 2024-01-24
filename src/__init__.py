from typing import NamedTuple, TypedDict

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
        return None
