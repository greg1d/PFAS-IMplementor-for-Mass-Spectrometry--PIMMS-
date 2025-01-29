import plotly.graph_objects as go

# Define nodes (labels)
labels = [
    "12572",
    "10577",
    "4456",
    "3099",
    "2808",
    "336",
    "271",
    "233",
    "End (227)",
    "Split 1 (20)",
    "Split 2 (80)",
    "Split 3 (171)",
]

# Define sources and targets for the flow
sources = [0, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8]  # Adjusted flow structure
targets = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

# Define link values reflecting new labels
link_values = [10577, 4456, 3099, 2808, 336, 271, 233, 227, 20, 80, 127]

# Define colors for the split end links and nodes
split_colors = ["#91ED91", "#91ED91", "#91ED91"]  # Light green for links
split_node_colors = ["#008101", "#008101", "#008101"]  # Dark green for nodes

# Assign colors to nodes, making the split nodes match the link colors
node_colors = ["#4682B3"] * 9 + split_node_colors  # Steel blue for main nodes
link_colors = ["#88CEFA"] * 8 + split_colors  # Blue for main links

# Define node positions for better spacing
node_x = [
    0,
    0.1,
    0.2,
    0.3,
    0.4,
    0.5,
    0.6,
    0.7,
    0.8,
    1,
    1,
    1,
]  # Spreading final splits apart
node_y = [
    0.5,
    0.5,
    0.5,
    0.5,
    0.5,
    0.5,
    0.5,
    0.5,
    0.5,
    0.2,
    0.5,
    0.8,
]  # Different vertical positions for split nodes

# Create the Sankey diagram
fig = go.Figure(
    go.Sankey(
        arrangement="snap",  # Keeps the nodes in fixed positions
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="white", width=2),  # White border around nodes
            color=node_colors,
            x=node_x,
            y=node_y,
        ),
        link=dict(source=sources, target=targets, value=link_values, color=link_colors),
    )
)

# Set title
fig.update_layout(
    title_text="Sankey Diagram with Custom Colors and Spread Out End Nodes",
    font_size=10,
)

# Show the figure
fig.show()
