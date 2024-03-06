from shapely.geometry import Polygon

from .FOV import intersection_point, lat_lon_to_mm, mm_to_lat_lon
from .sensor_position import calculate_rotated_points

REFERENCE_POINT = [32.835751, 34.606934]


def get_fov_polygon(sensor, angels: list[float], focal_point: list[float, float, float]) -> list[list[float]]:
    azimuth, elevation = angels

    focal_point_xy_mm = lat_lon_to_mm(focal_point[0], focal_point[1], REFERENCE_POINT[0], REFERENCE_POINT[1])
    focal_point_xyz_mm = [
        focal_point_xy_mm[1],
        focal_point_xy_mm[0],
        focal_point[2] * 1000,
    ]  # lon is y and lat is x

    a_rotated, b_rotated, c_rotated, d_rotated = calculate_rotated_points(
        sensor.width_mm,
        sensor.height_mm,
        sensor.focal_length_mm,
        azimuth,
        elevation,
        focal_point_xyz_mm,
    )
    intersections = []
    for point in [a_rotated, b_rotated, c_rotated, d_rotated]:
        intersection = intersection_point(focal_point_xyz_mm, point)
        interaction_lat_lon = mm_to_lat_lon(
            intersection[1], intersection[0], REFERENCE_POINT[0], REFERENCE_POINT[1]
        )

        intersections.append([*interaction_lat_lon])  # add z latter, curr z is 0

    return intersections
