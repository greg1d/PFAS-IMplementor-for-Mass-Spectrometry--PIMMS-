import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# === Load Kaufman plot data ===
file_path = r"PIMMS v1.2\CEF_reading\Kaufman_density_plot.csv"
raw_df = pd.read_csv(file_path, header=None)

# Extract axes
m_over_C = raw_df.iloc[0, 1:].astype(float).values
md_over_C = raw_df.iloc[1:, 0].astype(float).values
values_matrix = raw_df.iloc[1:, 1:].apply(pd.to_numeric, errors="coerce").values

# Build long-format DataFrame
points = []
for i, y in enumerate(md_over_C):
    for j, x in enumerate(m_over_C):
        val = values_matrix[i, j]
        if np.isnan(val):
            label = "NA"
        elif val >= 1.5:
            label = "PFAS"
        else:
            label = "OC"
        points.append({"m/C": x, "MD/C": y, "Score": val, "Class": label})

df = pd.DataFrame(points)

# === Split by class ===
pfas = df[df["Class"] == "PFAS"]
ocs = df[df["Class"] == "OC"]
nas = df[df["Class"] == "NA"]

# === Plot Setup ===
plt.figure(figsize=(5, 5))
ax = plt.gca()

# Plot OC and PFAS as translucent diamonds
sns.scatterplot(
    data=ocs,
    x="m/C",
    y="MD/C",
    color="blue",  # red
    edgecolor=None,
    label="OC",
    s=30,
    alpha=0.5,
    marker="o",
)
sns.scatterplot(
    data=pfas,
    x="m/C",
    y="MD/C",
    color="red",  # green
    edgecolor=None,
    label="PFAS",
    s=30,
    alpha=0.5,
    marker="o",
)

# Plot NA as white hollow diamonds
plt.scatter(
    nas["m/C"],
    nas["MD/C"],
    color="white",
    edgecolor="white",
    s=0,
    marker="o",
    label="Missing (NA)",
)

# Plot 90% KDE contour for PFAS
sns.kdeplot(
    data=pfas,
    x="m/C",
    y="MD/C",
    levels=[0.10, 1.0],
    color="red",
    fill=True,
    alpha=0.4,
    linewidth=0,
)


# === Style the plot ===
plt.xlabel("m / C", fontsize=10, fontweight="bold")
plt.ylabel("md / C", fontsize=10, fontweight="bold")
plt.xticks(fontsize=9)
plt.yticks(fontsize=9)
plt.grid(False)
plt.legend(frameon=False, fontsize=9)
plt.tight_layout()
plt.show()
