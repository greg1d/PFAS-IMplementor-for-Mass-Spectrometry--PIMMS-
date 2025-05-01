import matplotlib.pyplot as plt
import pandas as pd

# === Read the main data ===
file_path = r"figures\Raw_data_for_regression_analysis_figure.csv"
data = pd.read_csv(file_path)

# === Read the file containing IDs to highlight ===
match_file_path = r"PIMMS v1.2\Data_output\PIMMS Processed Data set.csv"
match_data = pd.read_csv(match_file_path)
match_ids = match_data["ID"].apply(lambda x: str(int(float(x)))).tolist()

# Add a new column based on the condition
data["Condition"] = data.apply(
    lambda row: row["m/z"] * 0.19 + 110.28 > row["CCS"], axis=1
)

# === Create 3D figure ===
fig = plt.figure(figsize=(8, 5))
ax = fig.add_subplot(111, projection="3d")

# Shrink all points
marker_size = 10

# Plot points
for idx, row in data.iterrows():
    mz = row["m/z"]
    ccs = row["CCS"]
    rt = row["RT"]
    id_ = str(int(float(row["ID"])))

    if id_ in match_ids:
        ax.scatter(
            mz, ccs, rt, color="black", marker="x", s=100, linewidths=1.5, zorder=5
        )
    else:
        if row["Condition"]:
            ax.scatter(
                mz, ccs, rt, facecolors="none", edgecolors="k", s=marker_size, alpha=0.5
            )
        else:
            ax.scatter(mz, ccs, rt, color="k", s=marker_size, alpha=0.5)

# === Labeling and aesthetics ===
ax.set_xlabel(r"$\mathbfit{m/z}$", fontsize=10, fontweight="bold", labelpad=10)
ax.set_ylabel(r"CCS (Å$^2$)", fontsize=10, fontweight="bold", labelpad=10)
ax.set_zlabel("RT (s)", fontsize=10, fontweight="bold", labelpad=10)

ax.tick_params(axis="both", labelsize=9)
ax.tick_params(axis="z", labelsize=9)

plt.tight_layout()
plt.show()
