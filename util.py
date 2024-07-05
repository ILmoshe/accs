import uuid
from copy import deepcopy

import branca
import folium
from shapely import Polygon

from map import Map
from plot import generate_plots_base64_with_gsd_text
from src import Demand, Flight
from src.logic import (
    calculate_accesses_for_demand,
    calculate_arrival_time,
    create_case_for_flight_path,
)


def add_demand(demand: Demand):
    folium.Polygon(demand.polygon, tooltip=demand.id, color="red", weight=1).add_to(Map)

    return demand


def add_demands_to_map(*demands: list[list[float, float]]):
    return [add_demand(Demand(id=str(uuid.uuid4()).split("-")[0], polygon=demand)) for demand in demands]


def show_demand_detail(res: dict, fligths, demands):
    for index, demand in enumerate(demands, 1):
        html_parts = []
        has_access_for_demand: dict = res.get(demand.id, False)
        if has_access_for_demand:
            for flight in fligths:
                encoded_images = []
                has_accesses_for_flight: list = has_access_for_demand.get(flight.id, False)
                if has_accesses_for_flight:
                    for access in has_accesses_for_flight:
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
            locations=[
                demand_centroid,
                [demand_centroid[0] - index, demand_centroid[1] - index],
            ],
            color="white",
            opacity=0.1,
        ).add_to(Map)

        html_content = "".join(html_parts)
        iframe = branca.element.IFrame(html=html_content, width=800, height=800)
        popup = folium.Popup(iframe, max_width=800)
        folium.Marker([demand_centroid[0] - index, demand_centroid[1] - index], popup=popup).add_to(Map)


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


def calculation(flights: list[Flight], demands: list[Demand]):
    accesses_for_demands = {}
    for flight in flights:
        accesses_along_a_fligth_path = []
        base_case = create_case_for_flight_path(flight)
        draw_base_caseing_on_map((case["case_polygon"] for case in base_case), Map)

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
                                # kw = {
                                #     "prefix": "fa",
                                #     "color": "pink",
                                #     "icon": "card",
                                # }
                                # icon_angle = 270
                                # icon = folium.Icon(angle=icon_angle, **kw)
                                # folium.Marker(
                                #     location=point,
                                #     icon=icon,
                                #     popup=html,
                                #     color="pink",
                                # ).add_to(Map)

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
                                fill=True,
                                **kwargs,
                            ).add_to(Map)
    return accesses_for_demands


def is_empty(los_gsd):
    values = los_gsd.values()
    return all(value["GSD"] == float("inf") for value in values)
