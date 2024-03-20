import random
import uuid

import arrow
import folium
from folium.plugins import Draw, HeatMap
from shapely.geometry import Polygon

from const import CAMERA_MAX_DISTANCE, INTERVAL_SAMPLE
from data.polygon import *
from data.polyline import circle, haifa_to_lebanon
from src import Flight, Sensor
from src.coverage import Demand
from src.logic import calculate_arrival_time, create_casing

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


def add_demand(demand: Demand):
    folium.Polygon(demand.polygon, tooltip=demand.id, color="red", weight=1).add_to(Map)

    return demand


def add_demands_to_map(*demands: list[list[float, float]]):
    return [add_demand(Demand(id=str(uuid.uuid4()).split("-")[0], polygon=demand)) for demand in demands]


# Actual path drawing
Map = folium.Map(
    location=[start_latitude, start_longitude],
    zoom_start=11,
    tiles="Cartodb dark_matter",
)

Draw(export=True).add_to(Map)


# path_case1 = create_casing(haifa_to_lebanon, CAMERA_MAX_DISTANCE)
folium.PolyLine(haifa_to_lebanon, tooltip="Flight path").add_to(Map)
# folium.Polygon(locations=path_case1, color="blue").add_to(Map)
flight_path1 = add_time(haifa_to_lebanon)


sensor1 = Sensor(width_mm=36, height_mm=24, focal_length_mm=300, image_width_px=12400)
flight1 = Flight(
    id="first",
    height_meters=10000,
    speed_km_h=500.0,
    path=haifa_to_lebanon,
    path_case=haifa_to_lebanon,
    camera_azimuth=70,
    camera_elevation_start=90,
    camera_elevation_end=30,
    sensor=sensor1,
)


demands = add_demands_to_map(
    demand_near_sea,
    # demand_not_near_sea,
    # demand_in_middle,
    # demand_huge_near_sea,
    # not_sure_demand,
    # fullone,
    # long_demand,
    near_haifa,
    # Even,
    # Idan,
)


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


folium.PolyLine(circle, tooltip="Flight path").add_to(Map)
sensor2 = Sensor(width_mm=36, height_mm=24, focal_length_mm=300, image_width_px=10_000)
flight2 = Flight(
    id="second",
    height_meters=3000,
    path=circle,
    path_case=circle,
    camera_elevation_start=110,
    camera_elevation_end=170,
    camera_azimuth=120,
    sensor=sensor2,
    speed_km_h=1000,
)

# folium.plugins.PolyLineTextPath(
#     circle, "\u2708     ", repeat=True, offset=8, attributes=attr
# ).add_to(Map)


def draw_base_caseing_on_map(polygons, Map: folium.Map):
    for polygon in polygons:
        folium.Polygon(
            locations=polygon,
            weight=0.11,
            fill_opacity=0.3,
            tooltip="camera FOV",
            fill=True,
            color="green",
        ).add_to(Map)


from copy import deepcopy

from src.logic import calculate_accesses_for_demand, create_case_for_flight_path

# def show_demand_detail(accesses):
#     for access in accesses


