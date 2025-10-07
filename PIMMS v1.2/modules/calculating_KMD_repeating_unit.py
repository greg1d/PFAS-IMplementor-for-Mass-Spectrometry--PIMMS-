import matplotlib.pyplot as plt
import pandas as pd
from calculating_kendrick_lamar_defect import calculate_KMD
from creating_single_df import stack_library_with_adjusted
from repeat_unit_analysis import mz_repeating_unit_analysis


def plot_KMD_v_mz(df):
    """
    Plots KMD vs m/z, color-coding by GroupID and differentiating by Repeating Unit.

    This function visualizes homologous series by plotting KMD against m/z.
    - It uses the correct KMD column based on the 'Repeating Unit' ('CF2' or 'OCF2').
    - It colors each unique 'GroupID' differently for "Other Compounds".
    - It uses distinct, fixed markers and colors for 'External Standard' compounds
      to make them stand out.

    Args:
        df (pd.DataFrame): DataFrame must contain 'm/z', 'Classification Type',
                           'Repeating Unit', 'KMD (CF2)', 'KMD (OCF2)', and 'GroupID'.
    """
    # --- Input Validation ---
    required_columns = [
        "m/z",
        "Classification Type",
        "Repeating Unit",
        "KMD (CF2)",
        "KMD (OCF2)",
        "GroupID",
    ]
    if df.empty or not all(col in df.columns for col in required_columns):
        print(
            "[WARNING] Plotting: DataFrame is empty or missing required columns:",
            " ".join(required_columns),
        )
        return

    # --- Plotting Setup ---
    plt.figure(figsize=(16, 9))

    # Get a list of unique group IDs to generate a color map
    # Exclude standards from group coloring
    other_compounds_df_all = df[df["Classification Type"] != "External Standard"]
    unique_group_ids = sorted(other_compounds_df_all["GroupID"].unique())

    # Use a perceptually uniform colormap like 'viridis' or 'plasma'
    # 'tab20' is also great for distinct colors if you have <= 20 groups
    colormap = plt.get_cmap("viridis", len(unique_group_ids) + 1)
    color_map = {gid: colormap(i) for i, gid in enumerate(unique_group_ids)}

    # Define fixed properties for External Standards
    standard_configs = {
        "CF2": {"color": "red", "marker": "x", "kmd_col": "KMD (CF2)"},
        "OCF2": {"color": "fuchsia", "marker": "+", "kmd_col": "KMD (OCF2)"},
    }

    # Define markers for other compounds based on repeating unit
    other_compound_markers = {"CF2": "o", "OCF2": "s"}

    # --- Plot "Other Compounds" grouped by GroupID ---
    for group_id, color in color_map.items():
        group_df = other_compounds_df_all[other_compounds_df_all["GroupID"] == group_id]
        if group_df.empty:
            continue

        # Plot CF2 and OCF2 points for this group separately to use correct KMD and marker
        for unit, marker in other_compound_markers.items():
            unit_group_df = group_df[group_df["Repeating Unit"] == unit]
            if not unit_group_df.empty:
                kmd_col = standard_configs[unit]["kmd_col"]
                plt.scatter(
                    unit_group_df["m/z"],
                    unit_group_df[kmd_col],
                    color=color,
                    marker=marker,
                    label=f"Group {group_id} ({unit})",
                    alpha=0.8,
                    edgecolors="k",
                    linewidths=0.5,
                )

    # --- Plot "External Standards" on top ---
    standards_df_all = df[df["Classification Type"] == "External Standard"]
    for unit, config in standard_configs.items():
        standards_df_unit = standards_df_all[standards_df_all["Repeating Unit"] == unit]
        if not standards_df_unit.empty:
            plt.scatter(
                standards_df_unit["m/z"],
                standards_df_unit[config["kmd_col"]],
                color=config["color"],
                marker=config["marker"],
                s=150,  # Make standards larger
                label=f"External Standard ({unit})",
                alpha=1.0,
                zorder=5,  # Ensure standards are plotted on top
            )

    # --- Final Plot Formatting ---
    plt.ylim(-0.1, 0.1)
    plt.xlabel("m/z", fontsize=12)
    plt.ylabel("Kendrick Mass Defect (KMD)", fontsize=12)
    plt.title("KMD vs m/z by GroupID, Repeating Unit, and Classification", fontsize=16)
    plt.legend(title="Legend", bbox_to_anchor=(1.04, 1), loc="upper left")
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.tight_layout(rect=[0, 0, 0.85, 1])  # Adjust layout to make room for legend
    plt.show()


def validate_KMD_group(results, min_well_spaced_points, min_library_points):
    """
    Validates the final trend lines produced by KMD analysis.

    This function filters trends based on three primary quality criteria:
    1. The minimum number of points that are well-spaced (m/z difference >= 10).
    2. The minimum number of external standard points.

    Args:
        ransac_df (pd.DataFrame): The DataFrame returned by the RANSAC process.
        min_well_spaced_points (int): The minimum number of points with an m/z spacing
                                      of at least 10 from the previous point.
        min_library_points (int): The minimum number of 'External Standard' points
                                  a trend must have.

    Returns:
        pd.DataFrame: A fully validated DataFrame containing only high-quality trends.
    """
    if results is None or results.empty:
        return pd.DataFrame()

    print("\n[INFO] Starting post-KMD validation of trend lines...")
    print("results df", results.head())
    # Define the fixed R-squared threshold internally.

    initial_trends = results["GroupID"].nunique()
    validated_df = results.copy()

    # --- Filter 1: Minimum well-spaced points per trend ---
    if min_well_spaced_points > 0:

        def _has_enough_well_spaced_points(group):
            """Checks if a trend group has enough points with significant m/z spacing."""
            sorted_group = group.sort_values(by="m/z")
            well_spaced_count = (sorted_group["m/z"].diff().fillna(10) >= 10).sum()
            return well_spaced_count >= min_well_spaced_points

        validated_df = validated_df.groupby("GroupID").filter(
            _has_enough_well_spaced_points
        )
        print(
            f"[INFO] {initial_trends - validated_df['GroupID'].nunique()} trends removed by min_well_spaced_points ({min_well_spaced_points})."
        )
        initial_trends = validated_df["GroupID"].nunique()

    # --- Filter 2: Minimum external standard points per trend ---
    if min_library_points > 0:

        def _has_min_library_points(group):
            """Checks if a trend group meets the minimum external standard point requirement."""
            standard_count = (group["Classification Type"] == "External Standard").sum()
            return standard_count >= min_library_points

        validated_df = validated_df.groupby("GroupID").filter(_has_min_library_points)
        print(
            f"[INFO] {initial_trends - validated_df['GroupID'].nunique()} trends removed by min_library_points ({min_library_points})."
        )
        initial_trends = validated_df["GroupID"].nunique()

    return validated_df


def main():
    adjusted_df = pd.read_csv("PIMMS v1.2\data\SealsPIMMS.csv")
    library_df = pd.read_csv(
        "PIMMS v1.2\import folder\Baker_Group_RPLC_DTIMS_MS_PFAS_Library_Negative.csv"
    )
    stacked_df = stack_library_with_adjusted(adjusted_df, library_df)
    selected_repeating_units = {"OCF2": 65.991721}
    # Call the mz_repeating_unit_analysis function
    results = mz_repeating_unit_analysis(
        stacked_df, selected_repeating_units, mass_error_ppm=10, min_valid_points=3
    )
    results = calculate_KMD(results)
    print("results after KMD calculation", results.head())
    validated_results = validate_KMD_group(results, 3, 2)

    plot_KMD_v_mz(validated_results)


if __name__ == "__main__":
    main()
