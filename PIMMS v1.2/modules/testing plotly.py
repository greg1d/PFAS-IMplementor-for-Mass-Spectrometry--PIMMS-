import dash
from dash import dcc, html
import plotly.graph_objects as go
import pandas as pd
import webbrowser
from threading import Timer
from dash.dependencies import Input, Output

# Sample Data
data = {
    "m/z": [100, 200, 300, 400, 500],
    "CCS": [50, 100, 150, 200, 250],
    "Column_A": [1, 0, 3, 0, 5],
    "Column_B": [5, 4, 3, 2, 0],
    "Column_C": [2, 3, 0, 5, 6],
}

df = pd.DataFrame(data)

# Initialize Dash App with proper meta tags
app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.title = "My Interactive Scatter Plot"  # ✅ Correctly updates tab name

# Layout
app.layout = html.Div(
    [
        html.H3("Select Columns to Display:"),
        dcc.Checklist(
            id="column-selector",
            options=[
                {"label": "Column A", "value": "Column_A"},
                {"label": "Column B", "value": "Column_B"},
                {"label": "Column C", "value": "Column_C"},
            ],
            value=["Column_A", "Column_B", "Column_C"],  # Default: Show all
            inline=True,
        ),
        dcc.Graph(id="scatter-plot"),
    ]
)


# Callback to update graph
@app.callback(Output("scatter-plot", "figure"), Input("column-selector", "value"))
def update_graph(selected_columns):
    fig = go.Figure()

    # Add traces for selected columns
    for col in selected_columns:
        valid_rows = df[df[col] > 0]  # Filter out zero values
        fig.add_trace(
            go.Scatter(
                x=valid_rows["m/z"],
                y=valid_rows["CCS"],
                mode="markers",
                marker=dict(size=10),
                name=col,
            )
        )

    # Layout settings
    fig.update_layout(
        title="Interactive Scatter Plot", xaxis_title="m/z", yaxis_title="CCS"
    )

    return fig


# Function to open browser only once
def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050/")


# Run app with auto-browser open, but prevent multiple instances
if __name__ == "__main__":
    Timer(1, open_browser).start()  # Open browser after 1s delay
    app.run_server(debug=True, use_reloader=False)  # Prevent multiple runs
