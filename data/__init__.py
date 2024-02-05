import numpy as np


def swap(polygon):
    result = [(coord[1], coord[0]) for coord in polygon]
    return result


def interpolate_polyline(polyline, total_time, interval):
    num_intervals = int(total_time / interval)
    points = len(polyline)

    # Create a numpy array from the original polyline
    polyline_array = np.array(polyline)

    # Calculate the total distance of the original polyline
    distances = np.linalg.norm(np.diff(polyline_array, axis=0), axis=1)
    total_distance = np.sum(distances)

    # Calculate the distance between each added point
    interval_distance = total_distance / num_intervals

    # Initialize variables
    current_distance = 0
    result_polyline = [polyline[0]]  # Start with the first point

    for i in range(1, points):
        # Calculate the distance between consecutive points
        segment_distance = np.linalg.norm(polyline_array[i] - polyline_array[i - 1])

        # If adding a point in the current segment would exceed the interval distance
        while current_distance + segment_distance >= interval_distance:
            # Calculate the position of the new point using linear interpolation
            t = (interval_distance - current_distance) / segment_distance
            new_point = (1 - t) * np.array(polyline[i - 1]) + t * np.array(polyline[i])

            # Add the new point to the result polyline
            result_polyline.append(new_point.tolist())

            # Update variables
            current_distance = (
                0 if current_distance == interval_distance else current_distance - interval_distance
            )

        current_distance += segment_distance

    return result_polyline
