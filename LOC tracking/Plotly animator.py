import base64
import os

import plotly.graph_objects as go


def encode_image(image_path):
    """Encode an image to base64 string."""
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return f"data:image/png;base64,{encoded_string}"


def animate_pngs(directory):
    # List all PNG files in the specified directory
    png_files = [f for f in os.listdir(directory) if f.endswith(".png")]

    # Sort PNG files by modification time (oldest first)
    png_files.sort(key=lambda x: os.path.getmtime(os.path.join(directory, x)))

    # Debugging statement to print the list of PNG files
    print(
        f"PNG files in directory '{directory}' (sorted by modification time): {png_files}"
    )

    if not png_files:
        print("No PNG files found in the directory.")
        return

    # Create a figure
    fig = go.Figure()

    # Add the first image to the figure
    first_image_path = os.path.join(directory, png_files[0])
    print(f"Adding first image to the figure: {first_image_path}")
    fig.add_trace(go.Image(source=encode_image(first_image_path)))

    # Create frames for the animation
    frames = []
    for i in range(len(png_files)):
        image_path = os.path.join(directory, png_files[i])
        print(f"Creating frame {i} with image: {image_path}")
        frames.append(
            go.Frame(data=[go.Image(source=encode_image(image_path))], name=str(i))
        )

    # Update the layout with animation settings and hide axes
    fig.update_layout(
        width=1000,  # Adjust width as needed
        height=800,  # Adjust height as needed
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        updatemenus=[
            {
                "buttons": [
                    {
                        "args": [
                            None,
                            {
                                "frame": {"duration": 500, "redraw": True},
                                "fromcurrent": True,
                            },
                        ],
                        "label": "Play",
                        "method": "animate",
                    },
                    {
                        "args": [
                            [None],
                            {
                                "frame": {"duration": 0, "redraw": True},
                                "mode": "immediate",
                                "transition": {"duration": 0},
                            },
                        ],
                        "label": "Pause",
                        "method": "animate",
                    },
                ],
                "direction": "left",
                "pad": {"r": 10, "t": 87},
                "showactive": False,
                "type": "buttons",
                "x": 0.1,
                "xanchor": "right",
                "y": 0,
                "yanchor": "top",
            }
        ],
        sliders=[
            {
                "active": 0,
                "yanchor": "top",
                "xanchor": "left",
                "currentvalue": {
                    "font": {"size": 20},
                    "prefix": "Frame:",
                    "visible": True,
                    "xanchor": "right",
                },
                "transition": {"duration": 300, "easing": "cubic-in-out"},
                "pad": {"b": 10, "t": 50},
                "len": 0.9,
                "x": 0.1,
                "y": 0,
                "steps": [
                    {
                        "args": [
                            [str(k)],
                            {
                                "frame": {"duration": 300, "redraw": True},
                                "mode": "immediate",
                                "transition": {"duration": 300},
                            },
                        ],
                        "label": str(k),
                        "method": "animate",
                    }
                    for k in range(len(png_files))
                ],
            }
        ],
    )

    # Add frames to the figure
    fig.frames = frames
    print(f"Total frames added: {len(frames)}")

    # Show the figure
    fig.show()
    print("Figure displayed.")


if __name__ == "__main__":
    # Specify the directory containing the PNG files
    png_directory = r"LOC tracking outputs"
    animate_pngs(png_directory)
