import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Aligned Feature m/z values
aligned_mz = np.array(
    [
        146.9807,
        146.9807,
        146.9809,
        146.9809,
        146.981,
        146.981,
        146.981,
        146.9813,
        146.9815,
        146.9818,
        146.9819,
        146.9822,
        146.9826,
        146.9834,
        146.9848,
        147.004,
        147.0271,
        147.0425,
        147.0426,
        147.0428,
        147.0432,
        147.0635,
        147.0785,
        147.0792,
    ]
)

# Aligned Feature CCS values
aligned_ccs = np.array(
    [
        202.77,
        238.43,
        160.43,
        401.1,
        231.97,
        39.46,
        211.42,
        170.76,
        299.76,
        250.4,
        75.87,
        230.42,
        101.35,
        70.07,
        273.36,
        110.28,
        122.39,
        131.41,
        141.11,
        128.03,
        185.92,
        128.57,
        133.79,
        153.91,
    ]
)

# Aligned Feature RT values
aligned_rt = np.array(
    [
        0.246,
        0.369,
        1.208,
        0.663,
        0.623,
        1.608,
        1.876,
        3.007,
        1.642,
        1.686,
        1.046,
        0.926,
        3.694,
        3.413,
        0.904,
        0.787,
        1.471,
        1.558,
        1.933,
        1.017,
        1.641,
        1.391,
        0.64,
        0.529,
    ]
)


# Function to generate noisy data
def generate_noisy_data(aligned_mz, aligned_ccs, aligned_rt, num_samples=100):
    noisy_data = []
    for mz, ccs, rt in zip(aligned_mz, aligned_ccs, aligned_rt):
        samples = []
        for _ in range(num_samples):
            noisy_mz = mz * (1 + np.random.uniform(-10e-6, 10e-6))  # Vary within 10 ppm
            noisy_ccs = ccs * (1 + np.random.uniform(-0.02, 0.02))  # Vary within 2%
            noisy_rt = max(
                0, rt + np.random.uniform(-0.5, 0.5)
            )  # Vary within 0.5, never negative
            samples.append((noisy_mz, noisy_ccs, noisy_rt))
        noisy_data.append(samples)
    return noisy_data


# Generate noisy data
noisy_data = generate_noisy_data(aligned_mz, aligned_ccs, aligned_rt)

# Convert to DataFrame for easier handling
aligned_features = pd.DataFrame(
    {
        "Aligned Feature m/z": aligned_mz,
        "Aligned Feature CCS": aligned_ccs,
        "Aligned Feature RT": aligned_rt,
    }
)

# Flatten the noisy data and create columns for each sample
noisy_data_flat = np.array(noisy_data).reshape(len(aligned_mz), -1)
columns = []
for i in range(noisy_data_flat.shape[1] // 3):
    columns.append(f"Sample {i+1} (m/z)")
    columns.append(f"Sample {i+1} (CCS)")
    columns.append(f"Sample {i+1} (RT)")
noisy_data_df = pd.DataFrame(noisy_data_flat, columns=columns)

# Combine aligned features and noisy data
df_combined = pd.concat([aligned_features, noisy_data_df], axis=1)

# Format m/z to 4 decimal places, CCS to 2 decimal places, and RT to 3 decimal places
df_combined["Aligned Feature m/z"] = df_combined["Aligned Feature m/z"].round(4)
df_combined["Aligned Feature CCS"] = df_combined["Aligned Feature CCS"].round(2)
df_combined["Aligned Feature RT"] = df_combined["Aligned Feature RT"].round(3)
for col in df_combined.columns:
    if "(m/z)" in col:
        df_combined[col] = df_combined[col].round(4)
    elif "(CCS)" in col:
        df_combined[col] = df_combined[col].round(2)
    elif "(RT)" in col:
        df_combined[col] = df_combined[col].round(3)

# Save to a CSV file
df_combined.to_csv("noisy_dataset.csv", index=False)
print("Noisy dataset generated and saved to 'noisy_dataset.csv'")

# Print the first few rows of the combined dataset
print(df_combined.head())

# Plot all the points in a 3D scatter plot, color-coordinated by row
fig = plt.figure(figsize=(10, 6))
ax = fig.add_subplot(111, projection="3d")
cmap = plt.get_cmap("viridis")
num_rows = len(df_combined)
colors = cmap(np.linspace(0, 1, num_rows))

for index, (row, color) in enumerate(zip(df_combined.iterrows(), colors)):
    mz_values = row[1][[col for col in df_combined.columns if "(m/z)" in col]].dropna()
    ccs_values = row[1][[col for col in df_combined.columns if "(CCS)" in col]].dropna()
    rt_values = row[1][[col for col in df_combined.columns if "(RT)" in col]].dropna()
    if len(mz_values) == len(ccs_values) == len(rt_values):
        ax.scatter(
            mz_values, ccs_values, rt_values, label=f"Row {index + 1}", color=color
        )

ax.set_xlabel("m/z")
ax.set_ylabel("CCS")
ax.set_zlabel("RT")
ax.set_title("3D Scatter Plot of m/z, CCS, and RT")
ax.legend()

# Rotate the graph interactively
plt.show()

# Rotate the graph programmatically and save frames
for angle in range(0, 360, 10):
    ax.view_init(elev=30, azim=angle)
    plt.draw()
    plt.pause(0.1)  # Pause to update the plot

if __name__ == "__main__":
    main()
