import plotly.graph_objects as go
import pandas as pd
import dash
from dash import dcc, html, Input, Output

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
from CCS_mz_trend_analysis import (
    mz_repeating_unit_analysis,
    refine_group_by_best_fit,
)
from plotly_graphing import make_plotly_graph, update_graph

# ✅ Load dataset **once** at startup
file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set.csv"
adjusted_df = pd.read_csv(file_path)

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
app = dash.Dash(__name__)

app.layout = html.Div(
    [
        html.H1("CCS vs m/z Trends", style={"text-align": "center"}),
        # ✅ Dropdown for selecting `.d` columns to remove
        html.Label("Select `.d` columns to remove:"),
        dcc.Dropdown(
            id="remove_columns",
            options=[{"label": col, "value": col} for col in d_columns],
            multi=True,
            placeholder="Select columns to remove...",
        ),
        # ✅ Graph Output
        dcc.Graph(id="plotly_graph", figure=initial_figure),
    ]
)


# ✅ Dash Callback to Update Graph
@app.callback(Output("plotly_graph", "figure"), [Input("remove_columns", "value")])
def update_graph_callback(remove_columns):
    return update_graph(remove_columns, adjusted_df)  # ✅ Call the imported function


# ✅ Run Dash App
if __name__ == "__main__":
    print("[INFO] Starting Dash server...")
    app.run_server(debug=True)
