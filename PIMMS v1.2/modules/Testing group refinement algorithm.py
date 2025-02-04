import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import linregress

# Example dataset with an outlier (m/z, CCS)
data_points = [
    (298.9415, 133.81),
    (348.9374, 138.24),
    (348.9374, 142.24),
    (348.9375, 146.24),  # Outlier
    (398.9354333, 150.3333333),
    (448.9324, 159.84),
    (498.9309, 167.655),
    (598.92445, 185.09),
]


def refine_group_by_best_fit(groups, threshold=0.02, min_r2=0.99):
    """
    Finds the best-fit linear regression using all points first,
    then excludes outliers with > 2% residual error.
    Flags excluded points as "Potential Post Source Decay" (above trend)
    or "Potential Branched Isomer" (below trend).
    """
    # Convert to NumPy arrays
    mz_values = np.array([p[0] for p in data_points])
    ccs_values = np.array([p[1] for p in data_points])

    # Step 1: Find best fit for all points initially
    slope, intercept, r_value, _, _ = linregress(mz_values, ccs_values)
    r_squared = r_value**2

    print(
        f"[INFO] Initial Fit: Slope={slope:.4f}, Intercept={intercept:.4f}, R²={r_squared:.4f}"
    )

    # Step 2: Compute residuals and filter out large deviations (>2%)
    refined_group = []
    post_source_decay = []
    branched_isomers = []

    for mz, ccs in data_points:
        predicted_ccs = slope * mz + intercept
        residual = abs(ccs - predicted_ccs)

        if residual <= threshold * predicted_ccs:
            refined_group.append((mz, ccs))
        else:
            if ccs > predicted_ccs:
                post_source_decay.append((mz, ccs))
                print(
                    f"[FLAGGED] Post Source Decay: m/z={mz}, CCS={ccs}, Residual={residual:.4f}"
                )
            else:
                branched_isomers.append((mz, ccs))
                print(
                    f"[FLAGGED] Branched Isomer: m/z={mz}, CCS={ccs}, Residual={residual:.4f}"
                )

    # Step 3: Ensure R² ≥ 0.99 after filtering
    if len(refined_group) > 2:
        final_mz_values = np.array([p[0] for p in refined_group])
        final_ccs_values = np.array([p[1] for p in refined_group])
        slope, intercept, r_value, _, _ = linregress(final_mz_values, final_ccs_values)
        final_r_squared = r_value**2

        if final_r_squared < min_r2:
            print(
                "[WARNING] Final group does not meet R² ≥ 0.99. Reverting to best subset."
            )
            return find_best_high_r2_subset(data_points, min_r2)

    return refined_group, post_source_decay, branched_isomers


def find_best_high_r2_subset(data_points, min_r2=0.99):
    """Finds the longest subset with R² ≥ 0.99 when removing outliers."""
    n = len(data_points)
    best_subset = []
    max_length = 0

    for start in range(n):
        for end in range(start + 2, n + 1):  # At least 2 points needed
            subset = data_points[start:end]
            subset_mz = np.array([p[0] for p in subset])
            subset_ccs = np.array([p[1] for p in subset])

            if len(set(subset_mz)) < 2:
                continue  # Skip if all x values are identical

            slope, intercept, r_value, _, _ = linregress(subset_mz, subset_ccs)
            r_squared = r_value**2

            if r_squared >= min_r2 and len(subset) > max_length:
                best_subset = subset
                max_length = len(subset)

    return best_subset


# Apply filtering
final_group, post_source_decay, branched_isomers = refine_group_by_best_fit(data_points)

# Plot results
plt.figure(figsize=(8, 6))

# Plot all candidate points
mz_all, ccs_all = zip(*data_points)
plt.scatter(mz_all, ccs_all, color="gray", label="All Points", s=100)

# Plot refined group
if final_group:
    mz_final, ccs_final = zip(*final_group)
    plt.scatter(
        mz_final, ccs_final, color="blue", label="Final Homologous Series", s=100
    )

# Plot flagged post source decay
if post_source_decay:
    mz_decay, ccs_decay = zip(*post_source_decay)
    plt.scatter(
        mz_decay, ccs_decay, color="red", label="Post Source Decay", marker="x", s=100
    )

# Plot flagged branched isomers
if branched_isomers:
    mz_br, ccs_br = zip(*branched_isomers)
    plt.scatter(
        mz_br, ccs_br, color="purple", label="Branched Isomers", marker="D", s=100
    )

# Plot trendline for final group
if len(final_group) > 1:
    slope, intercept, _, _, _ = linregress(mz_final, ccs_final)
    reg_x = np.linspace(min(mz_final), max(mz_final), 100)
    reg_y = slope * reg_x + intercept
    plt.plot(reg_x, reg_y, "k--", label="Trend Line")

# Output final groups
print("\n[FINAL GROUP - Homologous Series]")
for point in final_group:
    print(f"m/z: {point[0]}, CCS: {point[1]}")

print("\n[POST SOURCE DECAY POINTS]")
for point in post_source_decay:
    print(f"m/z: {point[0]}, CCS: {point[1]}")

print("\n[BRANCHED ISOMER POINTS]")
for point in branched_isomers:
    print(f"m/z: {point[0]}, CCS: {point[1]}")

plt.xlabel("m/z")
plt.ylabel("CCS")
plt.legend()
plt.title("Point Classification: Homologous Series vs Anomalous Points")
plt.show()
