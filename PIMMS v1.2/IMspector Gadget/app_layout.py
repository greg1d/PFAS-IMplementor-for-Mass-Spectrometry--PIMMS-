from dash import Dash, dcc, html

# ✅ Initialize Dash app
app = Dash(__name__)

# ✅ Global variable to store uploaded library data
uploaded_library = None


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
                        className="dropdown",  # ✅ Apply CSS class
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
                    # ✅ Library Search Section (WITH UPLOAD BUTTON)
                    html.Div(
                        [
                            html.H2(
                                "Library Search Results", className="section-title"
                            ),
                            # ✅ Upload Button for Library File
                            html.Div(
                                [
                                    dcc.Upload(
                                        id="upload-library",
                                        children=html.Button(
                                            "Upload Library", className="upload-button"
                                        ),
                                        multiple=False,  # ✅ Only allow one file at a time
                                        className="upload-container",
                                    ),
                                    # ✅ Upload status message
                                    html.Div(
                                        id="upload-status", className="upload-status"
                                    ),
                                ],
                                className="upload-wrapper",  # ✅ Style container for positioning
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


app.layout = get_layout()
