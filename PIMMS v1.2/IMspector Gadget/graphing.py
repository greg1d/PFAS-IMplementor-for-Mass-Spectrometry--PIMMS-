import os
import sys

# ✅ Ensure Python Can Find the Module
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get current script's directory
MODULE_PATH = os.path.join(BASE_DIR, "ccs_v_mz_modules")
sys.path.append(MODULE_PATH)  # Add it to sys.path

# ✅ Now Import Modules
from plotly_graphing import make_plotly_graph


def generate_plot(
    adjusted_df,
    refined_groups,
    branched_isomer_groups,
    post_source_decay_groups,
    mass_only_groups,
    mass_groups,
):
    """Generates the final Plotly figure."""
    print("[INFO] Generating Plotly graph...")
    return make_plotly_graph(
        adjusted_df,
        refined_groups,
        branched_isomer_groups,
        post_source_decay_groups,
        mass_only_groups,
        mass_groups,
    )
