import math
import time

import shapely
from geopy.distance import geodesic
from shapely.geometry import Polygon

from . import CoverageResult, Demand, DemandCoverage


def convert_multipolygon_to_list(multipolygon: shapely.MultiPolygon):
    result = []
    for polygon in list(multipolygon.geoms):
        converted_polygon = convert_polygon_to_list(polygon)
        result.append(converted_polygon)
    return result


def convert_polygon_to_list(
    shape: shapely.Polygon | shapely.MultiPolygon,
) -> list[tuple[float, float]]:
    try:
        result = [tuple(coord) for coord in shape.exterior.coords]
    except AttributeError as AE:
        result = convert_multipolygon_to_list(shape)
    return result


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


# def calculate_intersection_raw


def calculate_intersection_raw(circle_polygon, demand_polygon) -> tuple[float, Polygon, Polygon]:
    demand_polygon = Polygon(demand_polygon)
    circle_polygon = Polygon(circle_polygon)

    intersection: Polygon = circle_polygon.intersection(demand_polygon)

    intersection_area = intersection.area
    total_polygon_area = demand_polygon.area
    percentage_intersection = (intersection_area / total_polygon_area) * 100.0
    leftover_polygon: Polygon = demand_polygon.difference(circle_polygon)

    return (
        percentage_intersection,
        intersection,
        leftover_polygon,
    )


def get_coverage_of_flight(
    flight_path: tuple[tuple[float, float], str], demands: list[Demand], radius
) -> CoverageResult:
    start_time = time.time()

    result: CoverageResult = {}

    for (
        point,
        timestamp,
    ) in flight_path:  # Its wrong, we need to iterate over the demands, its much more efficent
        for demand in demands:
            circle_polygon = create_geodesic_circle(point[0], point[1], radius)
            coverage_percent, intersection, leftover = calculate_intersection(circle_polygon, demand.polygon)

            result.setdefault(timestamp, {})[demand.id] = DemandCoverage(
                coverage_percent=coverage_percent,
                coverage_intersection=intersection,
                coverage_leftover=leftover,
            )

    print("got coverage of flight path in :--- %s seconds ---" % (time.time() - start_time))
    return result


def add_distance_to_coordinates(old_lat, old_long, distance):
    # Earth's radius in meters
    R = 6371000

    # Convert distance to radians
    delta_lat = distance / (R * math.pi / 180)
    delta_long = distance / (R * math.cos(math.pi * old_lat / 180) * math.pi / 180)

    # Calculate new latitude and longitude
    new_lat = old_lat + delta_lat
    new_long = old_long + delta_long

    return new_lat, new_long


def create_geodesic_circle(center_lat, center_long, radius, num_points=50):
    circle_points = []

    for i in range(num_points):
        angle = 360 * i / num_points  # Azimuth
        point = geodesic(meters=radius).destination((center_lat, center_long), angle)
        circle_points.append((point.latitude, point.longitude))

    return circle_points
