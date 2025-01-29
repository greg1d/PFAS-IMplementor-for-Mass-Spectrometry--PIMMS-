import plotly.graph_objects as go

# Define nodes (labels)
labels = [
    "12572",
    "10577",
    "4628",
    "4456",
    "3099",
    "2808",
    "336",
    "271",
    "233",
    "227",
    "End (227)",
    "Split 1 (20)",
    "Split 2 (80)",
    "Split 3 (121)",
]

# Define sources and targets for the flow
sources = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 9]  # Adjusted flow structure
targets = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

# Define link values reflecting new labels
link_values = [10577, 4628, 4456, 3099, 2808, 336, 271, 233, 227, 20, 80, 121]

# Define colors for the split end links and nodes
split_colors = ["#91ED91", "#91ED91", "#91ED91"]  # Light green for links
split_node_colors = ["#008101", "#008101", "#008101"]  # Dark green for nodes

# Assign colors to nodes, making the split nodes match the link colors
node_colors = ["#4682B3"] * 10 + split_node_colors  # Steel blue for main nodes
link_colors = ["#88CEFA"] * 9 + split_colors  # Blue for main links

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
    0.9,
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
            thickness=100,
            line=dict(color="white", width=7),  # White border around nodes
            color=node_colors,
            x=node_x,
            y=node_y,
        ),
        link=dict(source=sources, target=targets, value=link_values, color=link_colors),
    )
)

# Set layout for 4K resolution
fig.update_layout(
    width=3840,  # 4K width
    height=1168,  # Height maintaining the 11.5 x 3.5 inch aspect ratio
)

# Show the figure
fig.show()
