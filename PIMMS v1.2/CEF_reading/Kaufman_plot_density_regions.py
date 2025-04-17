import pandas as pd
import matplotlib.pyplot as plt

# === File path ===
file_path = r"PIMMS v1.2\CEF_reading\Kaufman_density_plot_test.csv"

# === Load raw data (no headers) ===
raw_df = pd.read_csv(file_path, header=None)

# === Extract axis labels ===
m_over_C = raw_df.iloc[0, 1:].astype(float).values  # X-axis
md_over_C = raw_df.iloc[1:, 0].astype(float).values  # Y-axis

# === Extract values matrix ===
values_matrix = raw_df.iloc[1:, 1:].astype(float).values

# === Flatten into long format dataframe ===
points = []
for i, y_val in enumerate(md_over_C):
    for j, x_val in enumerate(m_over_C):
        score = values_matrix[i, j]
        label = "PFAS" if score >= 1.5 else "OC"
        points.append({"m/C": x_val, "MD/C": y_val, "Class": label})

df_long = pd.DataFrame(points)

# === Plotting ===
colors = {"PFAS": "dodgerblue", "OC": "darkorange"}
plt.figure(figsize=(7, 5))

for label, group in df_long.groupby("Class"):
    plt.scatter(group["m/C"], group["MD/C"], label=label, color=colors[label], s=20)

# Autoscale x/y limits
plt.xlim(df_long["m/C"].min(), df_long["m/C"].max())
plt.ylim(df_long["MD/C"].min(), df_long["MD/C"].max())

plt.axvline(1.5, color="gray", linestyle="--", linewidth=1, label="Threshold: 1.5")
plt.xlabel("m / C", fontsize=12, fontweight="bold")
plt.ylabel("md / C", fontsize=12, fontweight="bold")
plt.title("Kaufman Plot: m/C vs MD/C", fontsize=14)
plt.legend()
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.show()
