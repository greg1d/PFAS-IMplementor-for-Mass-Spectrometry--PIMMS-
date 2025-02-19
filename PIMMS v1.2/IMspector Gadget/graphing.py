import os
import sys

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

# ✅ Ensure Python Can Find the Module
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get current script's directory
MODULE_PATH_1 = os.path.join(BASE_DIR, "ccs_v_mz_modules")
MODULE_PATH_2 = os.path.join(BASE_DIR, "ccs_v_mz_library_search_modules")

sys.path.append(MODULE_PATH_1)  # Add `ccs_v_mz_modules` to sys.path
sys.path.append(MODULE_PATH_2)  # Add `ccs_v_mz_library_search_modules` to sys.path
from analysis import run_analysis, run_library_search_analysis
from config import FILE_PATH  # ✅ Import FILE_PATH from config
from library_search_module import library_search_plotly
from plotly_graphing import make_plotly_graph  # ✅ Import from `ccs_v_mz_modules`


def plot_figure_1(
    adjusted_df=None,
):
    """
    Processes data, runs analysis, and generates a Plotly figure.

    Args:
        adjusted_df (pd.DataFrame, optional): If provided, uses this dataframe instead of reading from file.
        file_path (str): Path to CSV file (only used if adjusted_df is not provided).

    Returns:
        plotly.graph_objects.Figure: The generated plot.
    """
    if adjusted_df is None:
        adjusted_df = pd.read_csv(FILE_PATH)  # ✅ Always read from FILE_PATH

    print("\n[INFO] Running `run_analysis()`...")

    # ✅ Run full analysis using imported function
    (
        refined_groups,
        branched_isomers,
        post_source_decay,
        mass_only_groups,
        mass_groups,
    ) = run_analysis(adjusted_df)

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


def plot_figure_2(
    adjusted_df=None,
):
    """
    Runs library search analysis and generates a Plotly figure.

    Returns:
        plotly.graph_objects.Figure: The generated plot.
    """

    if adjusted_df is None:
        adjusted_df = pd.read_csv(FILE_PATH)  # ✅ Always read from FILE_PATH

    # ✅ Run library search analysis
    filtered_IM_group, stacked_df = run_library_search_analysis()

    if stacked_df is None or stacked_df.empty:
        print("\n[WARNING] No stacked dataset available. Exiting.")
        return None

    if filtered_IM_group is None or filtered_IM_group.empty:
        print("\n[WARNING] No homologous series identified. Returning blank graph.")
        fig2 = go.Figure()
        fig2.update_layout(
            title="CCS vs. m/z (No Valid Homologous Series Found)",
            xaxis=dict(title=r"<b><i>m/z</i></b>"),
            yaxis=dict(title="<b>CCS (&#8491;<sup>2</sup>)</b>"),
            template="plotly_dark",
        )
        return fig2  # ✅ Return a blank graph instead of exiting

    print(
        f"[DEBUG] Identified {filtered_IM_group['GroupID'].nunique()} homologous series."
    )

    # ✅ Extract the library match source from the path
    library_match_source = os.path.splitext(
        os.path.basename("PIMMS v1.2/import folder/Library test file 1.csv")
    )[0]

    # ✅ Generate Plotly plot
    print("\n[INFO] Generating Library Search Plotly plot...")
    fig2 = library_search_plotly(stacked_df, filtered_IM_group, library_match_source)

    return fig2


# ✅ Main function to call `plot_figure_1()`
if __name__ == "__main__":
    fig1 = plot_figure_1()
    if fig1:
        print("[INFO] Plot generation complete. Displaying plot...")
        pio.show(fig1)
    fig2 = plot_figure_2()
    if fig2:
        print("[INFO] Plot generation complete. Displaying plot...")
        pio.show(fig2)
