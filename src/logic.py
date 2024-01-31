from shapely.geometry import LineString, Point, Polygon

from src import Point as _Point
from src import get_elevations
from src.angels import calculate_azimuth, calculate_elevation_angle, is_in_range
from src.coverage import (
    calculate_intersection,
    calculate_intersection_raw,
    create_geodesic_circle,
)


def add_meters_to_coordinates(coordinates, distance_in_meters, azimuth_to_north: int = 90):
    lat, lon, alt = coordinates
    destination_point = geodesic(meters=distance_in_meters).destination(point=(lat, lon), bearing=0)

    return destination_point.latitude, destination_point.longitude


def create_casing(polyline, distance_km: float):
    """
    :param polyline: List of (lon, lat) points representing the polyline
    :param distance_km: Desired distance in kilometers for the casing
    :return: List of casing points (lon, lat)
    """
    line = LineString(polyline)

    # Calculate the approximate conversion from kilometers to degrees for buffer distance
    centroid_lat = line.centroid.y
    buffer_distance_degrees = geodesic(kilometers=distance_km).destination((centroid_lat, 0), 90).longitude

    # Create buffer polygon using Shapely
    buffered_line = line.buffer(buffer_distance_degrees, join_style=2)

    if buffered_line.is_empty:
        return None

    casing_points = [list(coord) for coord in buffered_line.exterior.coords]

    return casing_points


def traveler():
    pass


def closest_point_index(polyline, target_point):
    """
    Find the index of the closest point in the polyline to the target point.

    :param polyline: List of (lat, lon) points representing the polyline
    :param target_point: (lat, lon) representing the target point
    :return: Index of the closest point in the polyline
    """
    line = LineString(polyline)
    target_point = Point(target_point)

    min_distance = float("inf")
    closest_index = -1

    for index, coord in enumerate(line.coords):
        current_point = Point(coord)
        distance = geodesic(
            target_point.coords[0][::-1], current_point.coords[0][::-1]
        ).meters  # In geopy is lon, lat

        if distance < min_distance:
            min_distance = distance
            closest_index = index

    return closest_index


def compute_coverage(case, demand):
    """
    :param case: The actual case polygon
    :param demand: The demand polygon
    :return: tuple of overlap percentage and the actual polygon
    """
    case = Polygon(case)
    demand = Polygon(demand)

    overlap_percent = 0.0

    intersected_polygon = []
    if case.intersects(demand):
        intersection = case.intersection(demand)
        new_polygon_area = case.area

        exterior_cords = intersection.exterior.coords
        intersected_polygon = [list(coord) for coord in exterior_cords]

        overlap_percent = (intersection.area / new_polygon_area) * 100

    return overlap_percent, intersected_polygon


from geopy.distance import geodesic


def create_sorted_array(polyline):
    points_with_index = [(lat, lon, i) for i, (lat, lon) in enumerate(polyline)]
    sorted_points = sorted(points_with_index, key=lambda x: (x[0], x[1]))
    return sorted_points


def closest_point_index_binary_search(sorted_array, target_point):
    left, right = 0, len(sorted_array) - 1
    min_distance = float("inf")
    closest_index = -1

    while left <= right:
        mid = (left + right) // 2
        current_point = sorted_array[mid][:2]
        target_coords = target_point

        distance = geodesic(target_coords, current_point).meters

        if distance < min_distance:
            min_distance = distance
            closest_index = sorted_array[mid][2]  # Update closest index

        if target_coords < current_point:
            right = mid - 1
        else:
            left = mid + 1

    return closest_index


# Example usage:
flight_path = [(lat, lon) for lat, lon in zip(range(10), range(10))]
sorted_array = create_sorted_array(flight_path)
target_point = (5, 5)

closest_index = closest_point_index_binary_search(sorted_array, target_point)
print(flight_path[closest_index])
print(f"The closest point in the flight path to the target point is at index: {closest_index}")


