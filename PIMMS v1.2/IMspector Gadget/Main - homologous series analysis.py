import os
import sys
import threading
import webbrowser
import plotly.io as pio
import dash
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output

sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
from CCS_mz_trend_analysis import CCS_v_mz_analysis, mz_repeating_unit_analysis
from dash_formatting import get_dash_layout
from plotly_graphing import make_plotly_graph, update_graph

# ✅ Load Data Before Initializing Layout
file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set test.csv"
adjusted_df = pd.read_csv(file_path)

# ✅ Extract d_columns (Columns containing ".d")
d_columns = [col for col in adjusted_df.columns if ".d" in col]

# ✅ Generate an Initial Empty Figure
initial_figure = go.Figure()

# ✅ Initialize Dash app with Correct Layout
app = dash.Dash(__name__)
app.layout = get_dash_layout(d_columns, initial_figure)  # ✅ Pass Required Arguments


def main():
    """Runs full analysis pipeline and generates an interactive Plotly plot."""

    repeating_units = ["CF2", "OCF2"]
    print("\n[INFO] Starting mz_repeating_unit_analysis...")

    # **Step 1: Identify homologous series**
    mass_groups = mz_repeating_unit_analysis(
        adjusted_df, repeating_units=repeating_units
    )

    # **Step 2: Perform CCS vs. m/z analysis**
    refined_groups, branched_isomer_groups, post_source_decay_groups = [], [], []
    mass_only_groups = {}  # ✅ Ensure this is a dictionary

    print("\n[INFO] Performing CCS_v_mz_analysis on identified mass groups...")
    for idx, (group_id, group_df) in enumerate(mass_groups.groupby("GroupID")):
        print(f"[DEBUG] Analyzing Group {idx + 1} (GroupID: {group_id})")

        refined_data_points, post_source_decay, branched_isomer, mass_only_group = (
            CCS_v_mz_analysis(group_df)
        )

        print(f"[DEBUG] Refined Data Points for Group {idx + 1}: {refined_data_points}")

        # ✅ Store results properly
        if refined_data_points:  # Only add if homologous series exist
            refined_groups.append(refined_data_points)  # ✅ Homologous series points

        branched_isomer_groups.append(branched_isomer)
        post_source_decay_groups.append(post_source_decay)

        # ✅ Store mass-only groups in a dictionary
        if isinstance(mass_only_group, list) and len(mass_only_group) > 0:
            mass_only_groups[f"Group {idx + 1}"] = mass_only_group

    # **Step 3: Print Debugging Before Plotting**
    print("\n[INFO] Final Data Sent to Plot:")
    print(
        f"  - IM Groups: {sum(len(group) for group in refined_groups if group)} points"
    )
    print(
        f"  - Branched Isomers: {sum(len(group) for group in branched_isomer_groups if group)} points"
    )
    print(
        f"  - Post Source Decay: {sum(len(group) for group in post_source_decay_groups if group)} points"
    )
    print(
        f"  - Mass-Only Groups: {sum(len(group) for group in mass_only_groups.values() if group)} points"
    )

    # **Step 4: Generate Plotly plot**
    fig = make_plotly_graph(
        adjusted_df,
        refined_groups,  # ✅ Now properly stored
        branched_isomer_groups,
        post_source_decay_groups,
        mass_only_groups,
    )

    # **Step 5: Display the Plotly plot**
    print("[INFO] Plot generation complete. Displaying plot...")
    pio.show(fig)


# ✅ Define the callback function outside `main()`
@app.callback(Output("plotly_graph", "figure"), [Input("remove_columns", "value")])
def update_graph_callback(remove_columns):
    return update_graph(remove_columns, adjusted_df)


# ✅ Function to Open Browser
def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050/")  # Adjust the URL if needed


if __name__ == "__main__":
    print("[INFO] Starting Dash server...")

    # ✅ Start the browser in a separate thread to avoid blocking
    threading.Timer(1, open_browser).start()

    app.run_server(debug=False)
