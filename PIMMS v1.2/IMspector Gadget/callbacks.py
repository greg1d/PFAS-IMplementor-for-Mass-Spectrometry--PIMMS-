import os
import sys

import pandas as pd

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
        os.path.join(os.path.dirname(__file__), "..")  # Move up to locate config.py
    )
)
UPLOAD_FOLDER = "PIMMS v1.2/imported_libraries"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the folder exists

# ✅ Import from `config.py`
try:
    from config import REPEATING_UNITS

    print(f"[DEBUG] Successfully imported repeating_units: {REPEATING_UNITS}")
except ModuleNotFoundError:
    print("[ERROR] Could not import `repeating_units` from config.py!")
    sys.exit(1)

from dash import Input, Output, State, no_update
from data_processing import load_standards_report
from graphing import plot_figure_2


def register_callbacks(app, adjusted_df):
    """Registers Dash callbacks for dynamic updates of plots and dropdown options."""

    @app.callback(
        Output("remove_columns", "options"),
        Input("plotly_graph", "figure"),
        State("remove_columns", "value"),
    )
    def update_dropdown_options(_, selected_values):
        return [{"label": col, "value": col} for col in adjusted_df.columns]

    from ccs_v_mz_modules.plotly_graphing import update_graph

    @app.callback(
        [Output("plotly_graph", "figure"), Output("library_search_graph", "figure")],
        Input("remove_columns", "value"),
    )
    def update_graph_callback(remove_columns):
        print(
            f"[DEBUG] update_graph_callback triggered with remove_columns={remove_columns}"
        )

        try:
            fig1 = update_graph(remove_columns, adjusted_df)
            fig2 = plot_figure_2(adjusted_df)  # Keep fig2 logic as before
            return fig1, fig2

        except KeyError as e:
            if str(e) == "'Classification Type'":
                print(
                    "[ERROR] 'Classification Type' missing. Returning empty DataFrame."
                )

                # ✅ Create an empty DataFrame with the same structure
                empty_df = pd.DataFrame(
                    columns=adjusted_df.columns
                )  # Ensure structure remains

                return update_graph(remove_columns, empty_df), plot_figure_2(empty_df)

            print(f"[ERROR] Exception in update_graph_callback: {e}")
            return no_update, no_update  # Default fallback if another error occurs

    @app.callback(
        [Output("standards-table", "columns"), Output("standards-table", "data")],
        [Input("refresh-standards-btn", "n_clicks")],
    )
    def refresh_standards_report(n_clicks):
        if n_clicks is None:
            return [], []
        df = load_standards_report()
        return [{"name": i, "id": i} for i in df.columns], df.to_dict("records")
