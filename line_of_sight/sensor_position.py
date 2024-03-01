import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from shapely import Polygon


# def calculate_rotated_points(W, H, FL, AZ, EL):
#     """
#     Calculates the positions of points A, B, C, and D after rotations.
#
#     Args:
#         W: Width of the rectangle.
#         H: Height of the rectangle.
#         FL: Distance from the focal point (assumed at (0, 0, 0)) to the center of the rectangle.
#         AZ: Rotation angle around the z-axis in degrees.
#         EL: Rotation angle around the x-axis in degrees.
#
#     Returns:
#         A tuple containing the final positions of points A, B, C, and D as NumPy arrays.
#     """
#
#     # Pre-calculate constants
#     half_W = W / 2
#     half_H = H / 2
#
#     # Initial points relative to the focal point (0, 0, 0)
#     A = np.array([-half_W, FL, half_H])
#     B = np.array([half_W, FL, half_H])
#     C = np.array([half_W, FL, -half_H])
#     D = np.array([-half_W, FL, -half_H])
#
#     # Rotate around x-axis
#     EL_rad = np.radians(EL)
#     R_x = np.array(
#         [
#             [1, 0, 0],
#             [0, np.cos(EL_rad), -np.sin(EL_rad)],
#             [0, np.sin(EL_rad), np.cos(EL_rad)],
#         ]
#     )
#
#     A_rotated_x = R_x.dot(A)
#     B_rotated_x = R_x.dot(B)
#     C_rotated_x = R_x.dot(C)
#     D_rotated_x = R_x.dot(D)
#
#     # Rotate around z-axis
#     AZ_rad = np.radians(AZ)
#     R_z = np.array(
#         [
#             [np.cos(AZ_rad), -np.sin(AZ_rad), 0],
#             [np.sin(AZ_rad), np.cos(AZ_rad), 0],
#             [0, 0, 1],
#         ]
#     )
#
#     A_rotated = R_z.dot(A_rotated_x)
#     B_rotated = R_z.dot(B_rotated_x)
#     C_rotated = R_z.dot(C_rotated_x)
#     D_rotated = R_z.dot(D_rotated_x)
#
#     return A_rotated, B_rotated, C_rotated, D_rotated


def plot_rotated_rectangle(points, figsize=(8, 6)):
    """
    Plots the 3D polygon formed by the given points.

    Args:
        points: A list of four NumPy arrays representing the corner points of the rectangle.
        figsize: Optional, a tuple specifying the figure size (width, height) in inches.
    """

    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection="3d")

    # Extract x, y, and z coordinates
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    zs = [point[2] for point in points]

    # Create and plot the polygon
    ax.scatter(
        FOCAL_POINT[0], FOCAL_POINT[1], FOCAL_POINT[2], marker="^", edgecolors="red"
    )  # center points the focal-length
    ax.plot_trisurf(xs, ys, zs, alpha=0.8)

    # Set labels and title
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("Rotated Rectangle")

    # Set axis limits slightly larger than the data range
    ax.set_xlim3d(-10, 10)
    ax.set_ylim3d(-10, 10)
    ax.set_zlim3d(0, 10)

    plt.show()


def calculate_rotated_points(W, H, FL, AZ, EL, focal_point):
    """
    Calculates the positions of points A, B, C, and D after rotations.

    Args:
        W: Width of the rectangle.
        H: Height of the rectangle.
        FL: Distance from the focal point to the center of the rectangle.
        AZ: Rotation angle around the z-axis in degrees.
        EL: Rotation angle around the x-axis in degrees.
        focal_point: A numpy array representing the focal point coordinates (x, y, z).

    Returns:
        A tuple containing the final positions of points A, B, C, and D as NumPy arrays.
    """

    # Pre-calculate constants
    half_W = W / 2
    half_H = H / 2

    # Points relative to the focal point
    A = np.array([-half_W, FL, half_H]) + focal_point
    B = np.array([half_W, FL, half_H]) + focal_point
    C = np.array([half_W, FL, -half_H]) + focal_point
    D = np.array([-half_W, FL, -half_H]) + focal_point

    # Rotate around x-axis
    EL_rad = np.radians(EL)
    R_x = np.array(
        [
            [1, 0, 0],
            [0, np.cos(EL_rad), -np.sin(EL_rad)],
            [0, np.sin(EL_rad), np.cos(EL_rad)],
        ]
    )

    A_rotated_x = R_x.dot(A - focal_point)
    B_rotated_x = R_x.dot(B - focal_point)
    C_rotated_x = R_x.dot(C - focal_point)
    D_rotated_x = R_x.dot(D - focal_point)

    # Rotate around z-axis
    AZ_rad = np.radians(AZ)
    R_z = np.array(
        [
            [np.cos(AZ_rad), -np.sin(AZ_rad), 0],
            [np.sin(AZ_rad), np.cos(AZ_rad), 0],
            [0, 0, 1],
        ]
    )

    A_rotated = R_z.dot(A_rotated_x) + focal_point
    B_rotated = R_z.dot(B_rotated_x) + focal_point
    C_rotated = R_z.dot(C_rotated_x) + focal_point
    D_rotated = R_z.dot(D_rotated_x) + focal_point

    return A_rotated, B_rotated, C_rotated, D_rotated


