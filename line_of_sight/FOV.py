import matplotlib.pyplot as plt
import numpy as np


def intersection_point(point1, point2) -> list[float]:
    """
    Calculating intersection with the plain when z=0
    :param point1:
    :param point2:
    :return: The intersection point on the plain where z=0
    """
    # Calculate the direction vector of the line passing through the two points
    direction_vector = [point2[i] - point1[i] for i in range(3)]

    # Find the parameter t when the line intersects the two-dimensional plane (z=0)
    t = point1[2] / (point1[2] - point2[2])

    # Calculate the coordinates of the intersection point
    intersection_x = point1[0] + t * direction_vector[0]
    intersection_y = point1[1] + t * direction_vector[1]
    intersection_z = 0

    return [intersection_x, intersection_y, intersection_z]


def plot_surface(points, figsize=(8, 6)):
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection="3d")

    # Extract x, y, and z coordinates
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    zs = [point[2] for point in points]

    # Create and plot the polygon
    ax.plot_trisurf(xs, ys, zs, alpha=0.8)

    # Set labels and title
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("Rotated Rectangle")

    # Set axis limits slightly larger than the data range
    ax.set_xlim3d(0, 100000000000)
    ax.set_ylim3d(0, 100000000000)
    ax.set_zlim3d(0, 100000000000)

    plt.show()


def lat_lon_to_mm(latitude, longitude, origin_lat, origin_lon):
    """

    :param latitude:
    :param longitude:
    :param origin_lat:
    :param origin_lon:
    :return: lat, lon
    """
    # Conversion factors
    lat_to_mm = (
        111000 * 1000
    )  # 1 degree of latitude is approximately 111 kilometers, converted to millimeters
    lon_to_mm = (
        111000 * np.cos(np.radians(origin_lat)) * 1000
    )  # Longitude conversion varies with latitude

    # Calculate offsets from the origin
    lat_offset = (latitude - origin_lat) * lat_to_mm
    lon_offset = (longitude - origin_lon) * lon_to_mm

    return lat_offset, lon_offset


def mm_to_lat_lon(lat_offset, lon_offset, origin_lat, origin_lon):
    """

    :param lat_offset:
    :param lon_offset:
    :param origin_lat:
    :param origin_lon:
    :return: lat, lon
    """
    # Conversion factors
    mm_to_lat = 1 / (111000 * 1000)  # Inverse of latitude conversion factor
    mm_to_lon = 1 / (
        111000 * np.cos(np.radians(origin_lat)) * 1000
    )  # Inverse of longitude conversion factor

    # Calculate latitude and longitude from offsets and origin
    latitude = origin_lat + lat_offset * mm_to_lat
    longitude = origin_lon + lon_offset * mm_to_lon

    return latitude, longitude


# Example usage for calc
# SENSOR_WIDTH_MM = 36
# SENSOR_HEIGHT_MM = 24
# FOCAL_LENGTH_MM = 500
# AZIMUTH = -80
# ELEVATION = -15
#
# FOCAL_POINT_XY = [32.931507, 34.926353]  # lat, lon
# REFERENCE_POINT = [32.835751, 34.606934]
#
# FOCAL_POINT_XY_MM = lat_lon_to_mm(
#     FOCAL_POINT_XY[0], FOCAL_POINT_XY[1], REFERENCE_POINT[0], REFERENCE_POINT[1]
# )
#
#
# FOCAL_POINT_XYZ_MM = [
#     FOCAL_POINT_XY_MM[1],
#     FOCAL_POINT_XY_MM[0],
#     5000 * 1000,
# ]  # lon is y and lat is x
#
# A_rotated, B_rotated, C_rotated, D_rotated = calculate_rotated_points(
#     SENSOR_WIDTH_MM,
#     SENSOR_HEIGHT_MM,
#     FOCAL_LENGTH_MM,
#     AZIMUTH,
#     ELEVATION,
#     FOCAL_POINT_XYZ_MM,
# )
#
# intersections = []
#
# for point in [A_rotated, B_rotated, C_rotated, D_rotated]:
#     intersection = intersection_point(FOCAL_POINT_XYZ_MM, point)
#     interaction_lat_lon = mm_to_lat_lon(
#         intersection[1], intersection[0], REFERENCE_POINT[0], REFERENCE_POINT[1]
#     )
#     intersections.append([*interaction_lat_lon])  # add z latter
#
# print("Intersection points:", intersections)


# plot_surface(intersections)
