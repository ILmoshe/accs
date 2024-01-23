import math
from functools import lru_cache
from math import acos, asin, atan2, cos, degrees, pi, radians, sin, sqrt

from geopy.distance import geodesic
from shapely.geometry import Polygon

from __init__ import Demand, Point, get_elevations


def calculate_azimuth(observer: Point, target: Point) -> float:
    # Calculate differences in latitude and longitude
    delta_lon = target.long - observer.long
    delta_lat = target.lat - observer.lat

    # Calculate azimuth angle
    azimuth = math.atan2(
        math.sin(math.radians(delta_lon)),
        math.cos(math.radians(observer.lat)) * math.tan(math.radians(target.lat))
        - math.sin(math.radians(observer.lat)) * math.cos(math.radians(delta_lon)),
    )

    # Convert azimuth angle from radians to degrees
    azimuth_degrees = math.degrees(azimuth)

    # Adjust azimuth to be in the range [0, 360)
    azimuth_degrees = (azimuth_degrees + 360) % 360

    return azimuth_degrees


def calculate_elevation(observer: Point, target: Point) -> float:
    """
    Not sure if it's working 100%
    :param observer:
    :param target:
    :return:
    """
    distance = geodesic((observer.lat, observer.long), (target.lat, target.long)).meters

    # Calculate elevation angle using Vincenty formulae
    delta_elevation = target.alt - observer.alt
    angle_radians = math.atan2(delta_elevation, distance)
    angle_degrees = math.degrees(angle_radians)

    return angle_degrees


def calculate_elevation_angle(observer: Point, target: Point) -> float:
    """
    Calculates the elevation angle between an observer and a target on Earth,
    considering its curvature.

    Args:
        observer: A tuple of (latitude, longitude, altitude) of the observer.
        target: A tuple of (latitude, longitude, altitude) of the target.

    Returns:
        The elevation angle in degrees between the observer and the target.
    """

    observer_lat, observer_lon, observer_alt = observer
    target_lat, target_lon, target_alt = target

    # Convert degrees to radians
    observer_lat = radians(observer_lat)
    observer_lon = radians(observer_lon)
    target_lat = radians(target_lat)
    target_lon = radians(target_lon)

    # Approximate Earth as a sphere
    R = 6371000  # Earth's mean radius in meters

    # Calculate horizontal distance using geodetic formula
    delta_lat = target_lat - observer_lat
    delta_lon = target_lon - observer_lon
    a = sin(delta_lat / 2) ** 2 + cos(observer_lat) * cos(target_lat) * sin(delta_lon / 2) ** 2
    c = 2 * asin(sqrt(a))
    horizontal_distance = R * c

    # Calculate vertical distance (altitude difference)
    vertical_distance = target_alt - observer_alt

    # Calculate elevation angle
    elevation_angle = degrees(atan2(vertical_distance, horizontal_distance))

    return elevation_angle


@lru_cache(maxsize=100)
def calculate_polygon_centroid(input_polygon: list[tuple[float, float]]) -> Point:
    polygon = Polygon(input_polygon)

    coordinates = list(polygon.exterior.coords)

    avg_x = sum(x for x, y in coordinates) / len(coordinates)
    avg_y = sum(y for x, y in coordinates) / len(coordinates)
    point_with_alt = get_elevations([Point(avg_x, avg_y)])[0]

    return point_with_alt


def is_in_range(value: float, value_range: dict) -> bool:
    return value_range["from"] <= value <= value_range["to"]


def calculate_demands_angels(point: Point | tuple[float, float], demands: list[Demand]):
    """

    :param point: point in time in the flight
    :param demands: array of demands to check against
    :return: dict of demand_id of elevation and azimuth, if invalid returns None
    """
    azimuth_full_range = {"from": 0, "to": 360}
    elevation_full_range = {"from": -90, "to": 90}

    result = {}

    for demand in demands:
        demand_center_point = calculate_polygon_centroid(demand.polygon)
        azimuth = calculate_azimuth(demand_center_point, point)
        elevation = calculate_elevation_angle(demand_center_point, point)

        result[demand.id] = {
            "azimuth": {
                "valid": azimuth if is_in_range(azimuth, demand.allowed_azimuth) else None,
                "available": azimuth,
            },
            "elevation": {
                "valid": elevation if is_in_range(elevation, demand.allowed_elevation) else None,
                "available": elevation,
            },
        }

    return result


# observer = Point(32.753066, 35.264912, 10000)
# target = Point(32.775584, 35.264397)

# azimuth = calculate_azimuth(observer, target)
# print(f"Azimuth from point_center to point_cypress: {azimuth} degrees")

# observer = Point(32.753066, 35.264912, 10000)
# target = Point(32.753066, 35.264912, 100)

# observer = Point(32.753066, 35.264912, 0)
# target = Point(49.234637, 12.747955, 10000)
# target = Point(43.866218, -107.116699, 0) # USA
# target = Point(33.555129, 35.480835, 0) # SEA
# elevation_angle = calculate_elevation_angle(observer, target)
# print(f"Elevation angle between observer and target: {elevation_angle} degrees")
