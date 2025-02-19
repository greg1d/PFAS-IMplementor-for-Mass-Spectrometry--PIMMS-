from dash import dcc, html


def get_layout():
    return html.Div(
        [
            html.H1("PIMMS Data Analysis Dashboard"),
            # ✅ Dropdown for column removal
            dcc.Dropdown(
                id="remove_columns",
                options=[],  # Dynamically populated in the app
                multi=True,
                placeholder="Select columns to remove...",
                className="dropdown",  # ✅ Add CSS class for styling
            ),
            # ✅ CCS vs. m/z Trend Analysis
            html.H2("CCS vs. m/z Trend Analysis"),
            dcc.Graph(id="plotly_graph", className="dash-graph"),  # ✅ Apply class
            # ✅ Library Search Results
            html.H2("Library Search Results"),
            dcc.Graph(
                id="library_search_graph", className="dash-graph"
            ),  # ✅ Apply class
        ],
        className="dashboard-container",  # ✅ Apply overall container class
    )
