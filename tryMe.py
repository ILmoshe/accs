import numpy as np
from geopy.distance import geodesic


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
    points = [(lat1 + i * lat_fraction, lon1 + i * lon_fraction) for i in range(1, num_segments)]

    return points


# Example points A and B (latitude and longitude in decimal degrees)
point_A = (40.7128, -74.0060)  # New York City
point_B = (34.0522, -118.2437)  # Los Angeles

# Calculate points along the line connecting A and B at 500-meter intervals
interval_distance = 500  # in meters
points = points_along_line(point_A[0], point_A[1], point_B[0], point_B[1], interval_distance)

# Print the result
for idx, point in enumerate(points):
    print(f"Point {idx + 1}: Latitude {point[0]}, Longitude {point[1]}")
