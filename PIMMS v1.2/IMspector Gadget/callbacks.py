import base64
import os
import sys

from plotly import graph_objs as go

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

REPEATING_UNITS = {
    "CF2": 49.9968064,
    "OCF2": 65.9917214,
    "CF2CF2O": 115.988527,
    "CH2CF2": 64.012456,
    "HF": 20.0062278,
}

UPLOAD_FOLDER = "PIMMS v1.2/imported_libraries"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the folder exists

# ✅ Import from `config.py`
try:
    from config import LIBRARY_PATH, REPEATING_UNITS

    print(f"[DEBUG] Successfully imported repeating_units: {REPEATING_UNITS}")
    print(f"[DEBUG] Default LIBRARY_PATH: {LIBRARY_PATH}")
except ModuleNotFoundError:
    print(
        "[ERROR] Could not import `repeating_units` or `LIBRARY_PATH` from config.py!"
    )
    sys.exit(1)

from ccs_v_mz_library_search_modules.library_search_module import (
    stack_library_with_adjusted,
)
from ccs_v_mz_modules.plotly_graphing import update_graph
from dash import Input, Output, State, ctx
from graphing import plot_figure_2, plot_figure_3


def register_callbacks(app, adjusted_df):
    """Registers Dash callbacks for dropdown updates and graph reloading."""

    # ✅ Dropdown update
    @app.callback(
        Output("remove_columns", "options"),
        Input("plotly_graph", "figure"),
        State("remove_columns", "value"),
    )
    def update_dropdown_options(_, selected_values):
        # ✅ Filter columns to only include those with ".d" in their names
        d_columns = [col for col in adjusted_df.columns if ".d" in col]

        return [{"label": col, "value": col} for col in d_columns]

    @app.callback(
        [
            Output("plotly_graph", "figure"),
            Output("library_search_graph", "figure"),
            Output("rt_vs_mz_graph", "figure"),  # ✅ Fig 3: RT vs. m/z Graph
        ],
        [
            Input("repeating-units-dropdown", "value"),
            Input("remove_columns", "value"),
            Input("upload-library", "contents"),
        ],
        [
            State("upload-library", "filename"),
        ],
    )
    def update_graph_callback(
        selected_units, remove_columns, upload_contents, upload_filename
    ):
        """Handles column removal, repeating units selection, AND library updates."""
        triggered_id = ctx.triggered_id
        print(f"[DEBUG] update_graph_callback triggered by: {triggered_id}")

        try:
            # ✅ Default to CF2 if no selection
            if not selected_units or selected_units == [""]:
                print("[WARNING] No repeating units selected. Defaulting to CF2.")
                selected_units = ["CF2"]

            # ✅ Convert selected_units into a dictionary
            selected_repeating_units = {
                key: REPEATING_UNITS[key]
                for key in selected_units
                if key in REPEATING_UNITS
            }
            print(
                f"[INFO] Updated selected repeating units: {selected_repeating_units}"
            )

            # ✅ Always update fig1
            fig1 = update_graph(remove_columns, adjusted_df, selected_repeating_units)

            # ✅ Always update fig2 (regardless of file upload)
            fig2 = plot_figure_2(selected_repeating_units)

            # ✅ Only process a new library if uploaded
            if triggered_id == "upload-library" and upload_contents:
                print(f"[INFO] Processing uploaded library file: {upload_filename}")

                # ✅ Step 1: Wipe previous library files
                for file in os.listdir(UPLOAD_FOLDER):
                    file_path = os.path.join(UPLOAD_FOLDER, file)
                    try:
                        os.remove(file_path)
                        print(f"[INFO] Deleted: {file_path}")
                    except Exception as e:
                        print(f"[WARNING] Failed to delete {file_path}: {e}")

                # ✅ Step 2: Save the new uploaded file
                filepath = os.path.join(UPLOAD_FOLDER, upload_filename)
                _, content_string = upload_contents.split(",")
                with open(filepath, "wb") as f:
                    decoded_data = base64.b64decode(content_string)
                    f.write(decoded_data)
                print(f"[INFO] File saved to: {filepath}")

                # ✅ Step 3: Run updated analysis with the new library
                stacked_df = stack_library_with_adjusted()
                if stacked_df is None or stacked_df.empty:
                    print(
                        "[WARNING] Stacked dataset is empty after library update. Returning blank graph."
                    )
                    # ✅ Create empty black-themed figure for Fig 2
                    empty_fig2 = go.Figure()
                    empty_fig2.update_layout(
                        title="CCS vs. <i>m/z</i>",
                        template="plotly_dark",
                        annotations=[
                            dict(
                                text="No data available",
                                x=0.5,
                                y=0.5,
                                xref="paper",
                                yref="paper",
                                showarrow=False,
                                font=dict(size=20, color="white"),
                            )
                        ],
                    )

                    # ✅ Create empty black-themed figure for Fig 3
                    empty_fig3 = go.Figure()
                    empty_fig3.update_layout(
                        title="RT vs. <i>m/z</i>",
                        template="plotly_dark",
                        annotations=[
                            dict(
                                text="No data available",
                                x=0.5,
                                y=0.5,
                                xref="paper",
                                yref="paper",
                                showarrow=False,
                                font=dict(size=20, color="white"),
                            )
                        ],
                    )
                    return fig1, empty_fig2, empty_fig3  # ✅ fig1 updates, fig2 blank

                # ✅ Step 4: Update fig2 after processing the new library
                fig2 = plot_figure_2(selected_repeating_units)
                print("[INFO] Library search graph updated.")
                fig3 = plot_figure_3(selected_repeating_units)

            return fig1, fig2, fig3, None

        except Exception as e:
            print(f"[ERROR] Exception in update_graph_callback: {e}")

            # ✅ If an error occurs, ensure dark-themed empty figures
            error_fig2 = go.Figure()
            error_fig2.update_layout(
                title="CCS vs. <i>m/z</i>",
                template="plotly_dark",
                annotations=[
                    dict(
                        text="Select an external library to visualize results",
                        x=0.5,
                        y=0.5,
                        xref="paper",
                        yref="paper",
                        showarrow=False,
                        font=dict(size=20, color="white"),
                    )
                ],
            )

            error_fig3 = go.Figure()
            error_fig3.update_layout(
                title="RT vs. <i>m/z</i>",
                template="plotly_dark",
                annotations=[
                    dict(
                        text="Select an external library to visualize results",
                        x=0.5,
                        y=0.5,
                        xref="paper",
                        yref="paper",
                        showarrow=False,
                        font=dict(size=20, color="white"),
                    )
                ],
            )

            return (
                fig1,
                error_fig2,
                error_fig3,
            )  # ✅ fig1 updates, fig2 & fig3 are error placeholders
