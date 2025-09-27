import plotly.graph_objects as go

# Define nodes (labels)
labels = [
    "9077",
    "3350",  # 1 after blank subtraction
    "2538",  # 2 after crude
    "2501",  # 3 after smearing
    "2003",  # 4 after branching
    "1748",  # 5 after monoisotopic
    "410",  # 6 after fluorinated density
    "350",  # 7 after mass defect
    "342",  # 8 after detection frequency
    "332",  # 9 after removing standards
    "331",  # 10 after post decay filter
    "48",  # 11 after regression analysis
    "End (34)",  # 12 after adduct and neutral loss filter
    "Split 1 (5)",
    "Split 2 (15)",
    "Split 3 (14)",
]

# Define flow: 13 sequential steps, then split to 3 nodes
sources = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 12, 12]
targets = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

# Link values and labels for all links
link_values = [
    9077,
    3350,
    2538,
    2501,
    2003,
    1748,
    410,
    350,
    342,
    332,
    331,
    48,
    34,
    15,
    14,
]

# Define colors for the split end links and nodes
split_colors = ["#91ED91"] * 3  # Light green
split_node_colors = ["#008101"] * 3  # Dark green

# Assign node colors: 13 main + 3 split
node_colors = ["#4682B3"] * 13 + split_node_colors
link_colors = ["#88CEFA"] * 12 + split_colors

# Define node positions for better spacing
node_x = [
    0.0,
    0.07,
    0.14,
    0.21,
    0.28,
    0.35,
    0.42,
    0.49,
    0.56,
    0.63,
    0.70,
    0.77,
    0.84,
    0.94,
    0.94,
    0.94,
]
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
    0.5,
    0.5,
    0.5,
    0.2,
    0.5,
    0.8,
]

# Create the Sankey diagram with text hidden
fig = go.Figure(
    go.Sankey(
        arrangement="fixed",
        node=dict(
            pad=0,
            thickness=100,
            line=dict(color="white", width=0),
            color=node_colors,
            x=node_x,
            y=node_y,
            label=[""] * len(labels),  # Hide node text
            hovertemplate=None,  # Hide hover text for nodes
        ),
        link=dict(
            source=sources,
            target=targets,
            value=link_values,
            label=[""] * len(link_values),  # Hide link text
            color=link_colors,
            hovertemplate=None,  # Hide hover text for links
        ),
    )
)

# Set layout for 4K resolution
fig.update_layout(
    width=3840,
    height=1168,
    showlegend=False,  # No legend
)

# Show the figure
fig.show()
fig.write_image("sankey_filtering_performance.png")
9077
