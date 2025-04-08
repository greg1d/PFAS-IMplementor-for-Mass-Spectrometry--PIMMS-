import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# Load CSV
file_path = (
    r"PIMMS Validation work\Comparison test output\All analytes comparison master.csv"
)
df = pd.read_csv(file_path)

# Extract relevant columns
x = df["Skyline (post blank subtraction)"]
y = df["Profiler (post blank subtraction)"]

x[x < 0] = 0
y[y < 0] = 0
# Determine conditions
true_neg = (x == 0) & (y == 0)
true_pos = (y > 0) & (x > 0)
false_neg = (y == 0) & (x > 0)
false_pos = (y > 0) & (x == 0)
# Convert negatives to 0

# Print counts
print("True Positives:", true_pos.sum())
print("True Negatives:", true_neg.sum())
print("False Positives:", false_pos.sum())
print("False Negatives:", false_neg.sum())
# Determine conditions
true_conditions = ((y == 0) & (x == 0)) | ((x > 0) & (y > 0))
false_conditions = ~true_conditions

# Plot main figure
fig, ax = plt.subplots(figsize=(3.5, 4))
ax.scatter(
    x[true_conditions], y[true_conditions], color="green", label="True", alpha=0.6
)
ax.scatter(
    x[false_conditions], y[false_conditions], color="red", label="False", alpha=0.6
)

# Log x-axis
ax.set_xlabel(
    "Skyline peak area (×10⁶)", fontsize=10, fontweight="bold", fontname="Arial"
)
ax.set_ylabel(
    "Mass Profiler peak area", fontsize=10, fontweight="bold", fontname="Arial"
)
ax.tick_params(axis="both", width=2)
# Linear trendline and R²
valid_mask = (x > 0) & (y > 0)
x_valid = np.array(x[valid_mask]).reshape(-1, 1)
y_valid = np.array(y[valid_mask])

reg = LinearRegression().fit(x_valid, y_valid)
y_pred = reg.predict(x_valid)
r2 = r2_score(y_valid, y_pred)

x_line = np.linspace(x_valid.min(), x_valid.max(), 100).reshape(-1, 1)
y_line = reg.predict(x_line)
ax.plot(
    x_line,
    y_line,
    color="black",
    alpha=0.7,
    linestyle="--",
    linewidth=1.5,
    label=f"R² = {r2:.2f}",
)
# Display R² value on the plot
ax.text(
    0.80,
    0.80,
    f"R² = {r2:.2f}",
    transform=ax.transAxes,
    fontsize=8,
    fontweight="bold",
    fontname="Arial",
    verticalalignment="top",
    horizontalalignment="left",
)

# Format tick labels
for label in ax.get_xticklabels() + ax.get_yticklabels():
    label.set_fontsize(8)
    label.set_fontname("Arial")
    label.set_fontweight("bold")

# Spine styling
for side in ["left", "bottom"]:
    ax.spines[side].set_linewidth(2)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Inset
axins = inset_axes(
    ax,
    width="40%",
    height="40%",
    bbox_to_anchor=(0.15, 0.7, 0.7, 0.7),  # x0, y0, width, height
    bbox_transform=ax.transAxes,
    loc="lower left",
)
axins.scatter(x[true_conditions], y[true_conditions], color="green", alpha=0.6)
axins.scatter(x[false_conditions], y[false_conditions], color="red", alpha=0.6)
axins.set_xlim(-10000, 80000)
axins.set_ylim(-100, 1500)
axins.tick_params(axis="both", width=2)

# Inset tick label styling
for label in axins.get_xticklabels() + axins.get_yticklabels():
    label.set_fontsize(8)
    label.set_fontname("Arial")
    label.set_fontweight("bold")

# Inset spine styling
for side in ["left", "bottom"]:
    axins.spines[side].set_linewidth(2)
axins.spines["top"].set_visible(False)
axins.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(
    r"PIMMS v1.2\PIMMS Validation Scripts\Performance with peak area all detections post blank subtraction.png",
    dpi=300,
    transparent=True,
    bbox_inches="tight",
)
plt.show()
