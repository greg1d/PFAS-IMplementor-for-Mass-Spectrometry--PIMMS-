import plotly.graph_objects as go

# Define nodes (labels)
labels = [
    "Start (12572)",
    "10577",
    "4628",
    "4456",
    "3099",
    "2808",
    "336",
    "End (271)",
    "Split 1 (20)",
    "Split 2 (80)",
    "Split 3 (171)",
]

# Define sources and targets for the flow
sources = list(range(len(labels) - 4)) + [7, 7, 7]  # Last node (271) splits into three
targets = list(range(1, len(labels) - 3)) + [8, 9, 10]

# Define link values
values = [12572, 10577, 4628, 4456, 3099, 2808, 336, 271, 20, 80, 171]
link_values = values[1:]

# Define colors for the split end links and nodes
split_colors = ["rgba(0,128,0,0.5)", "rgba(34,139,34,0.5)", "rgba(50,205,50,0.5)"]

# Assign colors to nodes, making the split nodes match the link colors
node_colors = ["blue"] * 8 + split_colors
link_colors = ["rgba(0,0,255,0.5)"] * 7 + split_colors

# Create the Sankey diagram
fig = go.Figure(
    go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=node_colors,
        ),
        link=dict(source=sources, target=targets, value=link_values, color=link_colors),
    )
)

# Set title
fig.update_layout(title_text="Sankey Diagram with Split End", font_size=10)

# Show the figure
fig.show()
