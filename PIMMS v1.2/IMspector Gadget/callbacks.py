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
        os.path.join(os.path.dirname(__file__), "..")  # Move up to locate config.py
    )
)

# ✅ Import from `config.py`
try:
    from config import REPEATING_UNITS

    print(f"[DEBUG] Successfully imported repeating_units: {REPEATING_UNITS}")
except ModuleNotFoundError:
    print("[ERROR] Could not import `repeating_units` from config.py!")
    sys.exit(1)

from CCS_mz_trend_analysis import CCS_v_mz_analysis, mz_repeating_unit_analysis
from dash import Input, Output, State, no_update
from data_processing import load_standards_report
from graphing import make_plotly_graph, plot_figure_2


def register_callbacks(app, adjusted_df):
    """Registers Dash callbacks for dynamic updates of plots and dropdown options."""

    @app.callback(
        Output("remove_columns", "options"),
        Input("plotly_graph", "figure"),
        State("remove_columns", "value"),
    )
    def update_dropdown_options(_, selected_values):
        return [{"label": col, "value": col} for col in adjusted_df.columns]

    @app.callback(
        [Output("plotly_graph", "figure"), Output("library_search_graph", "figure")],
        Input("remove_columns", "value"),
    )
    def update_graph_callback(remove_columns):
        print(
            f"[DEBUG] update_graph_callback triggered with remove_columns={remove_columns}"
        )

        # ✅ Call the main update function with required arguments
        try:
            fig1 = update_graph(remove_columns, adjusted_df)
            fig2 = plot_figure_2(
                adjusted_df
            )  # Modify this if fig2 needs similar filtering
            return fig1, fig2
        except Exception as e:
            print(f"[ERROR] Exception in update_graph_callback: {e}")
            return no_update, no_update

    def update_graph(remove_columns, adjusted_df, repeating_units=["CF2", "OCF2"]):
        """Updates the graph dynamically when columns are removed."""
        print("[INFO] Graph update triggered.")
        print(f"[DEBUG] Using repeating units in update_graph: {repeating_units}")

        # ✅ Default to empty list if None
        if remove_columns is None:
            remove_columns = []

        print(f"[DEBUG] Columns to remove: {remove_columns}")

        # ✅ Filter dataset
        filtered_df = adjusted_df.drop(
            columns=[col for col in remove_columns if col in adjusted_df.columns],
            errors="ignore",
        )

        # ✅ Identify columns that contain ".d"
        d_columns = [col for col in filtered_df.columns if ".d" in col]

        # ✅ Remove rows where all ".d" columns contain only 0s
        if d_columns:
            before_removal = len(filtered_df)
            filtered_df = filtered_df[~(filtered_df[d_columns] == 0).all(axis=1)]
            after_removal = len(filtered_df)
            print(
                f"[INFO] Removed {before_removal - after_removal} rows where all '.d' columns were 0."
            )

        # ✅ Identify rows where "Samples:" is "None" and remove them
        sample_columns = [col for col in filtered_df.columns if ".d" in col]

        def get_sample_info(row):
            """Extracts sample intensity info for hover text."""
            sample_info = [
                f"{col}: {row[col]:.2f}" for col in sample_columns if row[col] > 0
            ]
            return "<br>".join(sample_info) if sample_info else "None"

        # **Compute sample information**
        filtered_df["Sample_Info"] = filtered_df.apply(get_sample_info, axis=1)

        # ✅ **Remove rows where Sample_Info is "None"**
        before_sample_removal = len(filtered_df)
        filtered_df = filtered_df[filtered_df["Sample_Info"] != "None"]
        after_sample_removal = len(filtered_df)

        print(
            f"[INFO] Removed {before_sample_removal - after_sample_removal} rows with 'None' sample info."
        )

        # ✅ Ensure repeating units are passed correctly
        print(
            f"[DEBUG] Passing repeating units to mz_repeating_unit_analysis: {repeating_units}"
        )
        mass_groups = mz_repeating_unit_analysis(filtered_df)

        # ✅ Process each group through CCS_v_mz_analysis
        refined_groups, branched_isomer_groups, post_source_decay_groups = [], [], []
        mass_only_groups = {}

        for idx, (group_id, group_df) in enumerate(mass_groups.groupby("GroupID")):
            print(
                f"[DEBUG] Updating Graph - Analyzing Group {idx + 1} (GroupID: {group_id})"
            )

            IM_group, post_source_decay, branched_isomer, mass_only_group = (
                CCS_v_mz_analysis(group_df)
            )

            refined_groups.append(IM_group)
            branched_isomer_groups.append(branched_isomer)
            post_source_decay_groups.append(post_source_decay)

            if isinstance(mass_only_group, list) and len(mass_only_group) > 0:
                mass_only_groups[f"Group {idx + 1}"] = mass_only_group

        # ✅ Debugging before sending to plotting function
        print("\n[INFO] Final Data Sent to Plot:")
        print(
            f"  - Homologous Series: {sum(len(group) for group in refined_groups)} points"
        )
        print(
            f"  - Branched Isomers: {sum(len(group) for group in branched_isomer_groups)} points"
        )
        print(
            f"  - Post Source Decay: {sum(len(group) for group in post_source_decay_groups)} points"
        )
        print(
            f"  - Mass-Only Groups: {sum(len(group) for group in mass_only_groups.values())} points"
        )

        # ✅ Generate updated graph
        fig = make_plotly_graph(
            filtered_df,
            refined_groups,  # ✅ Now included!
            branched_isomer_groups,
            post_source_decay_groups,
            mass_only_groups,
            mass_groups,  # ✅ Ensure mass-only groups are passed properly
        )

        print("[INFO] Graph update successful.")
        return fig

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
