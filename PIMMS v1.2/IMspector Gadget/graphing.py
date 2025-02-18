import os
import sys

import pandas as pd
import plotly.io as pio

# ✅ Ensure Python Can Find the Module
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get current script's directory
MODULE_PATH_1 = os.path.join(BASE_DIR, "ccs_v_mz_modules")
MODULE_PATH_2 = os.path.join(BASE_DIR, "ccs_v_mz_library_search_modules")

sys.path.append(MODULE_PATH_1)  # Add `ccs_v_mz_modules` to sys.path
sys.path.append(MODULE_PATH_2)  # Add `ccs_v_mz_library_search_modules` to sys.path

from analysis import run_analysis  # ✅ Import `run_analysis()`
from plotly_graphing import make_plotly_graph  # ✅ Import from `ccs_v_mz_modules`


def plot_figure_1(file_path="PIMMS v1.2/Data_output/PIMMS Processed Data set.csv"):
    """
    Processes data, runs analysis, and generates a Plotly figure.

    Returns:
        plotly.graph_objects.Figure: The generated plot.
    """
    adjusted_df = pd.read_csv(file_path)
    print("\n[INFO] Running `run_analysis()`...")

    # ✅ Run full analysis using imported function
    (
        refined_groups,
        branched_isomers,
        post_source_decay,
        mass_only_groups,
        mass_groups,
    ) = run_analysis(adjusted_df)

    # ✅ Check if valid homologous series were identified
    if mass_groups.empty:
        print("\n[WARNING] No homologous series groups identified. Exiting.")
        return None

    print(f"[DEBUG] Identified {mass_groups['GroupID'].nunique()} homologous series.")

    # **Debugging Step**: Ensure that there is data in refined_groups for plotting
    non_empty_refined_groups = [
        group
        for group in refined_groups
        if isinstance(group, pd.DataFrame) and not group.empty
    ]

    if not non_empty_refined_groups:
        print("\n[WARNING] All refined_groups are empty! Trendlines may not appear.")
    else:
        print("\n[INFO] Some homologous series groups contain data.")

    # **Combine results into one simplified plot input**
    plot_data = {
        "adjusted_df": adjusted_df,
        "refined_groups": refined_groups,
        "branched_isomers": branched_isomers,
        "post_source_decay": post_source_decay,
        "mass_only_groups": mass_only_groups,
        "mass_groups": mass_groups,
    }

    # **Step: Generate Plotly plot**
    print("\n[INFO] Generating Plotly plot...")
    fig = make_plotly_graph(**plot_data)  # Pass all plot data in a single call

    return fig


# ✅ Main function to call `plot_figure_1()`
if __name__ == "__main__":
    fig = plot_figure_1()
    if fig:
        print("[INFO] Plot generation complete. Displaying plot...")
        pio.show(fig)
