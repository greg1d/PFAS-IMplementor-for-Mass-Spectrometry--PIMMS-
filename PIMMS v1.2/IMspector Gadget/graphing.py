import os
import sys

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

# ✅ Ensure Python Can Find the Module
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get current script's directory
MODULE_PATH_1 = os.path.join(BASE_DIR, "ccs_v_mz_modules")
MODULE_PATH_2 = os.path.join(BASE_DIR, "ccs_v_mz_library_search_modules")
MODULE_PATH_3 = os.path.join(BASE_DIR, "rt_v_mz_library_search_modules")

sys.path.append(MODULE_PATH_1)
sys.path.append(MODULE_PATH_2)
sys.path.append(MODULE_PATH_3)

from analysis import run_analysis, run_library_search_analysis, run_rt_mz_analysis
from config import FILE_PATH
from library_search_module import library_search_plotly
from plotly_graphing import make_plotly_graph  # ✅ Import from `ccs_v_mz_modules`
from rt_v_mz_library_searcher import rt_vs_mz_plotly

UPLOAD_FOLDER = "PIMMS v1.2/imported_libraries"


# ✅ Function to get the latest uploaded library file
def get_latest_library_file():
    """Retrieve the most recent CSV file from the import folder."""
    try:
        files = [
            os.path.join(UPLOAD_FOLDER, f)
            for f in os.listdir(UPLOAD_FOLDER)
            if f.endswith(".csv")
        ]
        if not files:
            print("[WARNING] No library file found in import folder!")
            return None

        latest_file = max(files, key=os.path.getctime)  # Get the most recent file
        print(f"[INFO] Using latest library file: {latest_file}")
        return latest_file

    except Exception as e:
        print(f"[ERROR] Exception while fetching library file: {e}")
        return None


def plot_figure_1(adjusted_df=None, selected_repeating_units=None):
    """
    Processes data, runs analysis, and generates a Plotly figure.

    Args:
        adjusted_df (pd.DataFrame, optional): Dataframe containing processed data.
        selected_repeating_units (dict, optional): User-selected repeating units.

    Returns:
        plotly.graph_objects.Figure: The generated plot.
    """
    if adjusted_df is None:
        adjusted_df = pd.read_csv(FILE_PATH)  # ✅ Always read from FILE_PATH
    if not selected_repeating_units:
        print("[WARNING] No repeating units selected. Returning blank figure.")
        return go.Figure()
    print("\n[INFO] Running `run_analysis()` with selected repeating units...")
    print(f"[DEBUG] Selected repeating units: {selected_repeating_units}")

    # ✅ Run full analysis using selected repeating units
    (
        refined_groups,
        branched_isomers,
        post_source_decay,
        mass_only_groups,
        mass_groups,
    ) = run_analysis(adjusted_df, selected_repeating_units)

    # ✅ Generate Plotly plot
    print("\n[INFO] Generating Plotly plot...")
    fig1 = make_plotly_graph(
        adjusted_df,
        refined_groups,
        branched_isomers,
        post_source_decay,
        mass_only_groups,
        mass_groups,
    )

    return fig1


def plot_figure_2(selected_repeating_units=None):
    """
    Runs library search analysis and generates a Plotly figure.
    """

    # ✅ Step 1: Check if repeating units are selected
    if (
        selected_repeating_units is None
        or not isinstance(selected_repeating_units, dict)
        or len(selected_repeating_units) == 0
    ):
        print("[WARNING] No repeating units selected. Returning blank figure.")
        return go.Figure().update_layout(
            title="CCS vs. m/z",
            template="plotly_dark",
            annotations=[
                dict(
                    text="No repeating units selected",
                    x=0.5,
                    y=0.5,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=20, color="white"),
                )
            ],
        )

    # ✅ Step 2: Run analysis and get results
    filtered_IM_group, stacked_df = run_library_search_analysis(
        selected_repeating_units
    )

    # ✅ Step 3: Ensure stacked_df is valid
    if stacked_df is None or stacked_df.empty:
        print("[WARNING] Stacked dataset is empty. Returning blank figure.")
        return go.Figure().update_layout(
            title="CCS vs. m/z",
            template="plotly_dark",
            annotations=[
                dict(
                    text="No data available",
                    x=0.5,
                    y=0.5,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=20, color="white"),
                )
            ],
        )

    # ✅ Step 4: If no valid homologous series found
    if filtered_IM_group is None or filtered_IM_group.empty:
        print("[WARNING] No valid homologous series found. Returning blank figure.")
        return go.Figure().update_layout(
            title="CCS vs. m/z",
            template="plotly_dark",
            annotations=[
                dict(
                    text="No valid homologous series found",
                    x=0.5,
                    y=0.5,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=20, color="white"),
                )
            ],
        )

    # ✅ Step 5: Generate Plotly figure with valid data
    return library_search_plotly(stacked_df, filtered_IM_group)


def plot_figure_3(selected_repeating_units=None):
    filtered_m_z_RT_groups = run_rt_mz_analysis(selected_repeating_units)
    fig3 = rt_vs_mz_plotly(filtered_m_z_RT_groups)
    return fig3


# ✅ Main execution for testing
if __name__ == "__main__":
    fig2 = plot_figure_2(
        selected_repeating_units={"CF2": 49.9968064}
    )  # Start with no selected units
    # Start with no selected units
    if fig2:
        print("[INFO] Plot generation complete. Displaying plot...")
        pio.show(fig2)
