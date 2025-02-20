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
from dash import Input, Output, State, ctx, no_update
from graphing import plot_figure_2


def register_callbacks(app, adjusted_df):
    """Registers Dash callbacks for dropdown updates and graph reloading."""

    # ✅ Dropdown update
    @app.callback(
        Output("remove_columns", "options"),
        Input("plotly_graph", "figure"),
        State("remove_columns", "value"),
    )
    def update_dropdown_options(_, selected_values):
        return [{"label": col, "value": col} for col in adjusted_df.columns]

    # ✅ Combined callback for graph updates (handles column removal + library upload)
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
        """Handles column removal AND library upload, updating graphs accordingly."""
        triggered_id = ctx.triggered_id
        print(f"[DEBUG] update_graph_callback triggered by: {triggered_id}")

        try:
            # ✅ Always update fig1 using the existing `adjusted_df`
            fig1 = update_graph(remove_columns, adjusted_df)

            # ✅ If no file is uploaded, return fig1 and set fig2 to a default template
            if triggered_id != "upload-library" or not upload_contents:
                print("[INFO] No new library uploaded. Returning default fig2.")

                # ✅ Create default fig2 with a message
                fig2 = go.Figure()
                fig2.update_layout(
                    template="plotly_dark",
                    xaxis=dict(title=r"<b><i>m/z</i></b>"),
                    yaxis=dict(title="<b>CCS (&#8491;<sup>2</sup>)</b>"),
                    annotations=[
                        dict(
                            text="Upload a CCS library to visualize trends",
                            x=0.5,
                            y=0.5,
                            xref="paper",
                            yref="paper",
                            showarrow=False,
                            font=dict(size=20, color="white"),
                        )
                    ],
                )
                return fig1, fig2  # ✅ fig1 updates, fig2 shows message

            print(f"[INFO] Processing uploaded library file: {upload_filename}")

            # ✅ Step 1: Wipe the folder before saving a new file
            print(f"[INFO] Clearing previous library files in {UPLOAD_FOLDER}...")
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

            # ✅ Step 3: Run updated analysis
            print(f"[INFO] Running library search with updated file: {filepath}")

            stacked_df = stack_library_with_adjusted()
            if stacked_df is None or stacked_df.empty:
                print(
                    "[WARNING] Stacked dataset is empty after library update. Returning blank graph."
                )

                # ✅ Return dark template with error message
                empty_fig = go.Figure()
                empty_fig.update_layout(
                    title="CCS vs. m/z",
                    template="plotly_dark",
                    annotations=[
                        dict(
                            text="No data available after library update",
                            x=0.5,
                            y=0.5,
                            xref="paper",
                            yref="paper",
                            showarrow=False,
                            font=dict(size=20, color="white"),
                        )
                    ],
                )
                return fig1, empty_fig  # ✅ fig1 always updates

            # ✅ Step 4: Generate updated figure 2
            fig2 = plot_figure_2()
            print("[INFO] Library search graph updated.")

            return fig1, fig2

        except Exception as e:
            print(f"[ERROR] Exception in update_graph_callback: {e}")
            return fig1, no_update  # ✅ fig1 always updates, fig2 remains unchanged