def decimal_degrees_to_meters(latitude, longitude):
    # Earth's radius in meters
    earth_radius = 6378137  # meters

    # Conversion factors for latitude and longitude
    lat_conversion_factor = 2 * np.pi * earth_radius / 360
    lon_conversion_factor = lat_conversion_factor * np.cos(np.radians(latitude))

    # Convert degrees to meters
    x = longitude * lon_conversion_factor
    y = latitude * lat_conversion_factor

    return x, y


def calculate_rotated_points1(W_mm, H_mm, FL_mm, AZ, EL, focal_point_degrees):
    """
    Calculates the positions of points A, B, C, and D after rotations.

    Args:
        W_mm: Width of the rectangle in millimeters.
        H_mm: Height of the rectangle in millimeters.
        FL_mm: Focal length of the camera in millimeters.
        AZ: Rotation angle around the z-axis in degrees.
        EL: Rotation angle around the x-axis in degrees.
        focal_point_degrees: Focal point coordinates in decimal degrees (lat, long, alt).

    Returns:
        A tuple containing the final positions of points A, B, C, and D as NumPy arrays.
    """

    # Convert sensor size and focal length to meters
    W = W_mm / 1000  # Convert millimeters to meters
    H = H_mm / 1000
    FL = FL_mm / 1000

    # Convert focal point from decimal degrees to meters
    focal_point_meters = np.array(decimal_degrees_to_meters(*focal_point_degrees))

    # Pre-calculate constants
    half_W = W / 2
    half_H = H / 2

    # Points relative to the focal point
    A = np.array([-half_W, FL, half_H]) + focal_point_meters
    B = np.array([half_W, FL, half_H]) + focal_point_meters
    C = np.array([half_W, FL, -half_H]) + focal_point_meters
    D = np.array([-half_W, FL, -half_H]) + focal_point_meters

    # Rotate around x-axis
    EL_rad = np.radians(EL)
    R_x = np.array(
        [
            [1, 0, 0],
            [0, np.cos(EL_rad), -np.sin(EL_rad)],
            [0, np.sin(EL_rad), np.cos(EL_rad)],
        ]
    )

    A_rotated_x = R_x.dot(A - focal_point_meters)
    B_rotated_x = R_x.dot(B - focal_point_meters)
    C_rotated_x = R_x.dot(C - focal_point_meters)
    D_rotated_x = R_x.dot(D - focal_point_meters)

    # Rotate around z-axis
    AZ_rad = np.radians(AZ)
    R_z = np.array(
        [
            [np.cos(AZ_rad), -np.sin(AZ_rad), 0],
            [np.sin(AZ_rad), np.cos(AZ_rad), 0],
            [0, 0, 1],
        ]
    )

    A_rotated = R_z.dot(A_rotated_x) + focal_point_meters
    B_rotated = R_z.dot(B_rotated_x) + focal_point_meters
    C_rotated = R_z.dot(C_rotated_x) + focal_point_meters
    D_rotated = R_z.dot(D_rotated_x) + focal_point_meters

    return A_rotated, B_rotated, C_rotated, D_rotated


def intersection_point(point1, point2):
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
    """
    Plots the 3D polygon formed by the given points.

    Args:
        points: A list of four NumPy arrays representing the corner points of the rectangle.
        figsize: Optional, a tuple specifying the figure size (width, height) in inches.
    """

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
    ax.set_xlim3d(-20, 20)
    ax.set_ylim3d(-20, 20)
    ax.set_zlim3d(0, 10)

    plt.show()


# A_rotated, B_rotated, C_rotated, D_rotated = calculate_rotated_points(
#     SENSOR_WIDTH, SENSOR_HEIGHT, FOCAL_LENGTH, AZIMUTH, ELEVATION, FOCAL_POINT
# )


SENSOR_WIDTH = 3  # millimeters
SENSOR_HEIGHT = 2  # millimeters
FOCAL_LENGTH = 2  # millimeters
AZIMUTH = 20  # degrees
ELEVATION = -70  # degrees
FOCAL_POINT = (32.882326, 34.90202, 2000)

A_rotated, B_rotated, C_rotated, D_rotated = calculate_rotated_points1(
    SENSOR_WIDTH, SENSOR_HEIGHT, FOCAL_LENGTH, AZIMUTH, ELEVATION, FOCAL_POINT
)

intersections = []
for point in [A_rotated, B_rotated, C_rotated, D_rotated]:
    intersection = intersection_point(FOCAL_POINT, point)
    intersections.append(intersection)


plot_surface(intersections)
print("Intersection points:", intersections)


# # Example usage
# SENSOR_WIDTH = 3
# SENSOR_HEIGHT = 2
# FOCAL_LENGTH = 2
# AZIMUTH = 1
# ELEVATION = -89
# FOCAL_POINT = np.array([0, 0, 8])
#
#
# A_rotated, B_rotated, C_rotated, D_rotated = calculate_rotated_points(
#     SENSOR_WIDTH, SENSOR_HEIGHT, FOCAL_LENGTH, AZIMUTH, ELEVATION, FOCAL_POINT
# )
# # polygonB = Polygon([A_rotated, B_rotated, C_rotated, D_rotated])
# # print(f"POLYGON: {polygonB}")
#
# print("Final positions:")
# print("A:", A_rotated)
# print("B:", B_rotated)
# print("C:", C_rotated)
# print("D:", D_rotated)
#
#
# polygonA = Polygon([A_rotated, B_rotated, C_rotated, D_rotated])
# print(f"POLYGON: {polygonA}")
#
# plot_rotated_rectangle([A_rotated, B_rotated, C_rotated, D_rotated])
