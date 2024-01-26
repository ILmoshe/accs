import random

import arrow
import folium
from folium.plugins import Draw

from data.polygon import (
    demand_huge_near_sea,
    demand_in_middle,
    demand_near_sea,
    demand_not_near_sea,
    fullone,
    not_sure_demand,
)
from data.polyline import haifa_to_lebanon
from src.access import get_accesses
from src.coverage import Demand, create_geodesic_circle, get_coverage_of_flight
from src.logic import create_casing

start_latitude = 32.7526326
start_longitude = 35.0701214

SENSOR_CAPABILITY_IN_KM = 12

path_case = create_casing(haifa_to_lebanon, 12)


def add_time(coord):
    result = []
    for index, point in enumerate(coord):
        if len(result):
            result.append((point, arrow.get(result[-1][1]).shift(seconds=10).format()))
        else:
            result.append((point, arrow.utcnow().format()))
    return result


with_time = add_time(haifa_to_lebanon)


def add_flight_path(flight_route):
    kw = {"prefix": "fa", "color": "red", "icon": "plane"}
    icon_angle = 270

    for (lat, long), time in flight_route:
        icon = folium.Icon(angle=icon_angle, **kw)
        folium.Marker(
            location=[lat, long],
            icon=icon,
            tooltip=str((lat, long, time)),
        ).add_to(Map)

        circle_polygon = create_geodesic_circle(lat, long, SENSOR_CAPABILITY_IN_KM * 1000)

        # add sensor capability
        folium.Polygon(
            circle_polygon,
            color="black",
            weight=0.1,
            fill_opacity=0.05,
            opacity=1,
            fill_color="green",
            fill=False,  # gets overridden by fill_color
            popup=f"{SENSOR_CAPABILITY_IN_KM} meters",
            tooltip="sensor capability",
        ).add_to(Map)


# def calculate_accesses(flight_path, demands):
#     return get_coverage_of_flight(
#         flight_path,
#         demands,
#         SENSOR_CAPABILITY_IN_KM * 1000,
#     )


def route_sample():
    """
    I get a basic route and I want to add points in the route
    :return:
    """
    pass


def add_demand(demand: Demand):
    folium.Polygon(
        demand.polygon,
        tooltip=demand.id,
        color="red",
    ).add_to(Map)

    return demand


def add_demands(*demands: list[list[float, float]]):
    import uuid

    return [add_demand(Demand(id=str(uuid.uuid4()), polygon=demand)) for demand in demands]


# Actual path drawing
Map = folium.Map(
    location=[start_latitude, start_longitude],
    zoom_start=10,
    tiles="cartodb positron",
)

Draw(export=True).add_to(Map)

# Flight path
folium.PolyLine(haifa_to_lebanon, tooltip="Flight path").add_to(Map)


# add_flight_path(with_time)

demands = add_demands(
    demand_near_sea,
    demand_not_near_sea,
    demand_in_middle,
    demand_huge_near_sea,
    not_sure_demand,
    fullone,
)


# result = calculate_accesses(
#     with_time,
#     demands,
# )


# accesses = get_accesses("my_first_flight", with_time, demands)


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

result_polyline = interpolate_polyline(polyline, total_time, interval)
print(result_polyline)
print(len(result_polyline))


from data import swap


heavy_flight = add_time(swap(result_polyline))

kw = {"prefix": "fa", "color": "red", "icon": "plane"}
icon_angle = 270

for (lat, long), time in heavy_flight:
    icon = folium.Icon(angle=icon_angle, **kw)
    folium.Marker(
        location=[lat, long],
        icon=icon,
        tooltip=str((lat, long, time)),
    ).add_to(Map)



add_flight_path(heavy_flight)

result = get_accesses(
    "my heact flight",
    heavy_flight,
    demands,
)



Map.save("flight_path_map.html")
print("FINISHED")
