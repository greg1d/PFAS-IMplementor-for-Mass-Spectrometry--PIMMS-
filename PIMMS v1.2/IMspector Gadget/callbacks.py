import os
import sys

# ✅ Ensure Python Can Find `config.py`
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "ccs_v_mz_modules"))
)
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "ccs_v_mz_library_search_modules")
    )
)
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )  # Move up to locate config.py
)

# ✅ Import from `config.py`
try:
    from config import REPEATING_UNITS

    print(f"[DEBUG] Successfully imported repeating_units: {REPEATING_UNITS}")
except ModuleNotFoundError:
    print("[ERROR] Could not import `repeating_units` from config.py!")
    sys.exit(1)

import dash  # ✅ Import the full dash module
from dash import Input, Output, State
from data_processing import load_standards_report
from graphing import plot_figure_1, plot_figure_2


def register_callbacks(app, adjusted_df):
    """Registers Dash callbacks for dynamic updates of plots and dropdown options."""

    # ✅ Callback to update column removal dropdown options dynamically
    @app.callback(
        Output("remove_columns", "options"),
        Input("plotly_graph", "figure"),  # Trigger on graph update
        State("remove_columns", "value"),  # Preserve selected values
    )
    def update_dropdown_options(_, selected_values):
        """Updates the column removal dropdown options dynamically."""
        options = [{"label": col, "value": col} for col in adjusted_df.columns]
        return options

    # ✅ Callback to update plots when columns are removed
    @app.callback(
        [Output("plotly_graph", "figure"), Output("library_search_graph", "figure")],
        Input("remove_columns", "value"),
    )
    def update_graph_callback(remove_columns):
        """Dynamically updates plots when selected columns are removed."""
        print(
            f"[DEBUG] update_graph_callback triggered with remove_columns={remove_columns}"
        )

        # ✅ Ensure adjusted_df is being filtered correctly
        if remove_columns:
            print(f"[DEBUG] Dropping columns: {remove_columns}")
            filtered_df = adjusted_df.drop(columns=remove_columns, errors="ignore")
        else:
            filtered_df = adjusted_df.copy()

        print(f"[DEBUG] Filtered DataFrame shape: {filtered_df.shape}")

        try:
            # ✅ Generate updated plots
            fig1 = plot_figure_1(filtered_df)
            fig2 = plot_figure_2(filtered_df)

            # ✅ Check if plots are generated correctly
            if fig1 and fig2:
                print("[DEBUG] Successfully generated plots")
            else:
                print("[ERROR] One or both figures were not generated correctly!")

            return fig1, fig2

        except Exception as e:
            print(f"[ERROR] Exception in update_graph_callback: {e}", flush=True)
            return dash.no_update, dash.no_update  # ✅ Use dash.no_update

    # ✅ Callback to refresh standards report
    @app.callback(
        [Output("standards-table", "columns"), Output("standards-table", "data")],
        [Input("refresh-standards-btn", "n_clicks")],
    )
    def refresh_standards_report(n_clicks):
        """Refreshes the standards report when the refresh button is clicked."""
        print(f"[DEBUG] refresh_standards_report triggered with n_clicks={n_clicks}")

        if n_clicks is None:
            print("[DEBUG] No clicks detected. Returning empty table.")
            return [], []

        df = load_standards_report()
        print(
            f"[DEBUG] Loaded standards report with {len(df)} rows and {len(df.columns)} columns."
        )

        return [{"name": i, "id": i} for i in df.columns], df.to_dict("records")
