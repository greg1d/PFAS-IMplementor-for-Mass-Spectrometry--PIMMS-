import os
import sys
import threading
import webbrowser

# Add the correct module path
script_dir = os.path.dirname(__file__)  # Get the directory of the current script
sys.path.append(script_dir)  # Ensure the script's directory is in the path

import dash
from analysis import run_analysis, run_library_search_analysis
from app_layout import get_layout
from callbacks import register_callbacks
from data_processing import load_adjusted_data
from config import LIBRARY_PATH  # ✅ Import LIBRARY_PATH

print("[DEBUG] Module imports successful!")

# ✅ Load Data
adjusted_df = load_adjusted_data()

# ✅ Run Library Search Analysis Before Dash Starts
print("[INFO] Running library search analysis...")
filtered_IM_group, stacked_df = run_library_search_analysis()

if stacked_df is None or stacked_df.empty:
    print("[WARNING] Stacked dataset is empty! Check data sources.")

if filtered_IM_group is None or filtered_IM_group.empty:
    print("[WARNING] No valid homologous series identified.")

# ✅ Extract `library_match_source` from `LIBRARY_PATH` dynamically
library_match_source = os.path.splitext(os.path.basename(LIBRARY_PATH))[0]  # ✅ Fix

# ✅ Run CCS vs. m/z trend analysis
(
    refined_groups,
    branched_isomer_groups,
    post_source_decay_groups,
    mass_only_groups,
    mass_groups,
) = run_analysis(adjusted_df)

# ✅ Initialize Dash App
app = dash.Dash(__name__)

# ✅ Set Layout
app.layout = get_layout()

# ✅ Register Callbacks with All Required Arguments
register_callbacks(
    app,
    adjusted_df,
    filtered_IM_group,
    library_match_source,
    refined_groups,
    branched_isomer_groups,
    post_source_decay_groups,
    mass_only_groups,
    mass_groups,
)


# ✅ Open Browser Automatically
def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050/")


if __name__ == "__main__":
    print("[INFO] Starting Dash server...")

    # ✅ Start browser in a separate thread
    threading.Timer(1, open_browser).start()

    # ✅ Run Dash Server
    app.run_server(debug=False)
