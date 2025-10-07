import pandas as pd
import os
import matplotlib.pyplot as plt
from CEF_PIMMS_reader_workflow_file_1 import (
    parse_all_cef_files_in_folder,
    get_cef_sample_names,
    compute_kaufman_constants,
    run_matching_pipeline,
)
from calculating_Kaufman_parameters_file_2 import (
    align_features,
    create_summary_table,
)


def plot_kaufman_scatter(kaufman_df):
    """
    Plots an XY scatter plot of md/C vs. m/C and overlays labels from the 'Match_ID' column.

    Parameters:
        kaufman_df (pd.DataFrame): DataFrame with Kaufman constants including
                                   'm_over_C', 'md_over_C', and 'Match_ID'.
    """
    if kaufman_df.empty:
        print("[INFO] No Kaufman data to plot.")
        return

    boundary_csv_path = r"PIMMS v1.2\CEF_reading\PFAS_90_percent_KDE_boundary.csv"
    plt.figure(figsize=(10, 8))  # Increased size for better label visibility

    # === Plot Kaufman Points ===
    plt.scatter(
        kaufman_df["m_over_C"],
        kaufman_df["md_over_C"],
        color="darkblue",
        edgecolor="black",
        s=60,
        alpha=0.7,
        label="Kaufman Points",
    )

    # --- NEW: Add Point Labels ---
    if "Match_ID" in kaufman_df.columns:
        # Iterate through each point in the DataFrame to add its label
        for i, row in kaufman_df.iterrows():
            label = row["Match_ID"]
            x = row["m_over_C"]
            y = row["md_over_C"]

            # Add the text label to the plot slightly above the point
            plt.text(x, y + 0.002, label, fontsize=9, ha="center", color="black")
    else:
        print(
            "[WARNING] 'Match_ID' column not found in DataFrame. Skipping point labels."
        )
    # --- End of New Code ---

    # === Optional: Overlay KDE Boundary ===
    try:
        if boundary_csv_path and os.path.exists(boundary_csv_path):
            boundary_df = pd.read_csv(boundary_csv_path)
            if {"m/C", "MD/C"}.issubset(boundary_df.columns):
                plt.plot(
                    boundary_df["m/C"],
                    boundary_df["MD/C"],
                    linestyle="--",
                    color="red",
                    linewidth=2,
                    label="PFAS 90% KDE Boundary",
                )
            else:
                print("[WARNING] Boundary CSV missing required columns: 'm/C', 'MD/C'")
        elif boundary_csv_path:
            print(f"[WARNING] Boundary CSV not found at: {boundary_csv_path}")
    except Exception as e:
        print(f"[ERROR] Could not read or plot boundary file: {e}")

    # === Axes Formatting ===
    plt.axhline(0, color="gray", linestyle="--", linewidth=1)
    plt.axvline(0, color="gray", linestyle="--", linewidth=1)
    plt.xlabel("m / C", fontsize=12, fontweight="bold")
    plt.ylabel("md / C", fontsize=12, fontweight="bold")
    plt.title("Kaufman Plot: Mass Defect / C vs. m / C", fontsize=14, fontweight="bold")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.show()


def main():
    """Main function to run the full workflow."""
    pimms_file_path = r"PIMMS v1.2\import folder\Dummy test output.csv"
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder"

    try:
        pimms_df = pd.read_csv(pimms_file_path)
        pimms_df.columns = pimms_df.columns.str.strip()
        all_cef_data = parse_all_cef_files_in_folder(cef_folder)

        kaufman_df = compute_kaufman_constants(all_cef_data)

        sample_names = get_cef_sample_names(cef_folder)
        combined_df = run_matching_pipeline(pimms_df, all_cef_data, sample_names)
        if combined_df.empty:
            print("\n--- No matches were found, skipping alignment. ---")
            return

        aligned_df = align_features(combined_df)

        final_long_df = pd.merge(
            aligned_df, kaufman_df, on=["Sample", "Compound"], how="left"
        )

        summary_table = create_summary_table(final_long_df)

        print("\n\n--- Final Feature Summary Table ---")
        if summary_table.empty:
            print("Could not generate a summary table.")
        else:
            print(
                f"Successfully generated a summary table with {len(summary_table)} aligned features."
            )
            with pd.option_context(
                "display.max_rows",
                None,
                "display.max_columns",
                None,
                "display.width",
                1000,
            ):
                print(summary_table)
                summary_table.to_csv(
                    r"PIMMS v1.2\import folder\summary_table.csv", index=False
                )

        plot_kaufman_scatter(summary_table)
        print("\n--- End of Workflow ---\n")
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] An error occurred: {e}")


if __name__ == "__main__":
    main()
