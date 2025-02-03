import time
import pandas as pd
from scipy.stats import linregress
import plotly.graph_objects as go

# Define repeating units
REPEATING_UNITS = {
    "CF2": 49.9968064,
    "OCF2": 65.9917214,
    "TEST": 100,
}


def mz_repeating_unit_analysis(adjusted_df, mass_error_ppm=10, repeating_units=["CF2"]):
    """Identifies homologous series trends with at least 3 points within 2 repeating units."""

    start_time = time.time()
    selected_units = [
        REPEATING_UNITS[unit] for unit in repeating_units if unit in REPEATING_UNITS
    ]

    # **Sort data by m/z to ensure proper trend building**
    adjusted_df = adjusted_df.sort_values(by="m/z").reset_index(drop=True)

    used_indices = set()  # Track indices that are already included in a group
    groups = []

    print(f"[DEBUG] Total data points: {len(adjusted_df)}")

    for M in selected_units:
        print(f"\n[INFO] Analyzing with M = {M:.6f}")

        for i in range(len(adjusted_df)):  # Iterate over all peaks
            if i in used_indices:
                continue  # Skip if already assigned to a group

            mz_value = adjusted_df.iloc[i]["m/z"]
            current_group = [
                {
                    "m/z": mz_value,
                    "ID": adjusted_df.iloc[i]["ID"],
                    "CCS": adjusted_df.iloc[i]["CCS"],
                    "Classification Type": adjusted_df.iloc[i]["Classification Type"],
                    "Match Source": adjusted_df.iloc[i]["Match Source"],
                    "Match": adjusted_df.iloc[i]["Match"],
                }
            ]
            used_indices.add(i)

            for j in range(i + 1, len(adjusted_df)):  # Only look forward
                if j in used_indices:
                    continue

                next_mz_value = adjusted_df.iloc[j]["m/z"]
                mass_diff = abs(mz_value - next_mz_value)

                # Check if the difference matches M, 2M, 3M, or 4M
                if any(
                    abs(mass_diff - M * k) <= (mass_error_ppm / 1e6) * mz_value
                    for k in range(1, 5)
                ):
                    current_group.append(
                        {
                            "m/z": next_mz_value,
                            "ID": adjusted_df.iloc[j]["ID"],
                            "CCS": adjusted_df.iloc[j]["CCS"],
                            "Classification Type": adjusted_df.iloc[j][
                                "Classification Type"
                            ],
                            "Match Source": adjusted_df.iloc[j]["Match Source"],
                            "Match": adjusted_df.iloc[j]["Match"],
                        }
                    )
                    used_indices.add(j)  # Mark as used

            if len(current_group) >= 3:  # Only store groups with 3+ points
                groups.append(current_group)

    print(
        f"\n[INFO] Mass repeating unit analysis completed in {time.time() - start_time:.4f} seconds."
    )

    # **🔹 Debugging: Print each group in tabular format**
    for idx, group in enumerate(groups):
        print(f"\n[DEBUG] Group {idx + 1} - Homologous Series:")
        df_debug = pd.DataFrame(group)
        print(df_debug.to_string(index=False))  # Print clean table without row index
        print("-" * 80)  # Separator for readability

    return groups


def CCS_vs_mz_trend_analysis(groups, variation_threshold=0.02):
    """Plots CCS vs. m/z trends and ensures correct data structure."""

    # **Debugging: Check type of `groups`**
    print(f"[DEBUG] `groups` type: {type(groups)}")
    if isinstance(groups, pd.DataFrame):
        print("[ERROR] `groups` is a DataFrame but should be a list! Converting...")
        groups = groups.to_dict(
            orient="records"
        )  # Convert it to a list of dictionaries

    if not isinstance(groups, list):
        print(f"[ERROR] `groups` should be a list, but it is {type(groups)}")
        return

    if len(groups) == 0:
        print("[ERROR] No groups found. Exiting function.")
        return

    for idx, group in enumerate(groups):
        print(f"\nProcessing Group {idx + 1}:")

        if not isinstance(group, list):
            print(f"[ERROR] Group {idx + 1} is not a list! It is type {type(group)}")
            continue

        if not all(isinstance(point, dict) for point in group):
            print(
                f"[ERROR] Group {idx + 1} contains invalid elements! Printing first 5:"
            )
            for point in group[:5]:  # Print first 5 elements for debugging
                print(f"    - {point} (Type: {type(point)})")
            continue

        mz_values = [point["m/z"] for point in group]
        ccs_values = [point["CCS"] for point in group]

        if len(mz_values) < 3:
            print(f"[DEBUG] Group {idx + 1} skipped (less than 3 points)")
            continue

        slope, intercept, r_value, p_value, std_err = linregress(mz_values, ccs_values)
        r_squared = r_value**2

        if r_squared <= 0.90:
            print(f"[DEBUG] Group {idx + 1} skipped (R² {r_squared:.4f} too low)")
            continue

        print(f"[DEBUG] Group {idx + 1} Regression: R²={r_squared:.4f}")

        # **Debugging: Print group data**
        print(pd.DataFrame(group))

        reg_line_x = sorted(mz_values)
        reg_line_y = [slope * mz + intercept for mz in reg_line_x]

        fig = go.Figure()

        # Add trendline
        fig.add_trace(
            go.Scatter(
                x=reg_line_x,
                y=reg_line_y,
                mode="lines",
                name=f"Trend {idx + 1}",
                line=dict(color="black", dash="dash"),
                hoverinfo="skip",
            )
        )

        # Add group points
        for point in group:
            mz, ccs, classification, match_name = (
                point["m/z"],
                point["CCS"],
                point["Classification Type"],
                point["Match"],
            )

            fig.add_trace(
                go.Scatter(
                    x=[mz],
                    y=[ccs],
                    mode="markers",
                    marker=dict(size=8, color="blue"),
                    hovertemplate=f"Match: {match_name}<br>m/z: {mz}<br>CCS: {ccs}<br>Classification: {classification}<extra></extra>",
                )
            )

        fig.update_layout(
            title=f"Group {idx + 1}: CCS vs m/z",
            xaxis_title="m/z",
            yaxis_title="CCS",
            template="plotly_white",
        )

        fig.show()


def main():
    """Run the analysis and interactive plot."""
    file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set.csv"
    adjusted_df = pd.read_csv(file_path)

    print("[DEBUG] First few rows of dataset:")
    print(adjusted_df.head())

    groups = mz_repeating_unit_analysis(adjusted_df)

    # **Verify `groups` before passing**
    print(f"[DEBUG] `groups` after function call type: {type(groups)}")
    if isinstance(groups, pd.DataFrame):
        print("[ERROR] `groups` is a DataFrame! Converting to list...")
        groups = groups.to_dict(orient="records")

    CCS_vs_mz_trend_analysis(groups)  # ✅ Ensure only list is passed


if __name__ == "__main__":
    main()
