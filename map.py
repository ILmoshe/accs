"""
PathLayer
=========

Locations of the Bay Area Rapid Transit lines.
"""
import random

import pandas as pd
import pydeck as pdk

from data.polyline import *


def generate_random_colors(num_colors):
    colors = []

    for _ in range(num_colors):
        red = random.randint(0, 150)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)

        hex_color = f"#{red:02x}{green:02x}{blue:02x}"
        colors.append(hex_color)

    return colors


def create_path_data(path, name, color):
    path_result = {}
    path_result["name"] = name
    path_result["color"] = color
    path_result["path"] = path
    return path_result


def create_paths():
    paths = [swap(haifa_to_lebanon), swap(circle), swap(fl3)]
    names = ["haifa_to_lebanon", "circle", "fl3"]
    colors = generate_random_colors(3)

    result = []
    for path, name, color in zip(paths, names, colors):
        result.append(create_path_data(path, name, color))

    return result


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


df = pd.DataFrame(create_paths())
df["color"] = df["color"].apply(hex_to_rgb)

view_state = pdk.ViewState(latitude=32.7526326, longitude=35.0701214, zoom=10)

layer = pdk.Layer(
    type="PathLayer",
    data=df,
    pickable=True,
    get_color="color",
    width_scale=20,
    width_min_pixels=6,
    get_path="path",
    get_width=6,
)

r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{name}"})
r.to_html("path_layer.html")
