import os
import sys

import dash
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output

sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
from CCS_mz_trend_analysis import (
    mz_repeating_unit_analysis,
    refine_group_by_best_fit,
)
from dash_formatting import get_dash_layout
from plotly_graphing import make_plotly_graph, update_graph

# ✅ Load dataset **once** at startup
file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set test.csv"
adjusted_df = pd.read_csv(file_path)
adjusted_df.columns = adjusted_df.columns.str.strip()  # ✅ Fix column names
# ✅ Identify `.d.DeMP` columns
d_columns = [col for col in adjusted_df.columns if ".d.DeMP" in col]

# ✅ Precompute the **initial graph**
print("[INFO] Generating initial graph...")
initial_groups = mz_repeating_unit_analysis(adjusted_df)
if initial_groups:
    refined_groups, branched_isomer_groups = [], []
    for group in initial_groups:
        refined_group, _, branched_isomers = refine_group_by_best_fit(group)
        refined_groups.append(refined_group)
        branched_isomer_groups.append(branched_isomers)
    initial_figure = make_plotly_graph(
        adjusted_df, refined_groups, branched_isomer_groups
    )
    print("[INFO] Initial graph successfully created.")
else:
    initial_figure = go.Figure()

# ✅ Dash App Setup
app = dash.Dash(__name__, title="IMspector Gadget")  # Set custom title
app.layout = get_dash_layout(d_columns, initial_figure)


# ✅ Dash Callback to Update Graph
@app.callback(Output("plotly_graph", "figure"), [Input("remove_columns", "value")])
def update_graph_callback(remove_columns):
    return update_graph(remove_columns, adjusted_df)  # ✅ Call the imported function


import threading
import webbrowser


# ✅ Open the app automatically in the default browser
def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050/")  # Adjust the URL if needed


if __name__ == "__main__":
    print("[INFO] Starting Dash server...")

    # ✅ Start the browser in a separate thread to avoid blocking
    threading.Timer(1, open_browser).start()

    app.run_server(debug=False)
