from dash import dash_table, dcc, html
from data_processing import load_adjusted_data

adjusted_df = load_adjusted_data()


def get_layout():
    """Returns the Dash app layout."""
    return html.Div(
        [
            html.H1("PIMMS Data Analysis Dashboard"),
            # Graph Panel
            dcc.Graph(id="plotly_graph"),
            dcc.Dropdown(
                id="remove_columns",
                options=[{"label": col, "value": col} for col in adjusted_df.columns],
                multi=True,
                placeholder="Select columns to remove",
            ),
            html.Hr(),
            # Standards Report Panel
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
