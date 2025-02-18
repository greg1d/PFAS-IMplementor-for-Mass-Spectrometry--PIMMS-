import os
import sys

# ✅ Ensure Python Can Find the Module
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get current script's directory
MODULE_PATH_1 = os.path.join(BASE_DIR, "ccs_v_mz_modules")
MODULE_PATH_2 = os.path.join(BASE_DIR, "ccs_v_mz_library_search_modules")

sys.path.append(MODULE_PATH_1)  # Add `ccs_v_mz_modules` to sys.path
sys.path.append(MODULE_PATH_2)  # Add `ccs_v_mz_library_search_modules` to sys.path

from plotly_graphing import make_plotly_graph  # ✅ Import from `ccs_v_mz_modules`
from library_search_module import (
    library_search_plotly,
)  # ✅ Import from `ccs_v_mz_library_search_modules`


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


def generate_library_search_plot(adjusted_df, filtered_IM_group, library_match_source):
    """Generates the final Plotly figure for library search results."""
    print("[INFO] Generating Library Search Plotly graph...")
    return library_search_plotly(adjusted_df, filtered_IM_group, library_match_source)
