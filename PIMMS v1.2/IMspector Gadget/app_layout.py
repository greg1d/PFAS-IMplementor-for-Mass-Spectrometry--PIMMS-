from dash import dash_table, dcc, html
from data_processing import load_adjusted_data

adjusted_df = load_adjusted_data()

d_columns = [col for col in adjusted_df.columns if ".d.DeMP" in col]


def get_layout(fig1=None):
    """Returns the Dash app layout with default figures."""
    return html.Div(
        [
            html.H1("PIMMS Data Analysis Dashboard"),
            # Sample Selection Dropdown
            dcc.Dropdown(
                id="remove_columns",
                options=[{"label": col, "value": col} for col in d_columns],
                multi=True,
                placeholder="Select Samples to Hide from Report...",
            ),
            # Main Plot (CCS vs. m/z)
            html.H2("CCS vs. m/z Trend Analysis"),
            dcc.Graph(id="plotly_graph", figure=fig1),  # ✅ Set default figure
            # Library Search Plot
            html.H2("Library Search Results"),
            dcc.Graph(id="library_search_graph"),  # ✅ Set default figure
            html.Hr(),
            # Standards Report Panela
            html.H2("Standards Report"),
            html.Button(
                "Refresh Standards Report", id="refresh-standards-btn", n_clicks=0
            ),
            dash_table.DataTable(
                id="standards-table",
                columns=[],
                data=[],
                style_table={"overflowX": "auto"},
            ),
        ]
    )
