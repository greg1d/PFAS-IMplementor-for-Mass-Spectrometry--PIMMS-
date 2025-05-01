import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# === Load Data ===
file_path = r"figures\Raw_data_for_regression_analysis_figure.csv"
match_file_path = r"PIMMS v1.2\Data_output\PIMMS Processed Data set.csv"
data = pd.read_csv(file_path)
match_data = pd.read_csv(match_file_path)

# Get list of IDs to highlight
match_ids = match_data["ID"].apply(lambda x: str(int(float(x)))).tolist()

# === Compute condition based on RT bounds ===
data["Condition"] = data.apply(
    lambda row: (
        -50.3742 + 9.3733 * np.log(row["m/z"])
        <= row["RT"]
        <= -23.6289 + 5.6657 * np.log(row["m/z"])
    ),
    axis=1,
)

# === Create meshgrid for shaded region ===
mz_vals = np.linspace(50, 1000, 200)
ccs_vals = np.linspace(data["CCS"].min(), data["CCS"].max(), 50)
MZ, CCS = np.meshgrid(mz_vals, ccs_vals)
LN_MZ = np.log(MZ)
RT_upper = -23.6289 + 5.6657 * LN_MZ
RT_lower = -50.3742 + 9.3733 * LN_MZ

# === Plot Setup ===
fig = plt.figure(figsize=(10, 6))
ax = fig.add_subplot(111, projection="3d")

# === Plot RT boundary surfaces ===
ax.plot_surface(MZ, CCS, RT_upper, color="blue", alpha=0.3, edgecolor="none")
ax.plot_surface(MZ, CCS, RT_lower, color="red", alpha=0.3, edgecolor="none")

# === Plot points with logic based on Condition ===
marker_size = 10

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
            ax.scatter(mz, ccs, rt, color="black", s=marker_size, alpha=1)
        else:
            ax.scatter(mz, ccs, rt, color="red", s=marker_size, alpha=0.5)

# === Labels and Aesthetics ===
ax.set_xlabel(r"$\mathbfit{m/z}$", fontsize=10, fontweight="bold")
ax.set_ylabel("CCS (Å$^2$)", fontsize=10, fontweight="bold")
ax.set_zlabel("RT (s)", fontsize=10, fontweight="bold")
ax.set_title("3D RT Cone with Condition-Based Coloring", fontsize=12, fontweight="bold")
ax.view_init(elev=25, azim=135)
ax.tick_params(labelsize=9)

plt.tight_layout()
plt.show()
