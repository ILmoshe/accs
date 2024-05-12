import numpy as np
from geopy.distance import geodesic
from shapely.geometry import Point, Polygon


class LRUCache:
    def __init__(self, capacity: int = 10):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key):
        if key not in self.cache:
            return None
        else:
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)


def read_hgt_file(filename):
    print(f"hgt file name {filename}")
    with open(filename, "rb") as f:
        elevation_data = np.fromfile(f, np.dtype(">i2"), -1).reshape((3601, 3601))
    return elevation_data


def get_elevation(lat, lon, elevation_data):
    lat_row = int((1 - (lat - int(lat))) * 3600)
    lon_row = int((lon - int(lon)) * 3600)
    return elevation_data[lat_row, lon_row]


def get_altitude(points, hgt_files_directory="hgt"):
    loaded_hgt = LRUCache(capacity=20)  # Adjust capacity as needed
    elevation_result = []

    for point in points:
        try:
            lat, lon = point.lat, point.long
        except AttributeError:
            lat, lon = (point[0], point[1])
        hgt_file = f"{hgt_files_directory}/N{int(lat):02d}E{int(lon):03d}.hgt"
        if not os.path.isfile(hgt_file):
            elevation_result.append(0.0)
            continue
        elevation_data = loaded_hgt.get(hgt_file)
        if elevation_data is None:
            elevation_data = read_hgt_file(hgt_file)
            loaded_hgt.put(hgt_file, elevation_data)

        elevation_result.append(get_elevation(lat, lon, elevation_data))

    points_result = []
    for point, elevation in zip(points, elevation_result):
        try:
            points_result.append(Point(point.lat, point.long, elevation))
        except AttributeError:
            points_result.append([point[0], point[1], elevation])

    return points_result


class Flight(BaseModel):
    id: str = "flight_id"
    height_meters: float
    speed_km_h: float
    path_case: list[list]
    path: list[list]
    camera_azimuth: float
    camera_elevation_start: int
    camera_elevation_end: int
    sensor: Sensor


def create_grid_polygons(polygon: Polygon | Any, cell_size: float):
    polygon = Polygon(polygon)

    minx, miny, maxx, maxy = polygon.bounds
    grid_polygons = {}

    print(len(np.arange(minx, maxx, cell_size)))
    print(len(np.arange(miny, maxy, cell_size)))
    for x in np.arange(minx, maxx, cell_size):
        for y in np.arange(miny, maxy, cell_size):
            # Define the current cell as a polygon (box)
            cell = box(x, y, x + cell_size, y + cell_size)

            if cell.intersects(polygon):
                # Clip the cell to the input polygon (to handle partial overlaps)
                clipped_cell: Polygon = cell.intersection(polygon)
                lat = clipped_cell.centroid.x
                long = clipped_cell.centroid.y
                [point_with_alt] = get_altitude([Point(lat, long)])
                p_x, p_y, p_z = (point_with_alt.lat, point_with_alt.long, point_with_alt.alt)
                grid_polygons[p_x, p_y, p_z] = {"area": clipped_cell, "GSD": float("inf"), "LOS": False}

    return grid_polygons


class Demand(BaseModel):
    id: str
    polygon: list[tuple[float, float]]
    allowed_azimuth: dict[str, float] = {"from": 0, "to": 360}
    allowed_elevation: dict[str, float] = {"from": -90, "to": 90}

    demand_inner_calculation: Optional[dict[str, dict[str, Any | float | bool]]] = None

    @model_validator(mode="after")
    def prepare_demand(self) -> Self:
        self.demand_inner_calculation = create_grid_polygons(
            self.polygon, 0.015
        )  # we will have to see which size is the appropriate cell size
        return self


def get_z_value_from_line(p1, p2, x, y):
    """
    Parameters:
        p1 (array_like): The first point (x1, y1, z1) defining the line.
        p2 (array_like): The second point (x2, y2, z2) defining the line.
        x (float): The x value for which to find the corresponding z value.
        y (float): The y value for which to find the corresponding z value.

    Returns:
        float: The z value corresponding to the given x and y on the line.
    """
    p1 = np.array(p1)
    p2 = np.array(p2)

    # Direction vector from p1 to p2
    d = p2 - p1

    # Handle cases where the line is parallel to one of the axes
    if d[0] == 0 and d[1] == 0:
        raise ValueError("The line is parallel to the z-axis; x and y values must match p1 or p2.")

    # Calculate parameter t
    t = np.where(d[0] != 0, (x - p1[0]) / d[0], (y - p1[1]) / d[1])

    # Calculate z using parameter t
    z = p1[2] + t * d[2]

    return z


def points_along_line(lat1, lon1, lat2, lon2, interval_distance):
    """
    Calculate points along the line connecting two points
    at specified intervals.
    """
    # Calculate total distance between two points in meters
    total_distance = geodesic((lat1, lon1), (lat2, lon2)).meters

    # Calculate the number of segments
    num_segments = int(total_distance / interval_distance)

    # Calculate the fraction to divide the latitude and longitude differences by
    lat_diff = lat2 - lat1
    lon_diff = lon2 - lon1
    lat_fraction = lat_diff / num_segments
    lon_fraction = lon_diff / num_segments

    # Generate points at specified intervals
    points = [(lat1 + i * lat_fraction, lon1 + i * lon_fraction) for i in range(num_segments)]

    return points


def put_LOS_into_demand(demand: Demand, point_with_alt: list[float], related_centroids: list) -> None:
    for related_centroid in related_centroids:
        if demand.demand_inner_calculation[related_centroid]["LOS"]:  # We already have LOS there
            continue

        points_on_line = points_along_line(
            point_with_alt[0], point_with_alt[1], related_centroid[0], related_centroid[1], 200
        )
        len_points_on_line = len(points_on_line)
        for index, point in enumerate(points_on_line, 1):
            equation_alt = get_z_value_from_line(point_with_alt, related_centroid, point[0], point[1])
            [real_point] = get_altitude([point])
            if real_point[2] > equation_alt:  # We don't have line of sight !
                break  # leave current centroid, unfortunately we didn't find

            if index == len_points_on_line:  # We checked all the way and we have LOS
                demand.demand_inner_calculation[related_centroid]["LOS"] = True
