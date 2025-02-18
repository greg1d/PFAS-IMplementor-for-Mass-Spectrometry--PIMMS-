import os
import sys
import threading
import webbrowser

# Add the correct module path
script_dir = os.path.dirname(__file__)  # Get the directory of the current script
sys.path.append(os.path.dirname(__file__))  # Add the script's directory

import dash
from analysis import run_analysis, run_library_search_analysis
from app_layout import get_layout
from callbacks import register_callbacks
from data_processing import load_adjusted_data
from graphing import generate_plot

print("[DEBUG] Module imports successful!")


# ✅ Ensure module paths are correctly added

# ✅ Initialize Dash App
app = dash.Dash(__name__)

# ✅ Load Data
adjusted_df = load_adjusted_data()
# ✅ Run Library Search Analysis Before Dash Starts
print("[INFO] Running library search analysis...")
filtered_IM_group, stacked_df = run_library_search_analysis()


app.layout = get_layout()

# ✅ Register Callbacks
register_callbacks(app, adjusted_df)


def main():
    """Runs full analysis pipeline and generates an interactive Plotly plot."""
    print("[INFO] Starting mz_repeating_unit_analysis...")

    # ✅ Run the CCS vs. m/z trend analysis
    (
        refined_groups,
        branched_isomer_groups,
        post_source_decay_groups,
        mass_only_groups,
        mass_groups,
    ) = run_analysis(adjusted_df)

    if not refined_groups:
        print("[WARNING] No homologous series identified. Exiting.")
        return

    # ✅ Generate Plot
    fig = generate_plot(
        adjusted_df,
        refined_groups,
        branched_isomer_groups,
        post_source_decay_groups,
        mass_only_groups,
        mass_groups,
    )

    # ✅ Display Plot
    print("[INFO] Plot generation complete. Displaying plot...")
    fig.show()


# ✅ Open Browser Automatically
def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050/")


if __name__ == "__main__":
    print("[INFO] Starting Dash server...")

    # ✅ Start browser in a separate thread
    threading.Timer(1, open_browser).start()

    # ✅ Run Dash Server
    app.run_server(debug=False)
