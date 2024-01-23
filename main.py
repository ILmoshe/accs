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
from src.coverage import Demand, create_geodesic_circle, get_coverage_of_flight
from src.logic import create_casing

start_latitude = 32.7526326
start_longitude = 35.0701214

SENSOR_CAPABILITY_IN_KM = 12

path_case = create_casing(haifa_to_lebanon, 12)


def add_time(coord):
    utc = arrow.utcnow()
    return [(point, utc.shift(minutes=index + 2).format()) for index, point in enumerate(coord)]


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


add_flight_path(with_time)

demands = add_demands(
    demand_near_sea,
    demand_not_near_sea,
    demand_in_middle,
    demand_huge_near_sea,
    not_sure_demand,
    fullone,
)

Map.save("flight_path_map.html")


result = calculate_accesses(
    with_time,
    demands,
)


print("FINISHED")
