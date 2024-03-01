import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

from line_of_sight.sensor_position import calculate_rotated_points


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


SENSOR_WIDTH = 3
SENSOR_HEIGHT = 2
FOCAL_LENGTH = 2
AZIMUTH = 20
ELEVATION = -70
FOCAL_POINT = np.array([0, 0, 8])


A_rotated, B_rotated, C_rotated, D_rotated = calculate_rotated_points(
    SENSOR_WIDTH, SENSOR_HEIGHT, FOCAL_LENGTH, AZIMUTH, ELEVATION, FOCAL_POINT
)

intersections = []

for point in [A_rotated, B_rotated, C_rotated, D_rotated]:
    intersection = intersection_point(FOCAL_POINT, point)
    intersections.append(intersection)


plot_surface(intersections)

# # Example usage:
# point_A = [2, 2, 5]
# point_B = [1, 1, 1]
# intersection = intersection_point(point_A, point_B)
print("Intersection points:", intersections)
