from analysis import run_analysis
from dash import Input, Output
from data_processing import load_standards_report
from graphing import generate_plot


def register_callbacks(app, adjusted_df):
    """Registers Dash callbacks."""

    @app.callback(Output("plotly_graph", "figure"), [Input("remove_columns", "value")])
    def update_graph_callback(remove_columns):
        (
            refined_groups,
            branched_isomer_groups,
            post_source_decay_groups,
            mass_only_groups,
            mass_groups,
        ) = run_analysis(adjusted_df)
        return generate_plot(
            adjusted_df,
            refined_groups,
            branched_isomer_groups,
            post_source_decay_groups,
            mass_only_groups,
            mass_groups,
        )

    @app.callback(
        Output("standards-table", "columns"),
        Output("standards-table", "data"),
        Input("refresh-standards-btn", "n_clicks"),
    )
    def refresh_standards_report(n_clicks):
        df = load_standards_report()
        return [{"name": i, "id": i} for i in df.columns], df.to_dict("records")
