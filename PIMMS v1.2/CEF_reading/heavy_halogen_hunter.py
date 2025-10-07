import pandas as pd
import matplotlib.pyplot as plt
from CEF_PIMMS_reader_workflow_file_1 import (
    parse_all_cef_files_in_folder,
    compute_kaufman_constants,
    get_cef_sample_names,
    run_matching_pipeline,
)
from calculating_Kaufman_parameters_file_2 import align_features, create_summary_table
# --- Data Extraction, Matching, and Alignment Functions (from previous steps) ---
# For brevity, the full code of these functions is collapsed.
# Ensure they are present in your script as defined in the previous responses.


def plot_kaufman_scatter(kaufman_df):
    """
    Plots an XY scatter plot of md/C (mass defect over C) vs. m/C and overlays the PFAS KDE boundary.

    Parameters:
        kaufman_df (pd.DataFrame): DataFrame with Kaufman constants including 'm_over_C' and 'md_over_C'.
        boundary_csv_path (str): Path to the CSV file containing PFAS KDE boundary with columns 'm/C', 'MD/C'.
    """
    if kaufman_df.empty:
        print("[INFO] No Kaufman data to plot.")
        return
    plt.figure(figsize=(7, 5))

    # === Plot Kaufman Points ===
    plt.scatter(
        kaufman_df["m_over_C"],
        kaufman_df["md_over_C"],
        color="darkblue",
        edgecolor="black",
        s=50,
        alpha=0.8,
        label="Kaufman Points",
    )

    # === Axes Formatting ===
    plt.axhline(0, color="gray", linestyle="--", linewidth=1)
    plt.axvline(0, color="gray", linestyle="--", linewidth=1)

    plt.xlabel("m / C", fontsize=12, fontweight="bold")
    plt.ylabel("md / C", fontsize=12, fontweight="bold")
    plt.title("Kaufman Plot: Mass Defect / C vs. m / C", fontsize=14)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.show()


def main():
    """Main function to run the full workflow."""
    pimms_file_path = r"PIMMS v1.2\import folder\Dummy test output.csv"
    cef_folder = r"PIMMS v1.2\CEF_reading\CEF_folder"

    try:
        # Load Data
        pimms_df = pd.read_csv(pimms_file_path)
        print(pimms_df.head())
        pimms_df.columns = pimms_df.columns.str.strip()
        all_cef_data = parse_all_cef_files_in_folder(cef_folder)

        # Pre-calculate Kaufman Constants (now includes Intensity_3)
        kaufman_df = compute_kaufman_constants(all_cef_data)

        # Run Matching and Alignment Pipeline
        sample_names = get_cef_sample_names(cef_folder)
        combined_df = run_matching_pipeline(pimms_df, all_cef_data, sample_names)

        if combined_df.empty:
            print("\n--- No matches were found, skipping alignment. ---")
            return

        aligned_df = align_features(combined_df)

        # Merge Kaufman data with Aligned Features
        final_long_df = pd.merge(
            aligned_df, kaufman_df, on=["Sample", "Compound"], how="left"
        )

        # Create the final summary table
        summary_table = create_summary_table(final_long_df)
        plot_kaufman_scatter(summary_table)
        #  Report Final Summary Table
        print("\n\n--- Final Feature Summary Table ---")
        if summary_table.empty:
            print("Could not generate a summary table.")
        else:
            print(
                f"Successfully generated a summary table with {len(summary_table)} aligned features."
            )
            print(summary_table)

    except (FileNotFoundError, TypeError) as e:
        print(f"\n[ERROR] {e}")
    except Exception as e:
        print(f"\n[UNEXPECTED ERROR] An error occurred: {e}")


if __name__ == "__main__":
    main()
