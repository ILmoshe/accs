from data.polyline import haifa_to_lebanon

import folium.plugins
import arrow

start_latitude = 32.7526326
start_longitude = 35.0701214


def add_time(coord):
    utc = arrow.utcnow()

    return [(point, utc.shift(minutes=index + 2).format()) for index, point in enumerate(coord)]


Map = folium.Map(
    location=[start_latitude, start_longitude], zoom_start=8, tiles="cartodb positron"
)

lat_lon_haifa_to_lebanon: list[[float, float]] = [
    [coord[1], coord[0]] for coord in haifa_to_lebanon
]

folium.PolyLine(lat_lon_haifa_to_lebanon, tooltip="Flight path").add_to(Map)

kw = {"prefix": "fa", "color": "red", "icon": "plane"}
angle = 270

with_time = add_time(haifa_to_lebanon)
for (long, lat), time in with_time:
    icon = folium.Icon(angle=angle, **kw)
    folium.Marker(location=[lat, long], icon=icon, tooltip=str((lat, long, time)), ).add_to(Map)

Map.save("flight_path_map.html")
