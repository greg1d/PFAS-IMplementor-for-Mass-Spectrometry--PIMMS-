import logging
import time

import dash
import numpy as np
import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Input, Output, State
from scipy.interpolate import splev, splprep
from scipy.spatial import ConvexHull

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = dash.Dash(__name__)

# ** Sample Data: Two Mass-Only Groups **
mass_only_groups = {
    "Group A": [(440.92, 200.0), (374.93, 60.0), (506.91, 40.0)],
    "Group B": [(308.94, 100.0), (572.90, 100.0), (400.91, 20.0)],
}

# ** Non-Mass-Only Points **
other_points = [
    (600.00, 150.0),  # Example of a point that should NOT trigger any boundary
]


# ** Generate Figure Function **
def create_figure(active_group=None):
    fig = go.Figure()

    # ** Plot Mass-Only Points **
    for group_name, points in mass_only_groups.items():
        for mz, ccs in points:
            fig.add_trace(
                go.Scatter(
                    x=[mz],
                    y=[ccs],
                    mode="markers",
                    marker=dict(size=8, color="green"),
                    name=f"Mass-Only ({group_name})",
                    legendgroup=f"mass_only_group_{group_name}",
                    showlegend=False,
                    hoverinfo="text",
                    hovertext=f"m/z: {mz:.4f}<br>CCS: {ccs:.2f}<br>Group: {group_name}",
                    customdata=[[mz, ccs, group_name]],  # ✅ Corrected formatting
                )
            )

    # ** Plot Other Points (Not in Mass-Only Groups) **
    for mz, ccs in other_points:
        fig.add_trace(
            go.Scatter(
                x=[mz],
                y=[ccs],
                mode="markers",
                marker=dict(size=8, color="red"),  # Different color
                name="Other Points",
                showlegend=False,
                hoverinfo="text",
                hovertext=f"m/z: {mz:.4f}<br>CCS: {ccs:.2f}<br>Classification: Other",
                customdata=[
                    [mz, ccs, None]
                ],  # ✅ Assign None to prevent boundary trigger
            )
        )

    # ** Draw Convex Hull for Active Group Only **
    # ** Draw Smooth Curved Boundary for Active Group **
    if active_group and active_group in mass_only_groups:
        points = np.array(mass_only_groups[active_group])
        if len(points) > 2:  # Convex hull requires at least 3 points
            hull = ConvexHull(points)
            hull_x = points[hull.vertices, 0].tolist()
            hull_y = points[hull.vertices, 1].tolist()

            # Close the polygon
            hull_x.append(hull_x[0])
            hull_y.append(hull_y[0])

            tck, u = splprep(
                [hull_x, hull_y], s=0.1, per=True
            )  # `s` controls smoothness
            smooth_x, smooth_y = splev(np.linspace(0, 1, 100), tck)

            fig.add_trace(
                go.Scatter(
                    x=smooth_x,
                    y=smooth_y,
                    fill="toself",
                    mode="lines",
                    line=dict(color="green", width=2, dash="dash"),
                    fillcolor="rgba(0, 255, 0, 0.2)",  # Semi-transparent green
                    name=f"Boundary ({active_group})",
                    legendgroup=f"mass_only_group_{active_group}",
                    hoverinfo="skip",  # Hide hover text for boundary
                    showlegend=False,
                    visible=True,  # ✅ Controlled dynamically
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


# ** Dash Layout **
app.layout = html.Div(
    [
        dcc.Graph(id="scatter-plot", figure=create_figure()),
        dcc.Interval(
            id="interval-timer", interval=1000, n_intervals=0
        ),  # ✅ Check every second
        dcc.Store(id="last-hover-time", data=0),  # ✅ Track last hover timestamp
        dcc.Store(id="active-group", data=None),  # ✅ Track active mass-only group
    ]
)


@app.callback(
    [
        Output("scatter-plot", "figure"),
        Output("last-hover-time", "data"),
        Output("active-group", "data"),
    ],
    [Input("scatter-plot", "hoverData"), Input("interval-timer", "n_intervals")],
    [State("last-hover-time", "data"), State("active-group", "data")],
)
def toggle_boundary_and_timer(hover_data, n_intervals, last_hover_time, active_group):
    logging.debug("\n[DEBUG] Hover Event Triggered")
    current_time = time.time()

    # ** Check if Hover Event is Valid **
    if hover_data and "points" in hover_data:
        logging.debug(f"[DEBUG] Hover Data Received: {hover_data}")

        hovered_point = hover_data["points"][0]  # Extract hovered point
        hovered_customdata = hovered_point.get("customdata", [])

        if isinstance(hovered_customdata, list) and len(hovered_customdata) >= 3:
            hovered_group = hovered_customdata[2]  # ✅ Get the group name

            # ** Hide the boundary if hovering over a non-mass-only point **
            if hovered_group is None:
                logging.debug(
                    "[INFO] Hovered over a Non-Mass-Only Point: Hiding Boundary"
                )
                return create_figure(active_group=None), current_time, None

            logging.debug(f"[DEBUG] Hovered over Mass-Only Group: {hovered_group}")

            if hovered_group != active_group:
                logging.debug(f"[INFO] Updating Active Group: {hovered_group}")
                return (
                    create_figure(active_group=hovered_group),
                    current_time,
                    hovered_group,
                )

    # ** Check if Boundary Should be Hidden After 5s **
    if active_group and (current_time - last_hover_time > 5):
        logging.debug(
            f"[INFO] No Hover in Last 5s, Hiding Boundary for: {active_group}"
        )
        return create_figure(active_group=None), current_time, None

    logging.debug(f"[INFO] No Updates Needed, Active Group: {active_group}")
    return dash.no_update, last_hover_time, active_group


if __name__ == "__main__":
    app.run_server(debug=True)
