import plotly.graph_objects as go

# Define nodes (labels)
labels = [
    "9077",
    "3350",  # after blank subtraction
    "2538",  # after crude
    "2501",  # after smearing
    "2003",  # after branching
    "1748",  # after monoisotopic
    "410",  # after fluorinated density
    "350",  # after mass defect
    "342",  # after detection frequency
    "332",  # after removing standards
    "331",  # after post decay filter
    "48",  # after regression analysis
    "End (34)",  # after adduct and neutral loss filter
    "Split 1 (5)",
    "Split 2 (15)",
    "Split 3 (14)",
]

# Define flow: 13 sequential steps, then split to 3 nodes
sources = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 12, 12]
targets = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

# Link values and labels for all links
link_values = [
    10577,
    4628,
    4456,
    3099,
    2808,
    336,
    271,
    233,
    227,
    20,
    80,
    121,
    5,
    15,
    14,
]
link_labels = [str(v) for v in link_values]

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

# Create the Sankey diagram
fig = go.Figure(
    go.Sankey(
        arrangement="snap",
        node=dict(
            pad=15,
            thickness=100,
            line=dict(color="white", width=7),
            color=node_colors,
            x=node_x,
            y=node_y,
            label=labels,
        ),
        link=dict(
            source=sources,
            target=targets,
            value=link_values,
            label=link_labels,
            color=link_colors,
        ),
    )
)

# Set layout for 4K resolution
fig.update_layout(
    width=3840,
    height=1168,
)

# Show the figure
fig.show()
