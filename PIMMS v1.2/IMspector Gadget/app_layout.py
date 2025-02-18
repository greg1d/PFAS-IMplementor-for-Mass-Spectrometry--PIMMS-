from dash import dcc, html


def get_layout():
    return html.Div(
        [
            html.H1("PIMMS Data Analysis Dashboard"),
            # Dropdown for column removal
            dcc.Dropdown(
                id="remove_columns",
                options=[],  # Dynamically populated in the app
                multi=True,
                placeholder="Select columns to remove...",
            ),
            html.H2("CCS vs. m/z Trend Analysis"),
            dcc.Graph(id="plotly_graph"),  # ✅ Ensure this exists!
            html.H2("Library Search Results"),
            dcc.Graph(id="library_search_graph"),  # ✅ Ensure this exists!
        ]
    )
