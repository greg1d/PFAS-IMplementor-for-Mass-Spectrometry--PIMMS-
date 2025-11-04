import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, RANSACRegressor


class SlopeValidator:
    def __init__(self, min_slope=0.05, max_slope=0.25):
        self.set_range(min_slope, max_slope)

    def set_range(self, min_slope, max_slope):
        self.min_slope = min_slope
        self.max_slope = max_slope
        print(f"[INFO] RANSAC slope range set to: [{self.min_slope}, {self.max_slope}]")

    def is_valid(self, model, X, y):
        if not hasattr(model, "coef_"):
            return False
        return self.min_slope <= model.coef_[0] <= self.max_slope


SLOPE_VALIDATOR = SlopeValidator()


def is_slope_valid(model, X, y):
    return SLOPE_VALIDATOR.is_valid(model, X, y)


# --- UPDATED FUNCTION SIGNATURE AND LOGIC ---


def find_trends_in_group(
    group_df,
    x_col,
    y_col,
    residual_threshold,
    min_trend_samples,
    min_r_squared,
    random_state=42,  # <---- added this
):
    group_df["subgroup"] = -1
    remaining_points = group_df.copy()
    trend_count = 0

    print(
        f"\n[INFO] Starting RANSAC trend search in group ({len(remaining_points)} points)..."
    )

    # Ensure numpy’s own RNG is also seeded
    np.random.seed(random_state)

    while len(remaining_points) >= min_trend_samples:
        X_ransac = remaining_points[[x_col]].values
        y_ransac = remaining_points[y_col].values

        ransac = RANSACRegressor(
            estimator=LinearRegression(),
            min_samples=2,
            residual_threshold=residual_threshold,
            is_model_valid=is_slope_valid,
            random_state=random_state,  # <---- added this
        )

        try:
            ransac.fit(X_ransac, y_ransac)
        except ValueError as e:
            print(f"  - RANSAC failed to fit: {e}")
            break

        if ransac.estimator_ is None:
            print("  - No valid estimator returned by RANSAC.")
            break

        inlier_mask = ransac.inlier_mask_
        num_inliers = np.sum(inlier_mask)

        if num_inliers < min_trend_samples:
            print(
                f"  - Only {num_inliers} inliers found (< {min_trend_samples} required). Stopping."
            )
            break

        X_inliers, y_inliers = X_ransac[inlier_mask], y_ransac[inlier_mask]
        score = ransac.estimator_.score(X_inliers, y_inliers)

        if score < min_r_squared:
            print(
                f"  - Trend rejected (R²={score:.3f} < {min_r_squared}) "
                f"with {num_inliers} inliers. Dropping those and retrying."
            )
            rejected_indices = remaining_points.index[inlier_mask]
            print(
                "    Rejected inlier m/z values:",
                remaining_points.loc[rejected_indices, x_col].tolist(),
            )
            remaining_points = remaining_points.iloc[~inlier_mask]
            continue

        # === Trend accepted ===
        inlier_indices = remaining_points.index[inlier_mask]
        slope, intercept = ransac.estimator_.coef_[0], ransac.estimator_.intercept_
        print(
            f"  - Found Trend {trend_count} (R²={score:.3f}, {num_inliers} points). "
            f"Slope={slope:.4f}, Intercept={intercept:.4f}"
        )

        print("    Inlier points:")
        for idx in inlier_indices:
            print(
                f"      Index {idx}: m/z={remaining_points.at[idx, x_col]:.4f}, CCS={remaining_points.at[idx, y_col]:.4f}"
            )

        group_df.loc[inlier_indices, "subgroup"] = trend_count

        remaining_points = remaining_points.drop(inlier_indices)
        trend_count += 1

    outlier_mask = group_df["subgroup"] == -1
    outlier_count = outlier_mask.sum()

    if outlier_count > 0:
        print(f"  - Dropping {outlier_count} outlier point(s).")
        print("    Outlier m/z values:", group_df.loc[outlier_mask, x_col].tolist())
        print("    Outlier CCS values:", group_df.loc[outlier_mask, y_col].tolist())

    print(f"[INFO] RANSAC trend search complete: {trend_count} trend(s) found.\n")

    return group_df[group_df["subgroup"] != -1].copy()


# --- UPDATED FUNCTION SIGNATURE ---
def process_all_groups(
    df, group_id_col, x_col, y_col, residual_threshold, min_trend_samples, min_r_squared
):
    if group_id_col not in df.columns:
        raise ValueError(f"Grouping column '{group_id_col}' not found.")
    all_results = []
    print("--- Starting Per-Group RANSAC Analysis ---")
    for group_id in sorted(df[group_id_col].unique()):
        print(f"\nProcessing {group_id_col}: {group_id}...")
        single_group_df = df[df[group_id_col] == group_id].copy()

        # Pass the parameter down to the next function
        result_df = find_trends_in_group(
            single_group_df,
            x_col,
            y_col,
            residual_threshold,
            min_trend_samples,
            min_r_squared,
        )

        if not result_df.empty:
            result_df["trend_group"] = result_df[group_id_col] + (
                result_df["subgroup"] / 10.0
            )
            all_results.append(result_df)
    print("\n--- Analysis Complete ---")
    if not all_results:
        return pd.DataFrame()
    final_df = pd.concat(all_results, ignore_index=True)
    final_df.drop(columns=["subgroup"], inplace=True)
    return final_df
