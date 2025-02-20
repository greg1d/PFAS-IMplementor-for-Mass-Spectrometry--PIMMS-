from dash import dcc, html

# ✅ Define Available Repeating Units
REPEATING_UNITS = {
    "CF2": 49.9968064,
    "OCF2": 65.9917214,
    "CF2CF2O": 115.988527,
    "CH2CF2": 64.012456,
    "HF": 20.0062278,
}


def get_layout():
    return html.Div(
        [
            # ✅ Page Title
            html.H1("PIMMS Data Analysis Dashboard", className="dashboard-title"),
            # ✅ Dropdown for Selecting Repeating Units
            html.Div(
                [
                    html.Label(
                        "Select repeating units to screen against:",
                        className="dropdown-label",
                    ),
                    dcc.Dropdown(
                        id="repeating-units-dropdown",
                        options=[
                            {"label": unit, "value": unit}
                            for unit in REPEATING_UNITS.keys()
                        ],
                        value=["CF2"],  # ✅ Default selection
                        multi=True,
                        placeholder="Select repeating units...",
                        className="dropdown",
                    ),
                ],
                className="dropdown-container",
            ),
            # ✅ Debugging Output
            html.Div(id="output-text", children="Select a repeating unit above."),
            # ✅ Section: CCS vs. m/z Trend Analysis
            html.H2("CCS vs. m/z Trend Analysis", className="section-title"),
            dcc.Graph(id="plotly_graph", className="dash-graph"),
            # ✅ Dropdown for Column Removal
            html.Div(
                [
                    html.Label("Select columns to remove:", className="dropdown-label"),
                    dcc.Dropdown(
                        id="remove_columns",
                        options=[],  # Dynamically populated in the app
                        multi=True,
                        placeholder="Select columns to remove...",
                        className="dropdown",
                    ),
                ],
                className="dropdown-container",
            ),
            # ✅ Section: Side-by-Side Graphs
            html.Div(
                [
                    # ✅ Library Search Section (WITH UPLOAD BUTTON)
                    html.Div(
                        [
                            html.H2(
                                "Library Search Results", className="section-title"
                            ),
                            html.Div(
                                [
                                    dcc.Upload(
                                        id="upload-library",
                                        children=html.Button(
                                            "Upload Library", className="upload-button"
                                        ),
                                        multiple=False,
                                        className="upload-container",
                                    ),
                                    html.Div(
                                        id="upload-status", className="upload-status"
                                    ),
                                ],
                                className="upload-wrapper",
                            ),
                            dcc.Graph(
                                id="library_search_graph",
                                className="dash-graph half-width",
                            ),
                        ],
                        className="graph-wrapper",
                    ),
                    # ✅ Additional Graph Placeholder
                    html.Div(
                        [
                            html.H2(
                                "Additional Graph Placeholder",
                                className="section-title",
                            ),
                            dcc.Graph(
                                id="additional_graph", className="dash-graph half-width"
                            ),
                        ],
                        className="graph-wrapper",
                    ),
                ],
                className="graph-container",
            ),
        ],
        className="dashboard-container",
    )
