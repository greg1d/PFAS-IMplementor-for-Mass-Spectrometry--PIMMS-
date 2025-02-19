from dash import dcc, html


def get_layout():
    return html.Div(
        [
            # ✅ Page Title
            html.H1("PIMMS Data Analysis Dashboard", className="dashboard-title"),
            # ✅ Dropdown for Column Removal
            html.Div(
                [
                    html.Label("Select columns to remove:", className="dropdown-label"),
                    dcc.Dropdown(
                        id="remove_columns",
                        options=[],  # Dynamically populated in the app
                        multi=True,
                        placeholder="Select columns to remove...",
                        className="dropdown",  # ✅ Add CSS class for styling
                    ),
                ],
                className="dropdown-container",  # ✅ Wrap dropdown in a div for styling
            ),
            # ✅ Section: CCS vs. m/z Trend Analysis
            html.H2("CCS vs. m/z Trend Analysis", className="section-title"),
            dcc.Graph(id="plotly_graph", className="dash-graph"),
            # ✅ Section: Side-by-Side Graphs
            html.Div(
                [
                    html.Div(
                        [
                            html.H2(
                                "Library Search Results", className="section-title"
                            ),
                            dcc.Graph(
                                id="library_search_graph",
                                className="dash-graph half-width",
                            ),
                        ],
                        className="graph-wrapper",
                    ),
                    html.Div(
                        [
                            html.H2(
                                "Additional Graph Placeholder",
                                className="section-title",
                            ),
                            dcc.Graph(
                                id="additional_graph",
                                className="dash-graph half-width",
                            ),
                        ],
                        className="graph-wrapper",
                    ),
                ],
                className="graph-container",  # ✅ Ensure graphs are side by side
            ),
        ],
        className="dashboard-container",  # ✅ Apply overall container class
    )
