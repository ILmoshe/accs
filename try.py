# x = [
#     Access(
#         demand_id="ef2cbe74-e8f3-4977-aca3-ac5d71f2ab04",
#         flight_id="my_first_flight",
#         start="2024-01-24 18:39:22+00:00",
#         end="2024-01-24 18:39:22+00:00",
#         params=Params(azimuth=295.4332253733194, elevation=-0.3498981153861924),
#     ),
#     Access(
#         demand_id="a4458d4c-9ad6-4d40-9076-5c666395b3b8",
#         flight_id="my_first_flight",
#         start="2024-01-24 18:39:22+00:00",
#         end="2024-01-24 18:40:22+00:00",
#         params=Params(azimuth=268.2506992425667, elevation=-0.2641434168902413),
#     ),
#     Access(
#         demand_id="8101cfdb-972f-4407-9168-5f11b3ae99fb",
#         flight_id="my_first_flight",
#         start="2024-01-24 18:39:22+00:00",
#         end="2024-01-24 18:40:22+00:00",
#         params=Params(azimuth=239.57418457311354, elevation=0.0),
#     ),
#     Access(
#         demand_id="9ed413a8-dbd5-4f9f-8786-8267e0f33eda",
#         flight_id="my_first_flight",
#         start="2024-01-24 18:39:22+00:00",
#         end="2024-01-24 18:39:22+00:00",
#         params=Params(azimuth=109.12894013420083, elevation=0.0),
#     ),
# ]


import numpy as np


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


# Example usage
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
interval = 20  # seconds

result_polyline = interpolate_polyline(polyline, total_time, interval)
print(result_polyline)
print(len(result_polyline))
