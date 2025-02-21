import os
import sys

import pandas as pd

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
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")  # Move up to locate config.py
    )
)

# ✅ Import necessary functions
try:
    from config import REPEATING_UNITS  # ✅ Import repeating_units globally
    from config import REPEATING_UNITS

    print(f"[DEBUG] Successfully imported repeating_units: {REPEATING_UNITS}")
except ModuleNotFoundError:
    print("[ERROR] Could not import `REPEATING_UNITS` from config.py!")
    sys.exit(1)

from CCS_mz_trend_analysis import CCS_v_mz_analysis, mz_repeating_unit_analysis
from dash import Input, Output, State, no_update
from data_processing import load_standards_report
from graphing import (
    plotly_ccs_v_mz_sample_plot,  # ✅ Import the correct graphing function
    generate_library_search_plot,
)
from graphing import make_plotly_graph, plot_figure_2


def register_callbacks(
    app,
    adjusted_df,
    filtered_IM_group,
    library_match_source,
):
    """Registers Dash callbacks for dynamic graph updates and table refresh."""
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
        [
            Output(
                "plotly_graph", "figure"
            ),  # ✅ This updates the main CCS vs. m/z plot
            Output("library_search_graph", "figure"),
        ],
        [Input("remove_columns", "value")],
        [Output("plotly_graph", "figure"), Output("library_search_graph", "figure")],
        Input("remove_columns", "value"),
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


def update_graph(remove_columns, adjusted_df, repeating_units=REPEATING_UNITS):
    print("[INFO] Graph update triggered.")

    remove_columns = remove_columns or []
    filtered_df = adjusted_df.drop(
        columns=[col for col in remove_columns if col in adjusted_df.columns],
        errors="ignore",
    )

    d_columns = [col for col in filtered_df.columns if ".d" in col]
    if d_columns:
        filtered_df = filtered_df[~(filtered_df[d_columns] == 0).all(axis=1)]

    sample_columns = [col for col in filtered_df.columns if ".d" in col]
    filtered_df["Sample_Info"] = filtered_df.apply(
        lambda row: "<br>".join(
            [f"{col}: {row[col]:.2f}" for col in sample_columns if row[col] > 0]
        )
        if any(row[col] > 0 for col in sample_columns)
        else "None",
        axis=1,
    )
    filtered_df = filtered_df[filtered_df["Sample_Info"] != "None"]

    mass_groups = mz_repeating_unit_analysis(filtered_df)
    (
        refined_groups,
        branched_isomer_groups,
        post_source_decay_groups,
        mass_only_groups,
    ) = [], [], [], {}

    for idx, (group_id, group_df) in enumerate(mass_groups.groupby("GroupID")):
        IM_group, post_source_decay, branched_isomer, mass_only_group = (
            CCS_v_mz_analysis(group_df)
        )
        refined_groups.append(IM_group)
        branched_isomer_groups.append(branched_isomer)
        post_source_decay_groups.append(post_source_decay)
        if isinstance(mass_only_group, list) and mass_only_group:
            mass_only_groups[f"Group {idx + 1}"] = mass_only_group

    fig = make_plotly_graph(
        filtered_df,
        refined_groups,
        branched_isomer_groups,
        post_source_decay_groups,
        mass_only_groups,
        mass_groups,
    )

    return fig
