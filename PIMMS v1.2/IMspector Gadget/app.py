import os
import sys
import threading
import webbrowser

# Add the correct module path
script_dir = os.path.dirname(__file__)  # Get the directory of the current script
sys.path.append(script_dir)  # Ensure the script's directory is in the path

import dash
from app_layout import get_layout
from callbacks import register_callbacks
from data_processing import load_adjusted_data
from graphing import plot_figure_1, plot_figure_2

print("[DEBUG] Module imports successful!")

# ✅ Load Data
adjusted_df = load_adjusted_data()

print("[INFO] Generating initial plots before starting Dash...")
fig1 = plot_figure_1(adjusted_df)
fig2 = plot_figure_2()

# ✅ Initialize Dash App
app = dash.Dash(__name__)

# ✅ Register Callbacks FIRST before setting layout
register_callbacks(app, adjusted_df)  # 🔹 Move this BEFORE layout

# ✅ Set Layout
app.layout = get_layout()  # ✅ Ensures upload button is included


# ✅ Open Browser Automatically
def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050/")


if __name__ == "__main__":
    print("[INFO] Starting Dash server...")

    # ✅ Start browser in a separate thread
    threading.Timer(1, open_browser).start()

    # ✅ Run Dash Server
    app.run_server(debug=False)  # 🔹 Enable debug mode to catch callback issues
