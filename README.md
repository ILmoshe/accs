# AccS
ACCESS(opportunity) CALCULATION FOR RECON MISSIONS with planes/drones/UAVs.


## Introduction
This repository contains a source code for advanced calculation of camera orientations combined with **GSD**(Ground sample distance) calculation while taking **LOS**(line of sight) into account.

## Installation and Usage
The project works on python 3.11.x <br />
To install the required packages, you can use the following command:

_We recommend using virtual environment to install the required packages._
```bash
python -m venv venv
```

```bash
pip install -r requirements.txt
```

To run the project, you can use the following command:
```bash
python main.py
```

This should generate a `flight_path.html` file with the results.
It should look something like this:

![Screenshot 2024-08-27 115001](https://github.com/user-attachments/assets/d668d739-3c11-463b-a961-c7474ceceec2)


We can see that we have 3 flights, each with a different camera orientation resulting in difference opportunity.
```python
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

sensor3 = Sensor(width_mm=69, height_mm=54, focal_length_mm=300, image_width_px=14_000)
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
```

You can play and change the camera orientations and the flights path to see how it affects the opportunity for the given demands.

In addition to it, you can change the demands in the `main.py` file to see how it affects the opportunity.

```python
    demands = add_demands_to_map(
        demand_near_sea,
        demand_not_near_sea,
        demand_in_middle,
        near_haifa,
        Even,
    )

```
A demand is just a polygon on the map that we want to capture with the camera.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
