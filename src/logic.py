import datetime
import math
import time
from copy import deepcopy

import numpy as np
from geopy.distance import distance, geodesic
from shapely.geometry import LineString, Point, Polygon

from const import CAMERA_MAX_DISTANCE, INTERVAL_SAMPLE
from line_of_sight import get_fov_polygon
from line_of_sight.create_polygon import calc_continues_fov
from src import Demand, Flight
from src import Point as _Point
from src import calculate_gsd_in_cm, get_altitude
from src.angels import calculate_azimuth, calculate_elevation_angle, is_in_range
from src.coverage import (
    calculate_intersection,
    calculate_intersection_raw,
    convert_polygon_to_list,
    create_geodesic_circle,
)


def get_intersectioncentroids(demand: Demand, intersection: Polygon):
    # Iterate over every area and see if the centroid of the area is inside the polygon
    intersection_centroids = []
    for centeroid in demand.demand_inner_calculation.keys():
        if intersection.contains(Point(centeroid[:2])):
            intersection_centroids.append(centeroid)

    return intersection_centroids


def get_z_value_from_line(p1, p2, x, y):
    """
    Calculates the z value on the line defined by two points in 3D space for given x and y,
    using NumPy for improved performance.

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
    """

    :param flight:
    :param demand:
    :param point_with_alt:
    :param related_centroids:
    :return:
    """
    for related_centroid in related_centroids:
        gsd = calculate_gsd_in_cm(flight.sensor, point_with_alt, related_centroid)
        if demand.demand_inner_calculation[related_centroid]["GSD"] > gsd:
            demand.demand_inner_calculation[related_centroid]["GSD"] = gsd


def put_LOS_into_demand(demand: Demand, point_with_alt: list[float], related_centroids: list) -> None:
    for related_centroid in related_centroids:
        if demand.demand_inner_calculation[related_centroid]["LOS"]:  # We already have LOS there
            continue

        points_on_line = points_along_line(
            point_with_alt[0], point_with_alt[1], related_centroid[0], related_centroid[1], 200
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

    return points


# 1. Create Casing:
def create_case_for_flight_path(flight: Flight):
    casing = []
    for i in range(len(flight.path) - 1):
        first_point = flight.path[i]
        second_point = flight.path[i + 1]

        azimuth = flight.get_relative_azimuth_to_flight_direction(first_point, second_point)
        fov_polygon1 = get_fov_polygon(
            flight.sensor, [azimuth, flight.camera_elevation_start], [*first_point, flight.height_meters]
        )
        fov_polygon2 = get_fov_polygon(
            flight.sensor, [azimuth, flight.camera_elevation_start], [*second_point, flight.height_meters]
        )

        fov_polygon3 = get_fov_polygon(
            flight.sensor, [azimuth, flight.camera_elevation_end], [*first_point, flight.height_meters]
        )
        fov_polygon4 = get_fov_polygon(
            flight.sensor, [azimuth, flight.camera_elevation_end], [*second_point, flight.height_meters]
        )

        continues_fov = calc_continues_fov([fov_polygon1, fov_polygon2, fov_polygon3, fov_polygon4])
        casing.append(
            {"points": {f"{i}": first_point, f"{i + 1}": second_point}, "case_polygon": continues_fov}
        )

    return casing


# 2. for each case see if it intersects:
def get_intersection_with_case(casing, demand: Demand):
    intersects_with_case = []
    for case in casing:
        _, intersection, _ = calculate_intersection_raw(case["case_polygon"], demand.polygon)
        if not intersection:
            continue
        intersects_with_case.append(case["points"])
    return intersects_with_case


# 3. for each intersection we found:
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
        # TODO: we some how need to keep track of the best gsd for a given area
        fov_polygon_start_elevation = get_fov_polygon(
            flight.sensor, [azimuth, flight.camera_elevation_start], [*point, flight.height_meters]
        )
        fov_polygon_end_elevation = get_fov_polygon(
            flight.sensor, [azimuth, flight.camera_elevation_end], [*point, flight.height_meters]
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


def add_meters_to_coordinates(coordinates, distance_in_meters, azimuth_to_north: int = 90):
    lat, lon, alt = coordinates
    destination_point = geodesic(meters=distance_in_meters).destination(point=(lat, lon), bearing=0)

    return destination_point.latitude, destination_point.longitude


def create_casing(polyline, distance_meters: float):
    """
    :param polyline: List of (lon, lat) points representing the polyline
    :param distance_meters: Desired distance in kilometers for the casing
    :return: List of casing points (lon, lat)
    """
    line = LineString(polyline)

    # Calculate the approximate conversion from kilometers to degrees for buffer distance
    centroid_lat = line.centroid.y
    buffer_distance_degrees = (
        geodesic(kilometers=distance_meters // 1000).destination((centroid_lat, 0), 90).longitude
    )

    # Create buffer polygon using Shapely
    buffered_line = line.buffer(buffer_distance_degrees, join_style=2)

    if buffered_line.is_empty:
        return None

    casing_points = [list(coord) for coord in buffered_line.exterior.coords]

    return casing_points


def filter_appropriate_points(flight, target_point, distance_in_m=CAMERA_MAX_DISTANCE):
    flight_indexes = set()
    for index, point in enumerate(flight):
        flat_distance = distance(target_point[:2], point[0][:2]).meters
        euclidian_distance = math.sqrt(flat_distance**2 + (target_point[2] - 0) ** 2)
        THRESHOLD = 1500  # some const threshold, not sure if needed
        if euclidian_distance - THRESHOLD <= distance_in_m:
            flight_indexes.add(index)

    return flight_indexes


def calc_access_for_demand1(flight: Flight, demand: Demand):
    _, casing_intersection, _ = calculate_intersection_raw(flight.path_case, demand.polygon)

    if not casing_intersection:
        return

    traveled_indexes = set()
    coverage_result = {}  # the key is the index

    for point in casing_intersection.exterior.coords:
        point_with_alt = [*point, flight.height_meters]
        indexes = filter_appropriate_points(flight.path_with_time, point_with_alt)
        for index in indexes:
            if index in traveled_indexes:
                continue
            traveled_indexes.add(index)
            relevant_flight_point = flight.path_with_time[index][0]
            coverage_percent, intersection, leftover = get_intersection(
                relevant_flight_point, demand.polygon
            )  # TODO: Change radius later
            if not intersection:
                continue
            coverage_result[str(index)] = {
                "coverage": {
                    "coverage_percent": coverage_percent,
                    "intersection": intersection,
                    "leftover": leftover,
                },
            }

    print(f"traveled indexes: {traveled_indexes}")
    (
        flight_path_who_has_cover,
        ordered_indexes_coverage,
        ordered_coverage_result,
    ) = pre_process_coverage_result(flight.path_with_time, coverage_result)

    print("asking api time")

    start_time = time.time()
    demand_centroid = get_demand_centroid(demand.polygon)
    print("got alt of  demand  path in :--- %s seconds ---" % (time.time() - start_time))
    angles_result = calculate_angels(demand_centroid, flight_path_who_has_cover)

    accesses_result = build_accesses(
        angles_result,
        demand,
        flight.path_with_time,
        ordered_coverage_result,
        ordered_indexes_coverage,
    )

    return accesses_result


def calc_access_for_demand(flight_path, flight_path_with_casing, demand: Demand):
    _, casing_intersection, _ = calculate_intersection_raw(flight_path_with_casing, demand.polygon)

    if not casing_intersection:
        return

    traveled_indexes = set()
    coverage_result = {}  # the key is the index

    for point in casing_intersection.exterior.coords:
        indexes = filter_appropriate_points(flight_path, point)
        for index in indexes:
            if index in traveled_indexes:
                continue
            traveled_indexes.add(index)
            relevant_flight_point = flight_path[index][0]
            coverage_percent, intersection, leftover = get_intersection(relevant_flight_point, demand.polygon)
            if not intersection:
                continue
            coverage_result[str(index)] = {
                "coverage": {
                    "coverage_percent": coverage_percent,
                    "intersection": intersection,
                    "leftover": leftover,
                },
            }

    print(f"traveled indexes: {traveled_indexes}")
    (
        flight_path_who_has_cover,
        ordered_indexes_coverage,
        ordered_coverage_result,
    ) = pre_process_coverage_result(flight_path, coverage_result)

    print("asking api time")

    start_time = time.time()
    demand_centroid = get_demand_centroid(demand.polygon)
    print("got alt of  demand  path in :--- %s seconds ---" % (time.time() - start_time))
    angles_result = calculate_angels(demand_centroid, flight_path_who_has_cover)

    accesses_result = build_accesses(
        angles_result,
        demand,
        flight_path,
        ordered_coverage_result,
        ordered_indexes_coverage,
    )

    return accesses_result


def build_accesses(
    angles_result,
    demand,
    flight_path,
    ordered_coverage_result,
    ordered_indexes_coverage,
):
    chunks = split_to_chunks(ordered_indexes_coverage)
    accesses_result = []
    for chunk in chunks:
        access = {
            "flight_id": "my first flight",
            "sample_rate_sec": INTERVAL_SAMPLE,
            "demand_id": demand.id,
            "start": flight_path[chunk[0]][1],
            "end": flight_path[chunk[-1]][1],
            "coverages": [],
            "angels": [],
        }

        for num in chunk:
            index = binary_search(ordered_indexes_coverage, num)
            azimuth, elevation = angles_result[index]
            if is_in_range(azimuth, demand.allowed_azimuth) and is_in_range(
                elevation, demand.allowed_elevation
            ):
                access["coverages"].append(ordered_coverage_result[str(num)])
                access["angels"].append((azimuth, elevation))

            else:
                if index:
                    access["end"] = flight_path[index - 1][1]
                break

        accesses_result.append(access)
    return accesses_result


def get_demand_centroid(demand):
    demand_centroid: Point = Polygon(demand).centroid
    demand_centroid = _Point(lat=demand_centroid.x, long=demand_centroid.y)
    [demand_centroid] = get_altitude([demand_centroid])
    return demand_centroid


def pre_process_coverage_result(flight_path, result):
    ordered_coverage_result = dict(sorted(result.items(), key=lambda x: int(x[0])))
    ordered_indexes_coverage = [int(index) for index in ordered_coverage_result.keys()]
    flight_path_with_coverage = [
        _Point(lat=flight_path[index][0][0], long=flight_path[index][0][1])
        for index in ordered_indexes_coverage
    ]
    return flight_path_with_coverage, ordered_indexes_coverage, ordered_coverage_result


def binary_search(arr, target):
    low, high = 0, len(arr) - 1

    while low <= high:
        mid = (low + high) // 2

        if arr[mid] == target:
            return mid  # Target found, return the index
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1

    return -1  # Target not found


def calculate_angels(demand_centroid, flight_path_with_coverage):
    angles_result = []
    for flight_point in flight_path_with_coverage:
        azimuth = calculate_azimuth(demand_centroid, flight_point)
        elevation = calculate_elevation_angle(
            demand_centroid, flight_point
        )  # make sure we are actually take care of the alt
        angles_result.append((azimuth, elevation))
    return angles_result


def split_to_chunks(arr):
    result = []
    current_group = []

    for num in arr:
        if not current_group or num == current_group[-1] + 1:
            current_group.append(num)
        else:
            result.append(current_group)
            current_group = [num]

    if current_group:
        result.append(current_group)

    return result


def get_intersection(point, demand, radius=CAMERA_MAX_DISTANCE):
    point_radius = create_geodesic_circle(point[0], point[1], radius=radius)
    return calculate_intersection(point_radius, demand)
