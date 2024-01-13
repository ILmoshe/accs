from geopy.distance import geodesic
from shapely.geometry import LineString, Polygon

# Polygon: list[[float, float]]
# Polyline: list[[float, float]]


def add_meters_to_coordinates(
    coordinates, distance_in_meters, azimuth_to_north: int = 90
):
    lat, lon, alt = coordinates
    destination_point = geodesic(meters=distance_in_meters).destination(
        point=(lat, lon), bearing=azimuth_to_north
    )

    return destination_point.latitude, destination_point.longitude, alt


def create_casing(polyline, distance_kilometers: float):
    """

    :param polyline:
    :param distance_kilometers:
    :return: Polygon with casing
    """
    line: LineString = LineString(polyline)
    distance_degrees = geodesic(kilometers=distance_kilometers).miles / 69.0
    buffered_line = line.buffer(distance_degrees, join_style=2)

    if buffered_line.is_empty:
        return None

    casing_points = [list(coord) for coord in buffered_line.exterior.coords]

    return casing_points


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
