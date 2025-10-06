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
values_matrix = raw_df.iloc[1:, 1:].astype(float).values

# Create long-format DataFrame
points = []
for i, y in enumerate(md_over_C):
    for j, x in enumerate(m_over_C):
        val = values_matrix[i, j]
        if np.isnan(val):
            continue
        label = "PFAS" if val >= 1.5 else "OC"
        points.append({"m/C": x, "MD/C": y, "Score": val, "Class": label})

df = pd.DataFrame(points)
pfas = df[df["Class"] == "PFAS"]

# === Plot and Extract KDE Boundary ===
fig, ax = plt.subplots(figsize=(8, 6))

kde = sns.kdeplot(
    data=pfas,
    x="m/C",
    y="MD/C",
    levels=[0.05],
    fill=False,
    linewidth=2,
    linestyles="--",
    color="blue",
    ax=ax,
)

# === Extract Contour Coordinates ===
contour_path = None
for collection in kde.collections:
    if collection.get_paths():
        # Assume the first path is the 90% contour
        contour_path = collection.get_paths()[0]
        break

if contour_path:
    vertices = contour_path.vertices
    contour_df = pd.DataFrame(vertices, columns=["m/C", "MD/C"])

    # Save to CSV
    output_csv = r"PIMMS v1.2\CEF_reading\PFAS_90_percent_KDE_boundary.csv"
    contour_df.to_csv(output_csv, index=False)
    print(f"[INFO] 90% KDE boundary exported to: {output_csv}")
else:
    print("[ERROR] No contour path found.")
