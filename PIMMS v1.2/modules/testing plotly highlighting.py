import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output
import numpy as np
from scipy.spatial import ConvexHull

# Sample Data (Replace with actual mass-only group data)
mass_only_points = [
    (440.92, 200.0),
    (374.93, 60.0),
    (506.91, 40.0),
    (308.94, 100.0),
    (572.90, 100.0),
]

# Compute Convex Hull (Boundary)
if len(mass_only_points) > 2:
    points = np.array(mass_only_points)
    hull = ConvexHull(points)
    hull_x = points[hull.vertices, 0].tolist()
    hull_y = points[hull.vertices, 1].tolist()
    hull_x.append(hull_x[0])  # Close the polygon
    hull_y.append(hull_y[0])
else:
    hull_x, hull_y = [], []  # No boundary if less than 3 points

# Initialize Dash app
app = dash.Dash(__name__)


# Define initial figure
def create_figure(show_boundary=False):
    fig = go.Figure()

    # ** Plot Mass-Only Points (Always Visible in Green) **
    for mz, ccs in mass_only_points:
        fig.add_trace(
            go.Scatter(
                x=[mz],
                y=[ccs],
                mode="markers",
                marker=dict(size=8, color="green"),
                name="Mass-Only",
                legendgroup="mass_only_group",
                showlegend=False,
                hoverinfo="text",
                hovertext=f"m/z: {mz:.4f}<br>CCS: {ccs:.2f}<br>Classification: Mass-Only",
                customdata=[mz, ccs],  # For interaction
            )
        )

    # ** Plot Convex Hull Boundary (Initially Hidden, Controlled by Callback) **
    fig.add_trace(
        go.Scatter(
            x=hull_x,
            y=hull_y,
            fill="toself",
            mode="lines",
            line=dict(color="green", width=2, dash="dash"),
            fillcolor="rgba(0, 255, 0, 0.2)",  # Semi-transparent green
            name="Mass-Only Group Boundary",
            legendgroup="mass_only_group",
            hoverinfo="skip",
            showlegend=False,
            visible=show_boundary,  # Control visibility dynamically
        )
    )

    fig.update_layout(
        title="CCS vs m/z Trend Analysis",
        xaxis=dict(title="m/z"),
        yaxis=dict(title="CCS"),
        template="plotly_dark",
        legend=dict(itemclick="toggle", itemdoubleclick="toggleothers"),
    )
    return fig


# Define App Layout
app.layout = html.Div(
    [
        dcc.Graph(id="scatter-plot", figure=create_figure()),
        dcc.Store(id="hover-state", data=False),  # Store hover state
    ]
)


# Callback to toggle visibility of boundary based on hover event
@app.callback(Output("scatter-plot", "figure"), Input("scatter-plot", "hoverData"))
def toggle_boundary(hover_data):
    """Shows boundary when hovering over Mass-Only points, hides otherwise."""
    if hover_data and "points" in hover_data:
        hovered_mz = hover_data["points"][0]["x"]
        hovered_ccs = hover_data["points"][0]["y"]

        # Check if hovered point belongs to mass-only group
        if (hovered_mz, hovered_ccs) in mass_only_points:
            return create_figure(show_boundary=True)

    return create_figure(show_boundary=False)


# Run Dash app
if __name__ == "__main__":
    app.run_server(debug=True)
