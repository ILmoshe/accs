import shapely
from shapely.geometry import Polygon


def convert_multipolygon_to_list(multipolygon: shapely.MultiPolygon):
    result = []
    for polygon in list(multipolygon.geoms):
        converted_polygon = convert_polygon_to_list(polygon)
        result.append(converted_polygon)
    return result


def convert_polygon_to_list(
    shape: shapely.Polygon | shapely.MultiPolygon,
) -> list[tuple[float, float]]:
    try:
        result = [tuple(coord) for coord in shape.exterior.coords]
    except AttributeError:
        result = convert_multipolygon_to_list(shape)
    return result


def calculate_intersection(circle_polygon, demand_polygon):
    demand_polygon = Polygon(demand_polygon)
    circle_polygon = Polygon(circle_polygon)

    intersection = circle_polygon.intersection(demand_polygon)

    intersection_area = intersection.area
    total_polygon_area = demand_polygon.area
    percentage_intersection = (intersection_area / total_polygon_area) * 100.0
    leftover_polygon = demand_polygon.difference(circle_polygon)

    return (
        percentage_intersection,
        convert_polygon_to_list(intersection),
        convert_polygon_to_list(leftover_polygon),
    )


def calculate_intersection_raw(
    circle_polygon, demand_polygon
) -> tuple[float, Polygon, Polygon]:
    demand_polygon = Polygon(demand_polygon)
    circle_polygon = Polygon(circle_polygon)

    intersection: Polygon = circle_polygon.intersection(demand_polygon)

    intersection_area = intersection.area
    total_polygon_area = demand_polygon.area
    percentage_intersection = (intersection_area / total_polygon_area) * 100.0
    leftover_polygon: Polygon = demand_polygon.difference(circle_polygon)

    return (
        percentage_intersection,
        intersection,
        leftover_polygon,
    )
