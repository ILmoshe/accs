import math
from math import asin, atan2, cos, degrees, radians, sin, sqrt

from src import Point


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
