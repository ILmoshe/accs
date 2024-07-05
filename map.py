import folium
from folium.plugins import Draw

start_latitude = 32.7526326
start_longitude = 35.0701214


Map = folium.Map(
    location=[start_latitude, start_longitude],
    zoom_start=11,
    tiles="Cartodb dark_matter",
)


def add_polyline(line, color):
    folium.PolyLine(line, tooltip="Flight path", color=color).add_to(Map)


Draw(export=True).add_to(Map)
