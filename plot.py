import base64
from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon as MplPolygon


def gsd_to_color(gsd, gsd_min=None, gsd_max=None):
    if gsd == np.inf:
        return "grey"
    normalized = (gsd - gsd_min) / (gsd_max - gsd_min) if gsd_max > gsd_min else 0
    return (1 - normalized, normalized, 0)


def generate_plots_base64_with_gsd_text(data):
    # Extract finite GSD values for color mapping
    finite_gsd_values = [val["GSD"] for val in data.values() if val["GSD"] != np.inf]
    # Set gsd_min and gsd_max based on the finite values or use default values if the list is empty
    gsd_min, gsd_max = (
        (min(finite_gsd_values), max(finite_gsd_values))
        if finite_gsd_values
        else (0, 1)
    )

    patches_gsd = []
    patches_los = []
    colors_los = []
    gsd_colors = []

    fig, axes = plt.subplots(1, 2, figsize=(14, 7))

    for value in data.values():
        polygon = value["area"]
        mpl_poly = MplPolygon(list(polygon.exterior.coords))
        patches_gsd.append(mpl_poly)
        patches_los.append(mpl_poly)
        colors_los.append("green" if value["LOS"] else "red")
        # Color mapping for GSD values
        gsd_colors.append(
            gsd_to_color(value["GSD"], gsd_min, gsd_max)
            if finite_gsd_values
            else "grey"
        )
        # GSD text
        gsd_text = f"{value['GSD']:.2f}" if value["GSD"] != np.inf else "-1"
        centroid = polygon.centroid.coords[0]
        axes[0].text(
            centroid[0], centroid[1], gsd_text, ha="center", va="center", fontsize=8
        )

    p_gsd = PatchCollection(patches_gsd, alpha=0.4, color=gsd_colors, edgecolor="black")
    axes[0].add_collection(p_gsd)
    axes[0].autoscale_view()
    axes[0].set_title("Ground Sample Distance (GSD)")

    p_los = PatchCollection(patches_los, alpha=0.4, color=colors_los, edgecolor="black")
    axes[1].add_collection(p_los)
    axes[1].autoscale_view()
    axes[1].set_title("Line of Sight (LOS)")

    for ax in axes:
        ax.set_aspect("equal")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")

    plt.tight_layout()

    img_data = BytesIO()
    plt.savefig(img_data, format="png", bbox_inches="tight")
    plt.close()
    img_data.seek(0)
    base64_data = base64.b64encode(img_data.read()).decode("utf8")

    return base64_data
