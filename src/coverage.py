import math
import time
from typing import Dict, List, Tuple, Union

import shapely
from geopy.distance import geodesic
from pydantic import BaseModel
from shapely.geometry import Point, Polygon


class Demand(BaseModel):
    id: str
    polygon: List[Tuple[float, float]]


CoverageResult = Dict[
    int, Dict[str, Dict[str, Union[float, Polygon, Polygon]]]
]


def convert_polygon_to_list(polygon: shapely.Polygon) -> list[list[float]]:
    return [list(coord) for coord in polygon.exterior.coords]


def calculate_intersection(circle_polygon, demand_polygon):

    demand_polygon = Polygon(demand_polygon)
    circle_polygon = Polygon(circle_polygon)

    intersection = circle_polygon.intersection(demand_polygon)

    intersection_area = intersection.area
    total_polygon_area = demand_polygon.area
    percentage_intersection = (intersection_area / total_polygon_area) * 100.0
    leftover_polygon = demand_polygon.difference(circle_polygon)

    return (
        percentage_intersection,
        convert_polygon_to_list(intersection),
        convert_polygon_to_list(leftover_polygon),
    )


def get_coverage_of_flight(
    flight_path, demands: List[Demand], radius
) -> CoverageResult:

    start_time = time.time()

    result = {}

    for point, timestamp in flight_path:
        for demand in demands:
            circle_polygon = create_geodesic_circle(point[0], point[1], radius)
            coverage_percent, intersection, leftover = calculate_intersection(
                circle_polygon, demand.polygon
            )

            result.setdefault(timestamp, {})[demand.id] = {
                'coverage_percent': coverage_percent,
                'intersection': intersection,
                'leftover': leftover,
            }
    print(
        'got coverage of flight path in :--- %s seconds ---'
        % (time.time() - start_time)
    )
    return result


def add_distance_to_coordinates(old_lat, old_long, distance):
    # Earth's radius in meters
    R = 6371000

    # Convert distance to radians
    delta_lat = distance / (R * math.pi / 180)
    delta_long = distance / (
        R * math.cos(math.pi * old_lat / 180) * math.pi / 180
    )

    # Calculate new latitude and longitude
    new_lat = old_lat + delta_lat
    new_long = old_long + delta_long

    return new_lat, new_long


def create_geodesic_circle(center_lat, center_long, radius, num_points=50):
    circle_points = []

    for i in range(num_points):
        angle = 360 * i / num_points   # Azimuth
        point = geodesic(meters=radius).destination(
            (center_lat, center_long), angle
        )
        circle_points.append((point.latitude, point.longitude))

    return circle_points
