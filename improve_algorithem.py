import geopandas as gpd
from pyproj import Geod, Transformer
from shapely.geometry import LineString, Point

# Load flight path and demands data
flight_path = gpd.read_file("flight_path.geojson")
demands = gpd.read_file("demands.geojson")

# Create a geodesic object for accurate distance calculations
geod = Geod(ellps="WGS84")


# Function to create a buffer around a point with a geodesic radius
def geodesic_buffer(point, radius):
    start_point = Point(point.x, point.y)
    end_point = geod.direct(point.x, point.y, point.x + radius, point.y)
    return LineString([start_point, end_point]).buffer(radius)


def find_casing_intersections(flight_path, demand):
    # Define geodesic object for accurate calculations
    geod = Geod(ellps="WGS84")

    # Choose a suitable planar projection for your region
    projection = "EPSG:3857"  # Example: Web Mercator

    # Create a transformer for projections
    transformer = Transformer.from_crs("EPSG:4326", projection, always_xy=True)

    # Project flight path and demand to planar projection
    flight_path_projected = flight_path.to_crs(projection)
    demand_projected = demand.to_crs(projection)

    # Create casing with geodesic buffers and simplification
    flight_casing_buffers = flight_path_projected.geometry.apply(
        lambda g: geodesic_buffer(g, 12000)
    ).simplify(tolerance=50)
    flight_casing = flight_casing_buffers.unary_union

    # Find intersections with demand polygon
    intersections_projected = flight_casing.intersection(demand_projected.geometry)
    intersections = transformer.transform(intersections_projected)  # Project back to WGS84

    return intersections


# Define the geodesic buffer function
def geodesic_buffer(point, radius):
    start_point = Point(point.x, point.y)
    end_point = geod.direct(point.x, point.y, point.x + radius, point.y)
    return LineString([start_point, end_point]).buffer(radius)


# Function to find closest flight path point to an intersection
def find_closest_flight_point(flight_path, intersection):
    closest_distance = float("inf")
    closest_point = None
    for idx, point in flight_path.iterrows():
        distance = geod.inv(point.geometry.x, point.geometry.y, intersection.x, intersection.y)[2]
        if distance < closest_distance:
            closest_distance = distance
            closest_point = point
    return closest_point


# Iterate over demands
for idx, demand in demands.iterrows():
    intersections = find_casing_intersections(flight_path, demand)

    access_times = []

    for intersection in intersections:
        closest_point = find_closest_flight_point(flight_path, intersection)
        current_time = closest_point["timestamp"]

        # Extend access times in both directions while within range
        while True:
            # Check for intersection with geodesic circle
            if geodesic_buffer(closest_point.geometry, 10000).intersects(demand.geometry):
                access_times.append([current_time, closest_point["timestamp"]])
                closest_point = flight_path.iloc[closest_point.name + 1]  # Move to next point
                current_time = closest_point["timestamp"]
            else:
                break

        # Extend access times in the backward direction
        closest_point = flight_path.iloc[closest_point.name - 1]  # Move to previous point
        current_time = closest_point["timestamp"]
        while True:
            # Check for intersection with geodesic circle
            if geodesic_buffer(closest_point.geometry, 10000).intersects(demand.geometry):
                access_times.append([current_time, closest_point["timestamp"]])
                closest_point = flight_path.iloc[closest_point.name - 1]  # Move to previous point
                current_time = closest_point["timestamp"]
            else:
                break

    # Process and store access times for the demand
    # ... (e.g., merge overlapping access times, handle edge cases)
