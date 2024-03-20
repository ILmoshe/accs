import numpy as np
from geopy.distance import distance, geodesic


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


from src import get_altitude


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


def calculate_los_for_point():
    traveld_already = set()
    focal_point = (1, 1, 1)
    grid_centeroids = list[Point]
    intersection_with_demand = Polygon

    for centeroid in grid_centeroids:
        if centeroid in traveld_already:
            continue
        alt_centeroid = get_altitude([centeroid])
        points = points_along_line(focal_point[0], focal_point[1], centeroid[0], centeroid[1])

        for point in points:
            alt = get_z_value_from_line(focal_point, alt_centeroid, point[0], point[1])
            real_alt = get_altitude(point)
            if real_alt[2] >= alt:  # We dont have line of sight
                break  # we somehow need to notify that we didn't found LOS for that shhit

        # we found acces
        traveld_already.add(
            "founded access"
        )  # somehow notifyt that we dont need to travel here any more because we did found LOS


# Example usage
p1 = (1, 1, 1)
p2 = (3, 3, 3)
x, y = 2, 2  # The x and y values for which we want to find z

z = get_z_value_from_line(p1, p2, x, y)
print(f"The z value for x={x} and y={y} on the line is: {z}")

import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon, box


def create_grid_polygons(polygon, cell_size):
    """
    Divides a polygon into a grid of smaller polygons (cells).

    Parameters:
        polygon (Polygon): The input polygon.
        cell_size (float): The size of the grid cells.

    Returns:
        list[Polygon]: A list of polygons representing the grid cells that intersect the input polygon.
    """
    minx, miny, maxx, maxy = polygon.bounds
    grid_polygons = []

    # Create grid cells within the bounding box of the input polygon
    for x in np.arange(minx, maxx, cell_size):
        for y in np.arange(miny, maxy, cell_size):
            # Define the current cell as a polygon (box)
            cell = box(x, y, x + cell_size, y + cell_size)
            # If the cell intersects the polygon, add it to the list
            if cell.intersects(polygon):
                # Clip the cell to the input polygon (to handle partial overlaps)
                clipped_cell = cell.intersection(polygon)
                grid_polygons.append(clipped_cell)

    return grid_polygons


# Define a polygon (e.g., a rectangle with a notch)
input_polygon = Polygon([(0, 0), (10, 0), (10, 5), (5, 5), (5, 10), (0, 10)])
# Define the cell size
cell_size = 0.3

# Generate the grid polygons
grid_polygons = create_grid_polygons(input_polygon, cell_size)

# Plotting
fig, ax = plt.subplots()
# Plot the input polygon
x, y = input_polygon.exterior.xy
ax.fill(x, y, alpha=0.5, fc="lightblue", ec="black")

# Plot each grid cell that intersects with the polygon
print(len(grid_polygons))
for poly in grid_polygons:
    x, y = poly.exterior.xy
    ax.plot(x, y, color="red")

ax.set_title("Polygon with Grid Overlay")
plt.show()
