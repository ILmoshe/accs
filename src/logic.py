import datetime
from copy import deepcopy

import numpy as np
from geopy.distance import geodesic
from shapely.geometry import Point, Polygon

from line_of_sight import get_fov_polygon
from line_of_sight.continues_fov import calc_continues_fov
from src import Demand, Flight, calculate_gsd_in_cm, get_altitude
from src.coverage import calculate_intersection_raw, convert_polygon_to_list


def get_intersectioncentroids(demand: Demand, intersection: Polygon):
    # Iterate over every area and see if the centroid of the area is inside the polygon
    intersection_centroids = []
    for centroid in demand.demand_inner_calculation.keys():
        if intersection.contains(Point(centroid[:2])):
            intersection_centroids.append(centroid)

    return intersection_centroids


def get_z_value_from_line(p1, p2, x, y):
    """
    Parameters:
        p1 (array_like): The first point (x1, y1, z1) defining the line.
        p2 (array_like): The second point (x2, y2, z2) defining the line.
        x (float): The x value for which to find the corresponding z value.
        y (float): The y value for which to find the corresponding z value.
    Returns:
        float: The z value corresponding to the given x and y on the line.
    """
    p1 = np.array(p1)
    p2 = np.array(p2)

    # Direction vector from p1 to p2
    d = p2 - p1

    # Handle cases where the line is parallel to one of the axes
    if d[0] == 0 and d[1] == 0:
        raise ValueError("The line is parallel to the z-axis; x and y values must match p1 or p2.")

    # Calculate parameter t
    t = np.where(d[0] != 0, (x - p1[0]) / d[0], (y - p1[1]) / d[1])

    # Calculate z using parameter t
    z = p1[2] + t * d[2]

    return z


def put_best_GSD_into_demand(
    demand: Demand, flight: Flight, point_with_alt: list[float], related_centroids: list
) -> None:
    for related_centroid in related_centroids:
        gsd = calculate_gsd_in_cm(flight.sensor, point_with_alt, related_centroid)
        if demand.demand_inner_calculation[related_centroid]["GSD"] > gsd:
            demand.demand_inner_calculation[related_centroid]["GSD"] = gsd


def put_LOS_into_demand(demand: Demand, point_with_alt: list[float], related_centroids: list) -> None:
    for related_centroid in related_centroids:
        if demand.demand_inner_calculation[related_centroid]["LOS"]:  # We already have LOS there
            continue

        points_on_line = points_along_line(
            point_with_alt[0],
            point_with_alt[1],
            related_centroid[0],
            related_centroid[1],
            350,
        )
        len_points_on_line = len(points_on_line)
        for index, point in enumerate(points_on_line, 1):
            equation_alt = get_z_value_from_line(point_with_alt, related_centroid, point[0], point[1])
            [real_point] = get_altitude([point])
            if real_point[2] > equation_alt:  # We don't have line of sight !
                break  # leave current centroid, unfortunately we didn't find

            if index == len_points_on_line:  # We checked all the way and we have LOS
                demand.demand_inner_calculation[related_centroid]["LOS"] = True


def calculate_arrival_time(flight: Flight, start_time_iso, target_point, margin_of_error=5):
    """
    Calculates the estimated arrival time at a specific point on a flight route.

    Args:
        polyline (list): A list of latitude/longitude tuples representing the flight path.
        start_time_iso (str): The starting time of the flight in ISO 8601 format (e.g., "2024-03-20T12:00:00Z").
        target_point (tuple): The latitude/longitude coordinates of the target point on the flight route.
        avg_speed (float, optional): The average speed of the aircraft in kilometers per hour. Defaults to 500.
        margin_of_error (float, optional): A margin of error (in minutes) to account for potential deviations. Defaults to 10.

    Returns:
        datetime.datetime: The estimated arrival time at the target point.

    Raises:
        ValueError: If the target point is not found on the polyline.
    """

    start_time = datetime.datetime.fromisoformat(start_time_iso)
    closest_segment_index = None
    closest_distance = float("inf")
    for i in range(len(flight.path_case) - 1):
        p1 = flight.path_case[i]
        p2 = flight.path_case[i + 1]
        distance = distance_to_segment(target_point, p1, p2)
        if distance < closest_distance:
            closest_segment_index = i
            closest_distance = distance

    if closest_segment_index is None:
        raise ValueError("Target point not found on the polyline")

    total_distance = 0
    for i in range(closest_segment_index + 1):
        total_distance += geodesic(flight.path_case[i], flight.path_case[i + 1]).km

    estimated_travel_time = total_distance / flight.speed_km_h

    estimated_arrival_time = start_time + datetime.timedelta(
        hours=estimated_travel_time, minutes=margin_of_error
    )

    return estimated_arrival_time


