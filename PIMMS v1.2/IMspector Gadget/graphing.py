import os
import sys
import plotly.io as pio
from data_processing import load_adjusted_data  # ✅ Ensure correct data loading

# ✅ Ensure Python Can Find the Module
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get current script's directory
MODULE_PATH_1 = os.path.join(BASE_DIR, "ccs_v_mz_modules")
MODULE_PATH_2 = os.path.join(BASE_DIR, "ccs_v_mz_library_search_modules")

sys.path.append(MODULE_PATH_1)  # Add `ccs_v_mz_modules` to sys.path
sys.path.append(MODULE_PATH_2)  # Add `ccs_v_mz_library_search_modules` to sys.path

from plotly_graphing import make_plotly_graph  # ✅ Import from `ccs_v_mz_modules`
from analysis import run_analysis  # ✅ Import `run_analysis()` instead of redefining


def plotly_ccs_v_mz_sample_plot(adjusted_df):
    """
    Runs CCS vs. m/z analysis and generates a Plotly plot.

    Args:
        adjusted_df (pd.DataFrame): The processed data set to analyze.

    Returns:
        fig (plotly.graph_objects.Figure): The generated Plotly figure.
    """

    print("\n[INFO] Running `run_analysis()` for CCS vs. m/z trend analysis...")

    # ✅ Step 1: Run Analysis
    (
        refined_groups,
        branched_isomer_groups,
        post_source_decay_groups,
        mass_only_groups,
        mass_groups,
    ) = run_analysis(adjusted_df)

    # ✅ Step 2: Check if valid homologous series were identified
    if mass_groups.empty:
        print("\n[WARNING] No homologous series groups identified. Exiting.")
        return None  # Return None if no valid series exist

    print(f"[DEBUG] Identified {mass_groups['GroupID'].nunique()} homologous series.")

    # ✅ Step 3: Generate Plotly graph
    fig = make_plotly_graph(
        adjusted_df,
        refined_groups,
        branched_isomer_groups,
        post_source_decay_groups,
        mass_only_groups,
        mass_groups,  # ✅ Now correctly formatted as a dictionary
    )

    print("[INFO] CCS v m/z plot generation complete.")

    return fig


def main():
    adjusted_df = load_adjusted_data()

    fig = plotly_ccs_v_mz_sample_plot(adjusted_df)

    # **Step 5: Display the Plotly plot**
    print("[INFO] Plot generation complete. Displaying plot...")
    pio.show(fig)


if __name__ == "__main__":
    main()
