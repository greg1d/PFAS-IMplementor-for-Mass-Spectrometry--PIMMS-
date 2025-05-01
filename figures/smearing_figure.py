import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter

# Load and clean data
file_path = r"presentations\smearing_raw_data.csv"
df = pd.read_csv(file_path)
df = df[["Mass", "Drift", "Abundance"]].dropna()

# Extract data
x = df["Mass"].values
y = df["Drift"].values
z = df["Abundance"].values

# Create fine grid
xi = np.linspace(x.min(), x.max(), 300)
yi = np.linspace(y.min(), y.max(), 300)
X, Y = np.meshgrid(xi, yi)

# Interpolate using 'linear' or 'cubic' (smoother)
Z = griddata((x, y), z, (X, Y), method="linear")

# Replace any NaNs with 0 for plotting
Z = np.nan_to_num(Z)
Z = gaussian_filter(Z, sigma=7)

# Plot
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection="3d")
surf = ax.plot_surface(
    X,
    Y,
    Z,
    cmap="Greys",
    edgecolor="k",
    linewidth=0.1,
    antialiased=True,
    vmin=Z.min(),  # Lower threshold (darken more of the surface)
    vmax=np.percentile(Z, 99),  # Compress upper range to enhance contrast
)

# Axis labeling
ax.set_xlabel(
    r"$\mathbfit{m/z}$",
    fontsize=10,
    fontfamily="Arial",
    fontweight="bold",
)
ax.set_ylabel(
    r"CCS (Å$^2$)",
    fontsize=10,
    fontfamily="Arial",
    fontweight="bold",
)
ax.zaxis.set_tick_params(pad=10)  # Try 10, adjust higher if needed

ax.set_zlabel(
    "Abundance (count)",
    fontsize=10,
    fontfamily="Arial",
    fontweight="bold",
    labelpad=15,
)

plt.tight_layout()
plt.show()
