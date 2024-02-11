import random
import time
import uuid

import arrow
import folium
from folium.plugins import Draw
from shapely.geometry import Polygon

from const import CAMERA_CAPABILITY, INTERVAL_SAMPLE
from data.polygon import *
from data.polyline import haifa_to_lebanon
from src.coverage import Demand
from src.logic import binary_search, calc_access_for_demand, create_casing
from data import interpolate_polyline

start_latitude = 32.7526326
start_longitude = 35.0701214


def add_time(coord):
    result = []
    for index, point in enumerate(coord):
        if len(result):
            result.append((point, arrow.get(result[-1][1]).shift(seconds=INTERVAL_SAMPLE).format()))
        else:
            result.append((point, arrow.utcnow().format()))
    return result


with_time = add_time(haifa_to_lebanon)


def add_flight_path_to_map(flight_route):
    kw = {
        "prefix": "fa",
        "color": "red",
        "icon": "plane",
    }
    icon_angle = 270

    for (lat, long), time in flight_route:
        icon = folium.Icon(angle=icon_angle, **kw)
        folium.Marker(
            location=[lat, long],
            icon=icon,
            tooltip=str((lat, long, time)),
        ).add_to(Map)


def add_demand(demand: Demand):
    folium.Polygon(
        demand.polygon,
        tooltip=demand.id,
        color="red",
    ).add_to(Map)

    return demand


def add_demands_to_map(*demands: list[list[float, float]]):
    return [add_demand(Demand(id=str(uuid.uuid4()).split("-")[0], polygon=demand)) for demand in demands]


# Actual path drawing
Map = folium.Map(
    location=[start_latitude, start_longitude],
    zoom_start=10,
    tiles="cartodb positron",
)

Draw(export=True).add_to(Map)

total_time = 30 * 60  # 30 minutes in seconds
interval = 20  # seconds
result_polyline = interpolate_polyline(haifa_to_lebanon, total_time, interval)
path_case = create_casing(result_polyline, CAMERA_CAPABILITY)


# Flight path
folium.PolyLine(haifa_to_lebanon, tooltip="Flight path").add_to(Map)
folium.Polygon(locations=path_case, color="blue").add_to(Map)
flight_path = add_time(result_polyline)

add_flight_path_to_map(flight_path)


demands = add_demands_to_map(
    demand_near_sea,
    demand_not_near_sea,
    demand_in_middle,
    demand_huge_near_sea,
    not_sure_demand,
    fullone,
    long_demand,
    near_haifa,
    # b,
)


def generate_random_colors(num_colors):
    colors = []

    for _ in range(num_colors):
        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)

        hex_color = f"#{red:02x}{green:02x}{blue:02x}"
        colors.append(hex_color)

    return colors


def add_accesses_to_popup(accesses, demand, color):
    html = f"""
        <h1>Demand Accesses</h1><br>
            <ul>\n
        """
    for access in accesses:
        style = "<br/>~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ <br/>"
        access_start = f"{style}<li>Start: {access['start']}<br/>"
        access_end = f"<li>end: {access['end']}<br/>"
        html += access_start + access_end

    html += "</ul>"
    folium.Polygon(
        demand.polygon,
        tooltip=demand.id,
        popup=html,
        color=color,
    ).add_to(Map)


def add_accesses_to_flight_on_map(accesses, demands, flight_path):
    colors = generate_random_colors(len(accesses))
    flight_times = [flightparams[1] for flightparams in flight_path]

    for accesses_for_demand, color, demand in zip(accesses, colors, demands):
        if accesses_for_demand is None:
            continue
        add_accesses_to_popup(accesses_for_demand, demand, color)
        for access in accesses_for_demand:
            index_of_start_access_in_flight_path = binary_search(flight_times, access["start"])
            index_of_end_access_in_flight_path = binary_search(flight_times, access["end"])
            for index in range(index_of_end_access_in_flight_path - index_of_start_access_in_flight_path):
                intersection_polygon = access["coverages"][index]["coverage"]["intersection"]
                intersection_centroid = Polygon(intersection_polygon).centroid
                if intersection_centroid:  # TODO: take a deep look when this shit happens
                    intersection_centroid = [intersection_centroid.x, intersection_centroid.y]
                else:
                    continue
                flight_point = flight_path[index_of_start_access_in_flight_path + index][0]
                angels = access["angels"][index]

                kwargs = {"color": color}

                folium.PolyLine(
                    [intersection_centroid, flight_point],
                    tooltip=f"Azimuth: {angels[0]}. Elevation: {angels[1]}",
                    **kwargs,
                ).add_to(Map)
                folium.Polygon(
                    locations=intersection_polygon,
                    weight=0.5,
                    fill_opacity=0.02,
                    # tooltip=f"intersection {index + 1}",
                    fill=True,
                    **kwargs,
                ).add_to(Map)


start_time = time.time()
accesses = []
for demand in demands:
    result = calc_access_for_demand(flight_path, path_case, demand)
    accesses.append(result)
print(f"got access of {len(demands)} demands path in :--- %s seconds ---" % (time.time() - start_time))


add_accesses_to_flight_on_map(accesses, demands, flight_path)


Map.save("flight_path_map.html")
print("FINISHED")
