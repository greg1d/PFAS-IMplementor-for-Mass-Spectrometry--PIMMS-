import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# === Read the main data ===
file_path = r"presentations\raw_data_for_figures.csv"
data = pd.read_csv(file_path)
print(data.head())

# === Read the file containing IDs to highlight ===
match_file_path = r"PIMMS v1.2\Data_output\PIMMS Processed Data set.csv"
match_data = pd.read_csv(match_file_path)
print(data["ID"].astype(str).drop_duplicates().head(10).to_list())
match_ids = match_data["ID"].apply(lambda x: str(int(float(x)))).tolist()
print(match_ids[:10])

# Add a new column based on the condition
data["Condition"] = data.apply(
    lambda row: row["m/z"] * 0.19 + 110.28 > row["CCS"], axis=1
)

# Plot the data
plt.figure(figsize=(7, 4.326))

# Shrink all points
marker_size = 10

# Plot points
for idx, row in data.iterrows():
    mz = row["m/z"]
    ccs = row["CCS"]
    id_ = str(int(float(row["ID"])))  # ensure it matches format in match_ids

    if id_ in match_ids:
        print(f"Matched ID: {id_}")
        plt.scatter(mz, ccs, color="red", marker="x", s=40, linewidths=1.5, zorder=5)
    else:
        if row["Condition"]:
            plt.scatter(mz, ccs, facecolors="none", edgecolors="k", s=marker_size)
        else:
            plt.scatter(mz, ccs, color="k", s=marker_size)

# === Plot condition line ===
mz_values = np.linspace(0, 1000, 500)
ccs_values = mz_values * 0.19 + 110.28

plt.plot(
    mz_values[mz_values <= 180],
    ccs_values[mz_values <= 180],
    "k--",
    label="Condition Line (Black)",
)
plt.plot(
    mz_values[mz_values >= 800],
    ccs_values[mz_values >= 800],
    "k--",
)
plt.plot(
    mz_values[(mz_values > 180) & (mz_values < 800)],
    ccs_values[(mz_values > 180) & (mz_values < 800)],
    "w--",
    label="Condition Line (White)",
)

# === Customize plot aesthetics ===
ax = plt.gca()
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_linewidth(2)
ax.spines["bottom"].set_linewidth(2)

plt.title(
    r"CCS vs $\mathit{m/z}$ cutoff",
    fontsize=10,
    fontfamily="Arial",
    fontweight="bold",
)
plt.xlabel(
    r"$\mathit{m/z}$ (Da)",
    fontsize=10,
    fontfamily="Arial",
    fontweight="bold",
)
plt.ylabel(
    r"CCS (Å$^2$)",
    fontsize=10,
    fontfamily="Arial",
    fontweight="bold",
)

plt.xlim(0, 1000)
plt.ylim(50, 400)

ax.tick_params(axis="both", which="both", labelsize=9)
for label in ax.get_xticklabels() + ax.get_yticklabels():
    label.set_fontname("Arial")
    label.set_weight("bold")

plt.legend()
plt.show()
