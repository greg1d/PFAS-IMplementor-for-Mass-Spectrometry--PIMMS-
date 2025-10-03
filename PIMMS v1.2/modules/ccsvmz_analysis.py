import pandas as pd
import numpy as np
from sklearn.linear_model import RANSACRegressor, LinearRegression
import matplotlib.pyplot as plt
from repeat_unit_analysis import (
    stack_library_with_adjusted,
    mz_repeating_unit_analysis,
    mz_group_refinement,
)


# MODULE 1: A simple, reusable validation callback for RANSAC.
def is_slope_valid(model, X, y):
    if not hasattr(model, "coef_"):
        return False
    slope = model.coef_[0]
    return 0.05 <= slope <= 0.25


# --- UPDATED: Core RANSAC logic with a try/except block ---
def find_trends_in_group(group_df, x_col, y_col, residual_threshold, min_trend_samples):
    """
    Applies RANSAC iteratively to a single group DataFrame to find trends.
    This version drops any points that are not assigned to a valid trend (outliers).
    """
    group_df["subgroup"] = -1
    remaining_points = group_df.copy()
    trend_count = 0

    while len(remaining_points) >= min_trend_samples:
        X_ransac = remaining_points[[x_col]].values
        y_ransac = remaining_points[y_col].values

        ransac = RANSACRegressor(
            estimator=LinearRegression(),
            min_samples=2,
            residual_threshold=residual_threshold,
            is_model_valid=is_slope_valid,
        )

        try:
            ransac.fit(X_ransac, y_ransac)
        except ValueError as e:
            if "RANSAC could not find a valid consensus set" in str(e):
                print(
                    "  - No more valid trends could be found in the remaining points. Stopping search for this group."
                )
                break
            else:
                raise e

        if ransac.estimator_ is None:
            print(
                "  - No more valid trends could be found in the remaining points. Stopping search for this group."
            )
            break

        inlier_mask = ransac.inlier_mask_

        if np.sum(inlier_mask) < min_trend_samples:
            break

        X_inliers = X_ransac[inlier_mask]
        y_inliers = y_ransac[inlier_mask]
        score = ransac.estimator_.score(X_inliers, y_inliers)

        if score < 0.9:
            outlier_mask = np.logical_not(inlier_mask)
            remaining_points = remaining_points[outlier_mask]
            continue

        inlier_indices = remaining_points[inlier_mask].index
        group_df.loc[inlier_indices, "subgroup"] = trend_count

        slope, intercept = ransac.estimator_.coef_[0], ransac.estimator_.intercept_
        print(
            f"  - Found Trend {trend_count} (R²={score:.3f}) with {len(inlier_indices)} points. Model: y = {slope:.4f}x + {intercept:.4f}"
        )

        remaining_points = remaining_points.drop(inlier_indices)
        trend_count += 1

    # --- NEW: Drop outliers before returning ---
    # Count how many points were not assigned to any valid trend
    outlier_count = (group_df["subgroup"] == -1).sum()
    if outlier_count > 0:
        print(f"  - Dropping {outlier_count} outlier point(s) from this group.")

    # Filter the DataFrame to keep only the points that are part of a valid trend (inliers)
    inlier_df = group_df[group_df["subgroup"] != -1].copy()

    return inlier_df


# --- (The rest of your script: process_all_groups, plot_ransac_results, and the main block, remain the same) ---
def process_all_groups(
    df, group_id_col, x_col, y_col, residual_threshold, min_trend_samples
):
    if group_id_col not in df.columns:
        raise ValueError(f"Grouping column '{group_id_col}' not found.")
    all_results = []
    print("--- Starting Per-Group RANSAC Analysis ---")
    for group_id in sorted(df[group_id_col].unique()):
        print(f"\nProcessing {group_id_col}: {group_id}...")
        single_group_df = df[df[group_id_col] == group_id].copy()
        result_df = find_trends_in_group(
            single_group_df, x_col, y_col, residual_threshold, min_trend_samples
        )
        result_df["trend_group"] = result_df[group_id_col] + (
            result_df["subgroup"] / 10.0
        )
        result_df.loc[result_df["subgroup"] == -1, "trend_group"] = -1
        all_results.append(result_df)
    print("\n--- Analysis Complete ---")
    if not all_results:
        return pd.DataFrame()
    final_df = pd.concat(all_results, ignore_index=True)
    final_df.drop(columns=["subgroup"], inplace=True)
    return final_df


