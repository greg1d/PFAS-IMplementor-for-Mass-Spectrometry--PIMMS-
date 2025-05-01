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

# === Compute RT bounds ===
mz_vals = np.linspace(0, 1000, 500)
rt_upper = -23.6289 + 5.6657 * np.log(np.clip(mz_vals, 1e-5, None))  # avoid log(0)
rt_lower = -50.3742 + 9.3733 * np.log(np.clip(mz_vals, 1e-5, None))

# === Plot Setup ===
plt.figure(figsize=(3.3, 4.326))
ax = plt.gca()

# === Shade between RT bounds ===
ax.fill_between(mz_vals, rt_lower, rt_upper, color="gray", alpha=0.3)

# === Plot points with logic based on Condition ===
marker_size = 10
for idx, row in data.iterrows():
    mz = row["m/z"]
    rt = row["RT"]
    id_ = str(int(float(row["ID"])))

    if row["Condition"]:
        plt.scatter(mz, rt, facecolors="none", edgecolors="k", s=marker_size, alpha=0.5)
    else:
        plt.scatter(mz, rt, color="k", s=marker_size, alpha=0.5)
    # === Count points inside vs outside bounds ===
inside_count = data["Condition"].sum()
outside_count = (~data["Condition"]).sum()
print("\n--- RT Bound Summary ---")
print(f"Points inside RT bounds: {inside_count}")
print(f"Points outside RT bounds: {outside_count}")
# === Axis formatting to match your original plot ===
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(2)
ax.spines["bottom"].set_linewidth(2)

ax.set_xlabel(r"$\mathbfit{m/z}$", fontsize=10, fontfamily="Arial", fontweight="bold")
ax.set_ylabel(
    "Retention Time (minutes)", fontsize=10, fontfamily="Arial", fontweight="bold"
)

ax.set_xlim(0, 1000)
ax.set_ylim(data["RT"].min() - 1, data["RT"].max() + 1)  # Auto range for RT

ax.tick_params(axis="both", which="both", labelsize=9)
for label in ax.get_xticklabels() + ax.get_yticklabels():
    label.set_fontname("Arial")
    label.set_weight("bold")

plt.tight_layout()
plt.show()
