import numpy as np
import matplotlib.pyplot as plt


def calculate_image_plane(focal_length, sensor_size, azimuth, elevation):
    # Convert azimuth and elevation angles to radians
    azimuth_rad = np.deg2rad(azimuth)
    elevation_rad = np.deg2rad(elevation)

    # Calculate the direction vector of the camera
    direction_vector = np.array(
        [
            np.sin(azimuth_rad) * np.cos(elevation_rad),
            np.cos(azimuth_rad) * np.cos(elevation_rad),
            np.sin(elevation_rad),
        ]
    )

    # Calculate the center of the image plane
    image_plane_center = focal_length * direction_vector

    # Calculate the size of the image plane
    image_plane_size = np.array([sensor_size[0], sensor_size[1]])

    # Calculate the vectors for the corners of the image plane
    half_width = image_plane_size[0] / 2
    half_height = image_plane_size[1] / 2
    corners = np.array(
        [
            [-half_width, -half_height, 0],
            [half_width, -half_height, 0],
            [half_width, half_height, 0],
            [-half_width, half_height, 0],
        ]
    )

    # Rotate the corners to align with the direction vector
    rotation_matrix = np.array(
        [
            [np.cos(azimuth_rad), -np.sin(azimuth_rad), 0],
            [np.sin(azimuth_rad), np.cos(azimuth_rad), 0],
            [0, 0, 1],
        ]
    )
    rotated_corners = np.dot(corners, rotation_matrix.T)

    # Translate the rotated corners to the image plane center
    translated_corners = rotated_corners + image_plane_center

    return translated_corners, image_plane_center, direction_vector


# Example parameters
focal_length = 50  # in millimeters
sensor_size = (36, 24)  # in millimeters, e.g., for full-frame sensor
azimuth = 0  # in degrees
elevation = 0  # in degrees, since the camera projects the x, y, 0 plane

# Calculate the image plane
image_plane, focal_point, direction_vector = calculate_image_plane(
    focal_length, sensor_size, azimuth, elevation
)

# Plot in 3D
fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")

# Plot the image plane
ax.plot(image_plane[:, 0], image_plane[:, 1], image_plane[:, 2], "b-")
ax.plot(
    [image_plane[0, 0], image_plane[1, 0]],
    [image_plane[0, 1], image_plane[1, 1]],
    [image_plane[0, 2], image_plane[1, 2]],
    "r-",
)
ax.plot(
    [image_plane[1, 0], image_plane[2, 0]],
    [image_plane[1, 1], image_plane[2, 1]],
    [image_plane[1, 2], image_plane[2, 2]],
    "r-",
)
ax.plot(
    [image_plane[2, 0], image_plane[3, 0]],
    [image_plane[2, 1], image_plane[3, 1]],
    [image_plane[2, 2], image_plane[3, 2]],
    "r-",
)
ax.plot(
    [image_plane[3, 0], image_plane[0, 0]],
    [image_plane[3, 1], image_plane[0, 1]],
    [image_plane[3, 2], image_plane[0, 2]],
    "r-",
)

# Plot the focal point
ax.scatter(
    focal_point[0],
    focal_point[1],
    focal_point[2],
    c="g",
    marker="o",
    label="Focal Point",
)

# Plot the direction vector
ax.quiver(
    focal_point[0],
    focal_point[1],
    focal_point[2],
    direction_vector[0],
    direction_vector[1],
    direction_vector[2],
    length=20,
    color="orange",
    label="Direction Vector",
)

ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_title("Image Plane, Focal Point, and Direction Vector")
ax.legend()

plt.show()
