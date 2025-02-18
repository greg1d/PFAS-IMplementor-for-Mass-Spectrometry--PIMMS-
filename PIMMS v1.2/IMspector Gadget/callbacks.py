from dash import Input, Output
import sys
import os

# ✅ Ensure Python Can Find the Module
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "ccs_v_mz_modules"))
)
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "ccs_v_mz_library_search_modules")
    )
)
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)  # Move up to locate `config.py`

# ✅ Import necessary functions
try:
    from config import REPEATING_UNITS  # ✅ Import repeating_units globally

    print(f"[DEBUG] Successfully imported repeating_units: {REPEATING_UNITS}")
except ModuleNotFoundError:
    print("[ERROR] Could not import `REPEATING_UNITS` from config.py!")
    sys.exit(1)

from data_processing import load_standards_report
from graphing import (
    plotly_ccs_v_mz_sample_plot,  # ✅ Import the correct graphing function
    generate_library_search_plot,
)


def register_callbacks(
    app,
    adjusted_df,
    filtered_IM_group,
    library_match_source,
):
    """Registers Dash callbacks for dynamic graph updates and table refresh."""

    @app.callback(
        [
            Output(
                "plotly_graph", "figure"
            ),  # ✅ This updates the main CCS vs. m/z plot
            Output("library_search_graph", "figure"),
        ],
        [Input("remove_columns", "value")],
    )
    def update_graph_callback(remove_columns):
        print(
            f"[DEBUG] update_graph_callback triggered with remove_columns={remove_columns}"
        )
        print(f"[DEBUG] Using repeating units: {REPEATING_UNITS}")

        # ✅ If repeating_units is empty, show a warning
        if not REPEATING_UNITS:
            print("[WARNING] No repeating units specified in callback!")

        # ✅ Filter `adjusted_df` based on selected columns
        filtered_df = (
            adjusted_df.drop(columns=remove_columns, errors="ignore")
            if remove_columns
            else adjusted_df
        )

        # ✅ Generate updated plots dynamically
        fig = plotly_ccs_v_mz_sample_plot(filtered_df)  # ✅ Use correct function
        fig2 = generate_library_search_plot(
            filtered_df, filtered_IM_group, library_match_source
        )

        return fig, fig2  # ✅ Now returning both figures dynamically

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
