from dash import Input, Output
import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "ccs_v_mz_modules"))
)
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "ccs_v_mz_library_search_modules")
    )
)

from data_processing import load_standards_report
from graphing import (
    generate_plot,
    generate_library_search_plot,
)  # ✅ Import new graph functions

# ✅ Global repeating_units (Needs to be updated externally)
repeating_units = {
    "CF2": 49.9968064,
    "OCF2": 65.9917214,
    "CF2CF2O": 115.988527,
    "CH2CF2": 64.012456,
    "HF": 20.0062278,
}


def register_callbacks(
    app,
    adjusted_df,
    filtered_IM_group,
    library_match_source,
    refined_groups,
    branched_isomer_groups,
    post_source_decay_groups,
    mass_only_groups,
    mass_groups,
):
    """Registers Dash callbacks for dynamic graph updates and table refresh."""

    @app.callback(
        [
            Output("plotly_graph", "figure"),
            Output("library_search_graph", "figure"),
        ],  # ✅ Added output for second plot
        [Input("remove_columns", "value")],
    )
    def update_graph_callback(remove_columns):
        global repeating_units  # ✅ Ensure the callback gets the updated value
        print(
            f"[DEBUG] update_graph_callback triggered with remove_columns={remove_columns}"
        )
        print(f"[DEBUG] Using repeating units: {repeating_units}")

        # ✅ If repeating_units is empty, show a warning
        if not repeating_units:
            print("[WARNING] No repeating units specified in callback!")

        # ✅ Filter adjusted_df based on selected columns
        filtered_df = (
            adjusted_df.drop(columns=remove_columns, errors="ignore")
            if remove_columns
            else adjusted_df
        )

        # ✅ Generate updated plots
        fig1 = generate_plot(
            filtered_df,
            refined_groups,
            branched_isomer_groups,
            post_source_decay_groups,
            mass_only_groups,
            mass_groups,
        )
        fig2 = generate_library_search_plot(
            filtered_df, filtered_IM_group, library_match_source
        )

        return fig1, fig2  # ✅ Now returning both figures

    @app.callback(
        [Output("standards-table", "columns"), Output("standards-table", "data")],
        [Input("refresh-standards-btn", "n_clicks")],
    )
    def refresh_standards_report(n_clicks):
        print(f"[DEBUG] refresh_standards_report triggered with n_clicks={n_clicks}")

        if n_clicks is None:
            print("[DEBUG] No clicks detected. Returning empty table.")
            return [], []

        df = load_standards_report()
        print(
            f"[DEBUG] Loaded standards report with {len(df)} rows and {len(df.columns)} columns."
        )

        return [{"name": i, "id": i} for i in df.columns], df.to_dict("records")