def calc_access_for_demand(flight_path, flight_path_with_casing, demand):
    _, casing_intersection, _ = calculate_intersection_raw(flight_path_with_casing, demand)

    if not casing_intersection:
        return

    # we will do it beforehand to improve performance
    sorted_flight = create_sorted_array(flight_path)

    traveled_indexes = set()
    coverage_result = {}  # the key is the index

    for point in casing_intersection.coords:
        index = closest_point_index_binary_search(sorted_flight, (point.lat, point.long))
        if index in traveled_indexes:
            continue

        forwordtrack, backtrack = True, True
        for i in range(len(flight_path)):
            forwordtrack_index = index + i
            backtrack_index = index - i - 1

            should_continue_forwordtrack = (
                forwordtrack_index < len(flight_path)
                and forwordtrack
                and forwordtrack_index not in traveled_indexes
            )
            if should_continue_forwordtrack:
                relevant_flight_point_following = flight_path[forwordtrack_index]
                coverage_percent, intersection, leftover = get_intersection(
                    relevant_flight_point_following, demand
                )
                traveled_indexes.add(forwordtrack_index)
                if not intersection:
                    forwordtrack = False
                if forwordtrack:
                    coverage_result[str(forwordtrack_index)] = {
                        "coverage": {
                            "coverage_percent": coverage_percent,
                            "intersection": intersection,
                            "leftover": leftover,
                        },
                    }
            else:
                forwordtrack = False

            should_continue_backtrack = (
                backtrack_index >= 0 and backtrack and backtrack_index not in traveled_indexes
            )
            if should_continue_backtrack:
                relevant_flight_point_back = flight_path[backtrack_index]
                coverage_percent, intersection, leftover = get_intersection(
                    relevant_flight_point_back, demand
                )
                traveled_indexes.add(backtrack_index)
                if not intersection:
                    backtrack = False
                if backtrack:
                    coverage_result[str(forwordtrack_index)] = {
                        "coverage": {
                            "coverage_percent": coverage_percent,
                            "intersection": intersection,
                            "leftover": leftover,
                        },
                    }
            else:
                backtrack = False

            if not forwordtrack and not backtrack:
                break

    (
        flight_path_with_coverage,
        ordered_indexes_coverage,
        ordered_coverage_result,
    ) = pre_process_coverage_result(flight_path, coverage_result)

    demand_centroid = get_demand_centroid(demand)
    angles_result = calculate_angels(demand_centroid, flight_path_with_coverage)

    accesses_result = build_accesses(
        angles_result, demand, flight_path, ordered_coverage_result, ordered_indexes_coverage
    )

    return accesses_result


def build_accesses(angles_result, demand, flight_path, ordered_coverage_result, ordered_indexes_coverage):
    chunks = split_to_chunks(ordered_indexes_coverage)
    accesses_result = []
    for chunk in chunks:
        access = {
            "flight_id": "my first flight",
            "sample_rate_sec": 30,
            "demand_id": demand.id,
            "start": flight_path[chunk[0]][2],
            "end": flight_path[chunk[-1]][2],
            "coverages": [],
            "angels": [],
        }

        for index in chunk:
            azimuth, elevation = angles_result[index]
            if is_in_range(azimuth, demand.allowed_azimuth) and is_in_range(
                elevation, demand.allowed_elevation
            ):
                access["coverages"].append(ordered_coverage_result[str(index)])
                access["angels"].append(angles_result[index])

            else:
                if index:
                    access["end"] = flight_path[index - 1][2]
                break

        accesses_result.append(access)
    return accesses_result


def get_demand_centroid(demand):
    demand_centroid: Point = Polygon(demand).centroid
    demand_centroid = _Point(lat=demand_centroid.x, long=demand_centroid.y)
    demand_centroid = get_elevations([demand_centroid])
    return demand_centroid


def pre_process_coverage_result(flight_path, result):
    ordered_coverage_result = dict(sorted(result.items()))
    ordered_indexes_coverage = [int(index) for index in ordered_coverage_result.keys()]
    flight_path_with_coverage = [
        _Point(lat=flight_path[index][0], long=flight_path[index][1]) for index in ordered_indexes_coverage
    ]
    return flight_path_with_coverage, ordered_indexes_coverage, ordered_coverage_result


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


def get_intersection(point, demand, radius=12_000):
    point_radius = create_geodesic_circle(point[0], point[1], radius=radius)
    return calculate_intersection(point_radius, demand)
