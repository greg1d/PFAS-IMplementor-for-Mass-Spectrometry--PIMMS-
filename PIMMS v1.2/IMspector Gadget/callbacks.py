import base64
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

from ccs_v_mz_modules.plotly_graphing import update_graph
from dash import Input, Output, State, ctx, no_update
from graphing import plot_figure_2


def register_callbacks(app, adjusted_df):
    """Registers Dash callbacks for dropdown updates and graph reloading."""

    @app.callback(
        Output("remove_columns", "options"),
        Input("plotly_graph", "figure"),
        State("remove_columns", "value"),
    )
    def update_dropdown_options(_, selected_values):
        return [{"label": col, "value": col} for col in adjusted_df.columns]

    @app.callback(
        [
            Output("plotly_graph", "figure"),
            Output("library_search_graph", "figure"),
        ],
        [
            Input("remove_columns", "value"),
            Input("upload-library", "contents"),
        ],
        [
            State("upload-library", "filename"),
        ],
    )
    def update_graph_callback(remove_columns, upload_contents, upload_filename):
        """Handles column removal AND library upload to retrigger graph updates."""
        triggered_id = ctx.triggered_id
        print(f"[DEBUG] update_graph_callback triggered by: {triggered_id}")

        try:
            # ✅ Case 1: A new file was uploaded
            if triggered_id == "upload-library" and upload_contents:
                print(f"[INFO] Processing uploaded library file: {upload_filename}")

                # ✅ Save uploaded file
                filepath = os.path.join(UPLOAD_FOLDER, upload_filename)
                _, content_string = upload_contents.split(",")

                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(content_string))
                print(f"[INFO] File saved to: {filepath}")

                # ✅ Load the new library and rerun analysis
                new_library_df = pd.read_csv(filepath)
                print("[DEBUG] Successfully loaded new library file!")

                fig2 = plot_figure_2(new_library_df)
                print("[INFO] Library search graph updated after file upload.")

                # ✅ Use the existing `adjusted_df` for the main plot (fig1)
                fig1 = update_graph(remove_columns, adjusted_df)

                return fig1, fig2

            # ✅ Case 2: Only columns were removed
            print(f"[INFO] Removing selected columns: {remove_columns}")
            fig1 = update_graph(remove_columns, adjusted_df)
            fig2 = plot_figure_2(adjusted_df)  # Re-run with the existing dataset

            return fig1, fig2

        except Exception as e:
            print(f"[ERROR] Exception in update_graph_callback: {e}")
            return no_update, no_update  # Prevent breaking the UI
