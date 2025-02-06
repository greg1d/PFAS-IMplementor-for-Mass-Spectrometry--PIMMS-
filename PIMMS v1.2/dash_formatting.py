from dash import dcc, html


def get_dash_layout(d_columns, initial_figure):
    """Returns the styled Dash layout with a black background and white text."""
    return html.Div(
        [
            html.H1(
                "IMspector Gadget",
                style={"text-align": "center", "margin-bottom": "20px"},
            ),
            html.Label(
                "Select `.d` columns to remove:",
                style={"font-size": "18px", "margin-bottom": "10px"},
            ),
            dcc.Dropdown(
                id="remove_columns",
                options=[{"label": col, "value": col} for col in d_columns],
                multi=True,
                placeholder="Select columns to remove...",
            ),
            html.Br(),
            dcc.Graph(id="plotly_graph", figure=initial_figure),
        ],
        style={
            "padding": "20px"
        },  # Keep padding, but remove other colors (handled in CSS)
    )
