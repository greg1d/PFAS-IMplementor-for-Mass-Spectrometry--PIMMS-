import os
import sys
import threading
import webbrowser

# Add the correct module path
script_dir = os.path.dirname(__file__)  # Get the directory of the current script
sys.path.append(script_dir)  # Ensure the script's directory is in the path

import dash
from analysis import run_library_search_analysis
from app_layout import get_layout
from data_processing import load_adjusted_data
from config import LIBRARY_PATH  # ✅ Import LIBRARY_PATH
from graphing import plotly_ccs_v_mz_sample_plot
from graphing import plot_figure_1, plot_figure_2

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

# ✅ Generate initial figures **BEFORE** starting the Dash app
fig1 = plotly_ccs_v_mz_sample_plot(adjusted_df)


print("[INFO] Generating initial plots before starting Dash...")
fig1 = plot_figure_1()
fig2 = plot_figure_2()
# ✅ Initialize Dash App
app = dash.Dash(__name__)

# ✅ Set Layout with Default Figures
app.layout = get_layout()  # ✅ Correct!

register_callbacks(app, adjusted_df)

# ✅ Set Layout with Default Figures
app.layout = get_layout(fig1)
# ✅ Set Layout
app.layout = get_layout()


# ✅ Open Browser Automatically
def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050/")


if __name__ == "__main__":
    print("[INFO] Starting Dash server...")

    # ✅ Start browser in a separate thread
    threading.Timer(1, open_browser).start()

    # ✅ Run Dash Server
    app.run_server(debug=False)