def plot_ransac_results(
    df, x_col="m/z", y_col="CCS", group_col="trend_group", title="RANSAC Trend Analysis"
):
    """
    Generates a scatter plot of the RANSAC results, coloring points by trend group.
    Updated to prevent scikit-learn UserWarning.
    """
    if df.empty or group_col not in df.columns:
        print("[INFO] Plotting skipped: DataFrame is empty or missing group column.")
        return

    plt.style.use("seaborn-v0_8-whitegrid")
    plt.figure(figsize=(12, 8))

    unique_groups = sorted([g for g in df[group_col].unique() if g != -1])
    colors = plt.cm.viridis(
        np.linspace(0, 1, len(unique_groups) if unique_groups else 1)
    )
    color_map = {group: color for group, color in zip(unique_groups, colors)}
    color_map[-1] = "gray"

    for group_id, group_df in df.groupby(group_col):
        label = f"Trend {group_id}" if group_id != -1 else "Outliers"
        plt.scatter(
            group_df[x_col],
            group_df[y_col],
            color=color_map[group_id],
            s=(50 if group_id != -1 else 20),
            label=label,
            alpha=(1.0 if group_id != -1 else 0.5),
        )

    for group_id in unique_groups:
        group_df = df[df[group_col] == group_id]

        # --- FIX: Use .values to pass NumPy arrays to .fit() ---
        # This ensures the data format for fitting matches the format for predicting.
        model = LinearRegression().fit(group_df[[x_col]].values, group_df[y_col].values)
        # --- END FIX ---

        x_range = np.linspace(group_df[x_col].min(), group_df[x_col].max(), 100)
        # model.predict() is already receiving a NumPy array, so no change is needed here.
        y_pred = model.predict(x_range.reshape(-1, 1))

        plt.plot(x_range, y_pred, color=color_map[group_id], linewidth=2)

    plt.title(title, fontsize=16)
    plt.xlabel(x_col, fontsize=12)
    plt.ylabel(y_col, fontsize=12)
    plt.legend()
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    try:
        adjusted_df = r"C:\Users\Greg Kudzin\Downloads\250918_SealsPIMMS.csv"
        pfas_library = r"PIMMS v1.2\import folder\Baker_Group_RPLC_DTIMS_MS_PFAS_Library_Negative.csv"
        adjusted_df = pd.read_csv(adjusted_df)
        pfas_library = pd.read_csv(pfas_library)
        print(adjusted_df)
        stacked_df = stack_library_with_adjusted(adjusted_df, pfas_library)
        selected_repeating_units = {
            "CF2": 49.9968,
        }
        mass_groups = mz_repeating_unit_analysis(
            stacked_df, selected_repeating_units, mass_error_ppm=10
        )
        min_valid_points = 4
        mass_groups = mz_group_refinement(
            mass_groups, min_library_points=1, min_valid_points=min_valid_points
        )

        RANSAC_THRESHOLD = 4
        MIN_SAMPLES_FOR_TREND = 3

        # Call the main controller function
        final_df = process_all_groups(
            df=mass_groups,
            group_id_col="GroupID",
            x_col="m/z",
            y_col="CCS",
            residual_threshold=RANSAC_THRESHOLD,
            min_trend_samples=min_valid_points,
        )

    except Exception as e:
        print(f"An error occurred: {e}")
