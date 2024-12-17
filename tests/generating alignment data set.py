import numpy as np
import pandas as pd

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


# Function to generate noisy data
def generate_noisy_data(aligned_mz, aligned_ccs, num_samples=100):
    noisy_data = []
    for mz, ccs in zip(aligned_mz, aligned_ccs):
        samples = []
        for _ in range(num_samples):
            noisy_mz = mz * (1 + np.random.uniform(-10e-6, 10e-6))  # Vary within 10 ppm
            noisy_ccs = ccs * (1 + np.random.uniform(-0.02, 0.02))  # Vary within 2%
            samples.append((noisy_mz, noisy_ccs))
        noisy_data.append(samples)
    return noisy_data


# Generate noisy data
noisy_data = generate_noisy_data(aligned_mz, aligned_ccs)

# Convert to DataFrame for easier handling
aligned_features = pd.DataFrame(
    {"Aligned Feature m/z": aligned_mz, "Aligned Feature CCS": aligned_ccs}
)

# Flatten the noisy data and create columns for each sample
noisy_data_flat = np.array(noisy_data).reshape(len(aligned_mz), -1)
columns = []
for i in range(noisy_data_flat.shape[1] // 2):
    columns.append(f"Sample {i+1} (m/z)")
    columns.append(f"Sample {i+1} (CCS)")
noisy_data_df = pd.DataFrame(noisy_data_flat, columns=columns)

# Combine aligned features and noisy data
df_combined = pd.concat([aligned_features, noisy_data_df], axis=1)

# Format m/z to 4 decimal places and CCS to 2 decimal places
df_combined["Aligned Feature m/z"] = df_combined["Aligned Feature m/z"].round(4)
df_combined["Aligned Feature CCS"] = df_combined["Aligned Feature CCS"].round(2)
for col in df_combined.columns:
    if "(m/z)" in col:
        df_combined[col] = df_combined[col].round(4)
    elif "(CCS)" in col:
        df_combined[col] = df_combined[col].round(2)

# Save to a CSV file
df_combined.to_csv("noisy_dataset.csv", index=False)
print("Noisy dataset generated and saved to 'noisy_dataset.csv'")

# Print the first few rows of the combined dataset
print(df_combined.head())
