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

    Args:
        selected_repeating_units (dict, optional): User-selected repeating units.

    Returns:
        plotly.graph_objects.Figure: The generated plot.
    """
    if (
        selected_repeating_units is None
        or not isinstance(selected_repeating_units, dict)
        or len(selected_repeating_units) == 0
    ):
        print("[WARNING] No repeating units selected. Returning blank figure.")
        fig2 = go.Figure()
        fig2.update_layout(
            title="CCS vs. m/z (No Repeating Units Selected)",
            xaxis=dict(title=r"<b><i>m/z</i></b>"),
            yaxis=dict(title="<b>CCS (&#8491;<sup>2</sup>)</b>"),
            template="plotly_dark",
        )
        return fig2  # ✅ Skip analysis and return an empty plot

    filtered_IM_group, stacked_df = run_library_search_analysis(
        selected_repeating_units
    )

    if stacked_df is None or stacked_df.empty:
        print("[WARNING] stacked_df is empty. Returning empty plot.")
        fig2 = go.Figure()
        fig2.update_layout(
            title="CCS vs. m/z (No Data Available)",
            xaxis=dict(title=r"<b><i>m/z</i></b>"),
            yaxis=dict(title="<b>CCS (&#8491;<sup>2</sup>)</b>"),
            template="plotly_dark",
        )
        return fig2  # ✅ Return a blank figure instead of breaking

    # ✅ Step 3: If no valid homologous series found
    if filtered_IM_group is None or filtered_IM_group.empty:
        print("[WARNING] No valid homologous series found. Returning empty plot.")
        fig2 = go.Figure()
        fig2.update_layout(
            title="CCS vs. m/z (No Valid Homologous Series Found)",
            xaxis=dict(title=r"<b><i>m/z</i></b>"),
            yaxis=dict(title="<b>CCS (&#8491;<sup>2</sup>)</b>"),
            template="plotly_dark",
        )
        return fig2  # ✅ Return a blank figure instead of breaking

    # ✅ Step 4: Generate Plotly figure with valid data
    fig2 = library_search_plotly(stacked_df, filtered_IM_group)
    return fig2


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
