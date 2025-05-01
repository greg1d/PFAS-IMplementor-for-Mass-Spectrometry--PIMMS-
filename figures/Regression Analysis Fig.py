import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# === Load Data ===
file_path = r"figures\Raw_data_for_regression_analysis_figure.csv"
data = pd.read_csv(file_path)

# === Define m/z and CCS grid for cone surface ===
mz_vals = np.linspace(50, 1000, 200)
ccs_vals = np.linspace(data["CCS"].min(), data["CCS"].max(), 50)
MZ, CCS = np.meshgrid(mz_vals, ccs_vals)
LN_MZ = np.log(MZ)

# Compute RT surface bounds
RT_upper = -50.3742 + 9.3733 * LN_MZ
RT_lower = -23.6289 + 5.6657 * LN_MZ

# === Plot Setup ===
fig = plt.figure(figsize=(10, 6))
ax = fig.add_subplot(111, projection="3d")

# === Plot surfaces to define the "cone" ===
ax.plot_surface(MZ, CCS, RT_upper, color="red", alpha=0.3, edgecolor="none")
ax.plot_surface(MZ, CCS, RT_lower, color="blue", alpha=0.3, edgecolor="none")

# === Classify and plot each point ===
for _, row in data.iterrows():
    mz = row["m/z"]
    ccs = row["CCS"]
    rt = row["RT"]
    ln_mz = np.log(mz)

    rt_lo = -23.6289 + 5.6657 * ln_mz
    rt_hi = -50.3742 + 9.3733 * ln_mz

    # Check if RT is within bounds
    if rt_lo <= rt <= rt_hi:
        ax.scatter(mz, ccs, rt, color="black", alpha=1, s=10)
    else:
        ax.scatter(mz, ccs, rt, color="black", alpha=0.5, s=10)

# === Labels and Aesthetics ===
ax.set_xlabel(r"$\mathbfit{m/z}$", fontsize=10, fontweight="bold")
ax.set_ylabel("CCS (Å$^2$)", fontsize=10, fontweight="bold")
ax.set_zlabel("RT (s)", fontsize=10, fontweight="bold")
ax.set_title("3D RT Bound Cone with Data Points", fontsize=12, fontweight="bold")
ax.view_init(elev=25, azim=135)
ax.tick_params(labelsize=9)

plt.tight_layout()
plt.show()
