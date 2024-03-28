import numpy as np
from scipy.spatial import ConvexHull


def minimum_bounding_rectangle(points):
    hull_points = points[ConvexHull(points).vertices]
    return hull_points


def flatten(xss):
    return [x for xs in xss for x in xs]


def calc_continues_fov(
    fov_polygons: list[list[list[float]]],
) -> list[list[float]]:
    flattened = flatten(fov_polygons)
    bounding_box = minimum_bounding_rectangle(np.array(flattened))

    return bounding_box.tolist()