def distance_to_segment(point, p1, p2):
    """
    Calculates the distance from a point to a line segment.
    """

    u = ((point[0] - p1[0]) * (p2[0] - p1[0]) + (point[1] - p1[1]) * (p2[1] - p1[1])) / (
        (p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2
    )
    if u < 0 or u > 1:
        return min(geodesic(point, p1).km, geodesic(point, p2).km)
    x = p1[0] + u * (p2[0] - p1[0])
    y = p1[1] + u * (p2[1] - p1[1])
    return geodesic(point, (x, y)).km


def points_along_line(lat1, lon1, lat2, lon2, interval_distance):
    """
    Calculate points along the line connecting two points
    at specified intervals.
    """
    # Calculate total distance between two points in meters
    total_distance = geodesic((lat1, lon1), (lat2, lon2)).meters

    # Calculate the number of segments
    num_segments = int(total_distance / interval_distance)

    # Calculate the fraction to divide the latitude and longitude differences by
    lat_diff = lat2 - lat1
    lon_diff = lon2 - lon1
    lat_fraction = lat_diff / num_segments
    lon_fraction = lon_diff / num_segments

    # Generate points at specified intervals
    points = [(lat1 + i * lat_fraction, lon1 + i * lon_fraction) for i in range(num_segments)]
    points.insert(0, (lat1, lon1))
    points.insert(len(points) - 1, (lat2, lon2))
    return points


def create_case_for_flight_path(flight: Flight):
    casing = []
    for i in range(len(flight.path) - 1):
        first_point = flight.path[i]
        second_point = flight.path[i + 1]

        azimuth = flight.get_relative_azimuth_to_flight_direction(first_point, second_point)
        fov_polygon1 = get_fov_polygon(
            flight.sensor,
            [azimuth, flight.camera_elevation_start],
            [*first_point, flight.height_meters],
        )
        fov_polygon2 = get_fov_polygon(
            flight.sensor,
            [azimuth, flight.camera_elevation_start],
            [*second_point, flight.height_meters],
        )

        fov_polygon3 = get_fov_polygon(
            flight.sensor,
            [azimuth, flight.camera_elevation_end],
            [*first_point, flight.height_meters],
        )
        fov_polygon4 = get_fov_polygon(
            flight.sensor,
            [azimuth, flight.camera_elevation_end],
            [*second_point, flight.height_meters],
        )

        continues_fov = calc_continues_fov([fov_polygon1, fov_polygon2, fov_polygon3, fov_polygon4])
        casing.append(
            {
                "points": {f"{i}": first_point, f"{i + 1}": second_point},
                "case_polygon": continues_fov,
            }
        )

    return casing


def get_intersection_with_case(casing, demand: Demand):
    intersects_with_case = []
    for case in casing:
        _, intersection, _ = calculate_intersection_raw(case["case_polygon"], demand.polygon)
        if not intersection:
            continue
        intersects_with_case.append(case["points"])
    return intersects_with_case


def calculate_accesses_with_case_intersections(
    intersects_with_case,
    flight: Flight,
    demand: Demand,
    resolution_in_meters: int = 250,
):
    accesses_for_flight = []
    for intersection_line in intersects_with_case:
        point_A, point_B = list(intersection_line.values())
        index_A, index_B = list(intersection_line.keys())

        azimuth = flight.get_relative_azimuth_to_flight_direction(point_A, point_B)
        points = points_along_line(point_A[0], point_A[1], point_B[0], point_B[1], resolution_in_meters)
        accesses_for_line, LOS_GSD = calculate_accesses_along_points(points, flight, demand, azimuth)
        accesses_for_flight.append(
            {
                f"{index_A},{index_B}": accesses_for_line,
                "LOS_GSD": LOS_GSD,
                "flight_id": flight.id,
                "demand_id": demand.id,
            }
        )

    return accesses_for_flight


def calculate_accesses_along_points(
    points, flight: Flight, demand: Demand, azimuth, elevation_sampling_rate: int = 1
):
    accesses = []
    demand_gsd_and_los_init_val = deepcopy(demand.demand_inner_calculation)
    for index, point in enumerate(points):
        fov_polygon_start_elevation = get_fov_polygon(
            flight.sensor,
            [azimuth, flight.camera_elevation_start],
            [*point, flight.height_meters],
        )
        fov_polygon_end_elevation = get_fov_polygon(
            flight.sensor,
            [azimuth, flight.camera_elevation_end],
            [*point, flight.height_meters],
        )
        continues_fov = calc_continues_fov([fov_polygon_start_elevation, fov_polygon_end_elevation])

        coverage_percent, intersection, leftover = calculate_intersection_raw(continues_fov, demand.polygon)
        if not intersection:
            continue

        related_centroids = get_intersectioncentroids(demand, intersection)
        put_best_GSD_into_demand(demand, flight, [*point, flight.height_meters], related_centroids)
        put_LOS_into_demand(demand, [*point, flight.height_meters], related_centroids)

        current_access = {
            "point": point,
            "coverage_percent": coverage_percent,
            "intersection": convert_polygon_to_list(intersection),
            "leftover": convert_polygon_to_list(leftover),
        }
        if (
            not accesses or list(accesses[-1].keys())[-1] != index - 1
        ):  # Is it a separate access, check it by looking at the last index
            accesses.append({index: current_access})
        else:  # The access is a continues from the last one
            accesses[-1][index] = current_access

    demand_gsd_and_los = demand.demand_inner_calculation
    demand.demand_inner_calculation = demand_gsd_and_los_init_val
    return accesses, demand_gsd_and_los


def calculate_accesses_for_demand(flight: Flight, base_case, demand: Demand):
    demand_intersection_with_case = get_intersection_with_case(base_case, demand)
    accesses_for_demand = calculate_accesses_with_case_intersections(
        demand_intersection_with_case, flight, demand, resolution_in_meters=600
    )

    return accesses_for_demand
