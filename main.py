import random
import time
import uuid

import arrow
import folium
from folium.plugins import Draw
from shapely.geometry import Polygon

from const import CAMERA_MAX_DISTANCE, INTERVAL_SAMPLE
from data import interpolate_polyline
from data.polygon import *
from data.polyline import haifa_to_lebanon
from line_of_sight import get_fov_polygon
from line_of_sight.create_polygon import calc_continues_fov
from src import Flight, Sensor
from src.coverage import Demand
from src.logic import binary_search, calc_access_for_demand1, create_casing

start_latitude = 32.7526326
start_longitude = 35.0701214


def add_time(coord):
    result = []
    for index, point in enumerate(coord):
        if len(result):
            result.append(
                (
                    point,
                    arrow.get(result[-1][1]).shift(seconds=INTERVAL_SAMPLE).format(),
                )
            )
        else:
            result.append((point, arrow.utcnow().format()))
    return result


def add_flight_path_to_map(flight_route, color):
    kw = {
        "prefix": "fa",
        "color": color,
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

# total_time = 30 * 60  # 30 minutes in seconds
# interval = 20  # seconds
# result_polyline1 = interpolate_polyline(haifa_to_lebanon, total_time, interval)
path_case1 = create_casing(haifa_to_lebanon, CAMERA_MAX_DISTANCE)
folium.PolyLine(haifa_to_lebanon, tooltip="Flight path").add_to(Map)
folium.Polygon(locations=path_case1, color="blue").add_to(Map)
flight_path1 = add_time(haifa_to_lebanon)

sensor1 = Sensor(width_mm=36, height_mm=24, focal_length_mm=300, image_width_px=12400)
flight1 = Flight(
    height_meters=5000,
    path_with_time=flight_path1,
    path_case=path_case1,
    camera_azimuth=99,
    camera_elevation=15,
    sensor=sensor1,
)
print(flight1.camera_capability_meters)
# flight1.path_case = create_casing(result_polyline1, flight1.camera_capability_meters)


add_flight_path_to_map(flight1.path_with_time, "blue")


demands = add_demands_to_map(
    demand_near_sea,
    demand_not_near_sea,
    demand_in_middle,
    demand_huge_near_sea,
    not_sure_demand,
    # fullone,
    long_demand,
    near_haifa,
    Even,
    Idan,
)

# demands[-1].allowed_azimuth = {"from": 0, "to": 294}


def generate_random_colors(num_colors):
    colors = []

    for _ in range(num_colors):
        red = random.randint(0, 150)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)

        hex_color = f"#{red:02x}{green:02x}{blue:02x}"
        colors.append(hex_color)

    return colors


def add_accesses_to_popup(accesses, demand, color):
    html = """
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
                    intersection_centroid = [
                        intersection_centroid.x,
                        intersection_centroid.y,
                    ]
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


# result_polyline2 = interpolate_polyline(circle, total_time, interval)
# path_case2 = create_casing(result_polyline2, CAMERA_MAX_DISTANCE)
# flight_path2 = add_time(result_polyline2)
# folium.PolyLine(circle, tooltip="Flight path").add_to(Map)
# folium.Polygon(locations=path_case2, color="red").add_to(Map)
# add_flight_path_to_map(flight_path2, "red")
#
# sensor2 = Sensor(width_mm=36, height_mm=24, focal_length_mm=300, image_width_px=10_000)
# flight2 = Flight(
#     height_meters=5000,
#     path_with_time=flight_path2,
#     path_case=path_case2,
#     camera_azimuth=-80,
#     camera_elevation=-15,
#     sensor=sensor2,
# )
print(f"Camera capability 1: {flight1.camera_capability_meters}")
# print(f"Camera capability 2: {flight2.camera_capability_meters}")

# iterate_over = zip([flight1.path_with_time, flight2.path_with_time], [flight1.path_case, flight2.path_case])


for fl in [flight1]:
    start_time = time.time()
    accesses = []
    for demand in demands:
        result = calc_access_for_demand1(fl, demand)
        accesses.append(result)
    print(f"got access of {len(demands)} demands path in :--- %s seconds ---" % (time.time() - start_time))
    add_accesses_to_flight_on_map(accesses, demands, fl.path_with_time)



# just for visualization purpose
for index, point in enumerate(flight1.path_with_time):
    if index + 1 == len(flight1.path_with_time):
        break
    focal_point = [*point[0], flight1.height_meters]
    azimuth = flight1.get_relative_azimuth_to_flight_direction(
        flight1.path_with_time[index][0], flight1.path_with_time[index + 1][0]
    )
    fov_polygon = get_fov_polygon(flight1.sensor, [azimuth, flight1.camera_elevation], focal_point)

    # for index, (lat, long) in enumerate(fov_polygon):
    #     kw = {
    #         "prefix": "fa",
    #         "color": "green",
    #         "icon": "arrow-up",
    #     }
    #     icon_angle = 270
    #     icon = folium.Icon(angle=icon_angle, **kw)
    #     folium.Marker(
    #         location=[lat, long],
    #         icon=icon,
    #         tooltip=str(index + 1),
    #     ).add_to(Map)

    folium.Polygon(
        locations=fov_polygon,
        weight=0.81,
        fill_opacity=0.2,
        tooltip="camera FOV",
        fill=True,
        color="red",
    ).add_to(Map)

print(f"GSD flight1: {flight1.gsd}")
# print(f"GSD flight2: {flight2.gsd}")


for i in range(len(haifa_to_lebanon) - 1):
    first_point = haifa_to_lebanon[i]
    second_point = haifa_to_lebanon[i + 1]

    f1_point_with_height = [*first_point, 5000]
    f2_point_with_height = [*second_point, 5000]

    azimuth = flight1.get_relative_azimuth_to_flight_direction(first_point, second_point)
    fov_polygon1 = get_fov_polygon(flight1.sensor, [azimuth, flight1.camera_elevation], f1_point_with_height)
    fov_polygon2 = get_fov_polygon(flight1.sensor, [azimuth, flight1.camera_elevation], f2_point_with_height)

    continues_fov = calc_continues_fov(fov_polygon1, fov_polygon2)
    folium.Polygon(
        locations=continues_fov,
        weight=0.11,
        fill_opacity=0.6,
        tooltip="camera FOV",
        fill=True,
        color="green",
    ).add_to(Map)

print("I AM HERE!!!")
Map.save("flight_path_map.html")
print("FINISHED")
