import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D


def plot_3d_azimuth_elevation(azimuth, elevation):
    # Convert degrees to radians
    azimuth_rad = np.radians(azimuth)
    elevation_rad = np.radians(elevation)

    # Calculate Cartesian coordinates from azimuth and elevation
    x = np.cos(azimuth_rad) * np.cos(elevation_rad)
    y = np.sin(azimuth_rad) * np.cos(elevation_rad)
    z = np.sin(elevation_rad)

    # Create 3D plot
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    # Plot a point representing azimuth and elevation
    ax.scatter(x, y, z, marker="o", s=100, label="Object")

    # Set labels
    ax.set_xlabel("X-axis")
    ax.set_ylabel("Y-axis")
    ax.set_zlabel("Z-axis")

    # Set the azimuth and elevation title
    ax.set_title(f"Azimuth: {azimuth}°, Elevation: {elevation}°")

    # Add legend
    ax.legend()

    # Show the 3D plot
    plt.show()


# Example azimuth and elevation angles
azimuth_angle = 45
elevation_angle = 0

# Generate the 3D plot
plot_3d_azimuth_elevation(azimuth_angle, elevation_angle)