def calculation(flights: list[Flight], demands: list[Demand]):
    accesses_for_demands = {}
    for flight in flights:
        accesses_along_a_fligth_path = []
        base_case = create_case_for_flight_path(flight)
        draw_base_caseing_on_map((case["case_polygon"] for case in base_case), Map)  # TODO: important!!!

        for demand in demands:
            accesses = calculate_accesses_for_demand(flight, base_case, demand)
            accesses_for_demands[demand.id] = deepcopy(
                {**accesses_for_demands.get(demand.id, {}), flight.id: accesses}
            )
            accesses_along_a_fligth_path.append(accesses)

        # Drawing on map:
        for accesses_for_demand in accesses_along_a_fligth_path:
            for accesses_for_line in accesses_for_demand:
                del accesses_for_line["LOS_GSD"]
                del accesses_for_line["flight_id"]
                del accesses_for_line["demand_id"]
                for line, accesses in accesses_for_line.items():
                    for access in accesses:
                        start_time_access = None
                        end_time_access = None
                        for index, access_point in enumerate(access.values()):
                            start_time_iso = "2024-03-20T10:00:00Z"
                            point = access_point["point"]
                            intersection = access_point["intersection"]

                            if index == 0:  # first access
                                start_time_access = calculate_arrival_time(flight, start_time_iso, point)

                            if index == len(list(access.values())) - 1:  # last access
                                end_time_access = calculate_arrival_time(flight, start_time_iso, point)

                                html = """
                                    <h1>Access</h1><br>
                                        <ul>\n
                                    """

                                style = "<br/>~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ <br/>"
                                access_start = f"{style}<li>Start: {str(start_time_access)}<br/>"
                                access_end = f"<li>end: {str(end_time_access)}<br/>"
                                html += access_start + access_end

                                html += "</ul>"
                                kw = {
                                    "prefix": "fa",
                                    "color": "pink",
                                    "icon": "card",
                                }
                                icon_angle = 270
                                icon = folium.Icon(angle=icon_angle, **kw)
                                folium.Marker(
                                    location=point,
                                    icon=icon,
                                    popup=html,
                                    color="pink",
                                ).add_to(Map)

                            kwargs = {"color": "red"}
                            intersection_centroid = Polygon(intersection).centroid
                            if intersection_centroid:  # TODO: take a deep look when this shit happens
                                intersection_centroid = [
                                    intersection_centroid.x,
                                    intersection_centroid.y,
                                ]

                            folium.PolyLine(
                                [intersection_centroid, point],
                                tooltip=f"coverage percentage: {access_point['coverage_percent']}",
                                opacity=0.3,
                                **kwargs,
                            ).add_to(Map)

                            folium.Polygon(
                                locations=intersection,
                                weight=0.3,
                                fill_opacity=0.01,
                                # tooltip=f"intersection {index + 1}",
                                fill=True,
                                **kwargs,
                            ).add_to(Map)
    return accesses_for_demands


flights = [flight1, flight2]
res: dict[str, dict] = calculation(flights, demands)
print("FINSHED CALCULATION")
import branca

from tryMe import generate_plots_base64_with_gsd_text


def is_empty(los_gsd):
    values = los_gsd.values()
    return all(value["GSD"] == float("inf") for value in values)


def show_demand_detail(res: dict, fligths):
    for index, demand in enumerate(demands, 1):
        html_parts = []
        encoded_images = []
        has_access_for_demand: dict = res.get(demand.id, False)
        if has_access_for_demand:
            for flight in fligths:
                has_accesses_for_flight: list = has_access_for_demand.get(flight.id, False)
                if has_accesses_for_flight:
                    for access in has_accesses_for_flight:
                        # For each access we really add, we want to see the gsd, los
                        los_gsd_obj = access["LOS_GSD"]
                        if is_empty(los_gsd_obj):
                            continue
                        base64_plots = generate_plots_base64_with_gsd_text(los_gsd_obj)
                        encoded_images.append(base64_plots)

                for i, encoded_image in enumerate(encoded_images, start=1):
                    html_parts.append(f"<h2>Demand:{demand.id} flight:{flight.id}</h2>")
                    image_src = f"data:image/png;base64,{encoded_image}"
                    html_parts.append(f'<img src="{image_src}" width="300" height="300"><br>')

        demand_centroid = Polygon(demand.polygon).centroid
        if demand_centroid:
            demand_centroid = [
                demand_centroid.x,
                demand_centroid.y,
            ]
        folium.PolyLine(
            locations=[demand_centroid, [demand_centroid[0] - index, demand_centroid[1] - index]]
        ).add_to(Map)

        html_content = "".join(html_parts)
        iframe = branca.element.IFrame(html=html_content, width=800, height=800)
        popup = folium.Popup(iframe, max_width=800)
        folium.Marker([demand_centroid[0] - index, demand_centroid[1] - index], popup=popup).add_to(Map)


show_demand_detail(res, flights)

# show_demand_detail(res)
# from tryMe import larger_gsd_values
#
# for p in larger_gsd_values:
#     kw = {
#         "prefix": "fa",
#         "color": "pink",
#         "icon": "card",
#     }
#     icon_angle = 270
#     icon = folium.Icon(angle=icon_angle, **kw)
#     folium.Marker(
#         location=p["point"],
#         icon=icon,
#         tooltip=p["GSD"],
#         color="pink",
#     ).add_to(Map)

print("I AM HERE!!!")
Map.save("flight_path_map.html")
print("FINISHED")
