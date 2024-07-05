from loguru import logger

from data.polygon import *
from data.polyline import *
from map import Map, add_polyline
from src import Flight, Sensor
from util import add_demands_to_map, calculation, show_demand_detail

add_polyline(haifa_to_lebanon, color="red")
# folium.PolyLine(haifa_to_lebanon, tooltip="Flight path").add_to(Map)
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

add_polyline(circle, color="blue")
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

add_polyline(fl3, color="yellow")
sensor2 = Sensor(width_mm=69, height_mm=54, focal_length_mm=300, image_width_px=14_000)
flight3 = Flight(
    id="third",
    height_meters=5000,
    path=fl3,
    path_case=fl3,
    camera_elevation_start=80,
    camera_elevation_end=120,
    camera_azimuth=1,
    sensor=sensor2,
    speed_km_h=1000,
)


def main():
    # creating the demands
    demands = add_demands_to_map(
        demand_near_sea,
        # demand_not_near_sea,
        demand_in_middle,
        # demand_huge_near_sea,
        # not_sure_demand,
        # fullone,
        # long_demand,
        near_haifa,
        # Even,
        Idan,
    )
    flights = [flight1, flight2, flight3]
    res = calculation(flights, demands)
    logger.info("FINSHED CALCULATION")

    show_demand_detail(res, flights, demands)
    Map.save("flight_path_map.html")
    logger.info("FINISHED")


main()
