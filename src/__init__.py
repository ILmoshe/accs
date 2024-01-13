from datetime import datetime, timedelta

import folium
import numpy as np


def generate_flight_vector(
    num_points, start_lat, start_long, end_lat, end_long, curve_factor
):
    coordinates = []
    timestamps = []

    current_lat = start_lat
    current_long = start_long

    delta_lat = (end_lat - start_lat) / num_points
    delta_long = (end_long - start_long) / num_points

    current_time = datetime.utcnow()
    delta_time = timedelta(minutes=1)

    for _ in range(num_points):
        coordinates.append([current_lat, current_long])
        timestamps.append(current_time.isoformat())

        current_lat += delta_lat
        current_long += (
            delta_long
            * (1 - np.cos(np.radians((current_lat + end_lat) / 2)))
            * curve_factor
        )

        current_time += delta_time

    return coordinates, timestamps


# Set parameters for the flight
num_points = 20
start_latitude = 30.0
start_longitude = 34.0
end_latitude = 40.0
end_longitude = 36.0
curve_factor = 0.5  # Adjust this value for the desired curvature (0 to 1)

# Generate flight vector
flight_coordinates, flight_timestamps = generate_flight_vector(
    num_points,
    start_latitude,
    start_longitude,
    end_latitude,
    end_longitude,
    curve_factor,
)

# Create a folium map centered around the starting point
m = folium.Map(location=[start_latitude, start_longitude], zoom_start=6)

# Add the flight path to the map
for coord in flight_coordinates:
    folium.Marker(
        location=[coord[0], coord[1]], icon=folium.Icon(color='blue')
    ).add_to(m)

# Save the map to an HTML file
m.save('flight_path_map.html')
