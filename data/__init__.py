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


polyline = [
    [35.0701214, 32.7526326],
    [34.8873759, 32.7537875],
    [34.891498, 32.8622859],
    [34.9368409, 32.9522158],
    [34.995924, 33.0639242],
    [35.0563811, 33.1524991],
    [35.1003499, 33.2409847],
    [35.1223343, 33.2960993],
    [35.1456928, 33.3569146],
    [35.1731733, 33.4108096],
    [35.2061499, 33.4784176],
    [35.230407, 33.54025],
    [35.256506, 33.592575],
    [35.282606, 33.6089009],
    [35.307079, 33.636725],
    [35.331552, 33.664549],
    [35.3435525, 33.6729257],
]
total_time = 30 * 60  # 30 minutes in seconds
interval = 10  # seconds

# result_polyline = interpolate_polyline(polyline, total_time, interval)
# print(result_polyline)
# print(len(result_polyline))
#
# heavy_flight = add_time(swap(result_polyline))
