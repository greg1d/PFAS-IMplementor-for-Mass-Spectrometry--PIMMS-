import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from CCS_mz_trend_analysis import CCS_v_mz_analysis, mz_repeating_unit_analysis
from scipy.stats import linregress

FONT_CONFIG = dict(
    family="NormativePro, Arial, sans-serif",  # Use Arial as a fallback
    size=18,  # Default font size
    color="white",  # Ensure visibility on dark backgrounds
)


def apply_plotly_font_styling(fig, font_family="NormativePro"):
    """
    Applies uniform font styling to all text elements in the Plotly figure.

    :param fig: The Plotly figure object to be styled.
    :param font_family: The font family to apply.
    """
    fig.update_layout(
        title=dict(font=dict(family=font_family, size=18)),
        xaxis=dict(title=dict(font=dict(family=font_family, size=16))),
        yaxis=dict(title=dict(font=dict(family=font_family, size=16))),
        legend=dict(font=dict(family=font_family, size=14)),
        hoverlabel=dict(font=dict(family=font_family, size=12)),
    )


def add_homologous_series_trendlines(fig, refined_groups):
    """Adds homologous series trendlines to the Plotly figure."""
    homologous_series_plotted = False

    if refined_groups and any(len(group) >= 3 for group in refined_groups):
        for idx, group in enumerate(refined_groups):
            if len(group) < 3:
                continue

            mz_values = [point[0] for point in group]
            ccs_values = [point[1] for point in group]
            slope, intercept, r_value, _, _ = linregress(mz_values, ccs_values)
            r_squared = r_value**2

            reg_line_x = sorted(mz_values)
            reg_line_y = [slope * mz + intercept for mz in reg_line_x]

            print(f"[DEBUG] Homologous Series {idx + 1} Regression: R²={r_squared:.4f}")

            fig.add_trace(
                go.Scatter(
                    x=reg_line_x,
                    y=reg_line_y,
                    mode="lines",
                    name="Homologous Series" if not homologous_series_plotted else None,
                    line=dict(color="white", dash="dash"),
                    legendgroup="homologous_series",
                    hoverinfo="skip",
                    visible=True,
                    showlegend=False,
                )
            )
            homologous_series_plotted = True


def add_legend_entries(fig):
    """
    Adds legend entries as dummy Scatter traces without plotting actual points.
    """
    legend_items = [
        {
            "name": "Likely Identified",
            "color": "blue",
            "legendgroup": "likely_identified",
        },
        {
            "name": "Branched Isomers",
            "color": "#FF69B4",
            "legendgroup": "branched_isomers",
        },
        {
            "name": "Tentative - Library Match",
            "color": "orange",
            "legendgroup": "tentative_matched",
        },
        {
            "name": "Unmatched",
            "color": "purple",
            "legendgroup": "tentative_no_match",
        },
    ]

    for item in legend_items:
        fig.add_trace(
            go.Scatter(
                x=[None],  # Dummy point for legend only
                y=[None],
                mode="markers",
                marker=dict(size=8, color=item["color"]),
                name=item["name"],
                legendgroup=item["legendgroup"],
                showlegend=True,
                visible=True,
            )
        )

    # ✅ Add a single legend entry for the homologous series (dashed white line)
    fig.add_trace(
        go.Scatter(
            x=[None],  # Dummy line for legend only
            y=[None],
            mode="lines",
            line=dict(color="white", dash="dash"),
            name="Homologous Series",
            legendgroup="homologous_series",
            showlegend=True,
            visible=True,
        )
    )


def make_plotly_graph(
    adjusted_df, refined_groups, branched_isomers, post_source_decay, mass_only_groups
):
    sample_columns = [col.strip() for col in adjusted_df.columns if ".d" in col]
    fig = go.Figure()
    add_legend_entries(fig)
    adjusted_df.columns = adjusted_df.columns.str.strip()
    add_homologous_series_trendlines(fig, refined_groups)

    # ** Ensure `branched_isomers`, `post_source_decay`, and `mass_only_groups` are lists of dictionaries **
    if not isinstance(branched_isomers, list):
        branched_isomers = []
    if not isinstance(post_source_decay, list):
        post_source_decay = []
    if not isinstance(mass_only_groups, list):
        mass_only_groups = []

    # ** Ensure each element in the lists is a list of dicts **
    branched_isomers = [
        group if isinstance(group, list) else [] for group in branched_isomers
    ]
    post_source_decay = [
        group if isinstance(group, list) else [] for group in post_source_decay
    ]
    mass_only_groups = [
        group if isinstance(group, list) else [] for group in mass_only_groups
    ]

    # ** Remove post-source decay & branched isomer points from general data **
    flagged_mz_values = {
        point["m/z"]
        for group in (branched_isomers + post_source_decay)
        for point in group
        if isinstance(point, dict)
    }
    clean_df = adjusted_df[~adjusted_df["m/z"].isin(flagged_mz_values)]

    # ** Separate DataFrames for Different Groups **
    tentative_df = clean_df[clean_df["Classification Type"] == "tentative"]
    unmatched_df = clean_df[clean_df["Classification Type"] == "unmatched"]
    likely_df = clean_df[clean_df["Classification Type"] == "likely"]

    # ** Plot Data Points for Different Groups **
    for df, color, legend_group, legend_name in [
        (likely_df, "blue", "likely_identified", "Likely Identified"),
        (tentative_df, "orange", "tentative_matched", "Tentative - Library Match"),
        (unmatched_df, "purple", "tentative_no_match", "Unmatched"),
    ]:
        for _, row in df.iterrows():
            mz, ccs, classification, match_name = (
                row["m/z"],
                row["CCS"],
                row["Classification Type"],
                row["Match"],
            )
            RT = row.get("RT", "N/A")
            sample_info = [
                f"{col.strip()}: {row[col.strip()]:.2f}"
                for col in sample_columns
                if row[col.strip()] > 0
            ]
            sample_text = "<br>".join(sample_info) if sample_info else "None"

            fig.add_trace(
                go.Scatter(
                    x=[mz],
                    y=[ccs],
                    mode="markers",
                    marker=dict(size=8, color=color),
                    name=legend_name,
                    legendgroup=legend_group,
                    showlegend=False,
                    hovertemplate=f"Match: {match_name}<br>m/z: {mz:.4f}<br>CCS: {ccs:.2f}<br>RT: {RT:.2f}<br>"
                    f"Classification: {classification}<br>Samples:<br>{sample_text}<extra></extra>",
                    visible=True,
                )
            )

    # **🔹 Plot Branched Isomers**
    for group in branched_isomers:
        if not isinstance(group, list):
            continue
        for point in group:
            if not isinstance(point, dict):
                continue
            fig.add_trace(
                go.Scatter(
                    x=[point["m/z"]],
                    y=[point["CCS"]],
                    mode="markers",
                    marker=dict(size=8, color="#FF69B4"),
                    name="Branched Isomers",
                    legendgroup="branched_isomers",
                    showlegend=False,
                    hovertemplate=f"m/z: {point['m/z']:.4f}<br>CCS: {point['CCS']:.2f}<br>"
                    f"Classification: Branched Isomer<extra></extra>",
                    visible=True,
                )
            )

    # **🔹 Plot Post Source Decay**
    for group in post_source_decay:
        if not isinstance(group, list):
            continue
        for point in group:
            if not isinstance(point, dict):
                continue
            fig.add_trace(
                go.Scatter(
                    x=[point["m/z"]],
                    y=[point["CCS"]],
                    mode="markers",
                    marker=dict(size=8, color="red"),
                    name="Post Source Decay",
                    legendgroup="post_source_decay",
                    showlegend=False,
                    hovertemplate=f"m/z: {point['m/z']:.4f}<br>CCS: {point['CCS']:.2f}<br>"
                    f"Classification: Post Source Decay<extra></extra>",
                    visible=True,
                )
            )

    # ✅ Ensure mass_only_groups is a dictionary
    if not isinstance(mass_only_groups, dict):
        mass_only_groups = {}

    print("\n[DEBUG] Mass-Only Groups Read in for Plotting:")
    for group_name, group in mass_only_groups.items():  # ✅ Iterate over dictionary
        print(f"  - {group_name}: {len(group)} points")
        for point in group:
            if isinstance(
                point, dict
            ):  # ✅ Ensure point is a dictionary before accessing keys
                print(
                    f"    m/z: {point['m/z']:.4f}, CCS: {point['CCS']:.2f}, Classification: Mass-Only"
                )

    # **🔹 Extract m/z and CCS for mass-only points**
    mass_only_points = []
    for group in mass_only_groups.values():  # ✅ Iterate over values of the dictionary
        for point in group:
            if isinstance(point, dict):  # ✅ Ensure each point is a dictionary
                mass_only_points.append((point["m/z"], point["CCS"]))

    # ✅ Debugging: Check extracted mass-only points
    print("\n[DEBUG] Extracted Mass-Only Points:")
    for mz, ccs in mass_only_points:
        print(f"  m/z: {mz:.4f}, CCS: {ccs:.2f}")

    # ** Plot Mass-Only Points (Always Visible in Green) **
    for group in mass_only_groups:
        for point in group:
            if isinstance(point, dict):
                fig.add_trace(
                    go.Scatter(
                        x=[point["m/z"]],
                        y=[point["CCS"]],
                        mode="markers",
                        marker=dict(size=8, color="green"),
                        name="Mass-Only",
                        legendgroup="mass_only_group",
                        showlegend=False,
                        hovertemplate=f"m/z: {point['m/z']:.4f}<br>CCS: {point['CCS']:.2f}<br>"
                        f"Classification: Mass-Only<extra></extra>",
                        visible=True,
                    )
                )

    # ** Update layout **
    fig.update_layout(
        title=dict(text="CCS vs m/z Trend Analysis"),
        xaxis=dict(title="m/z"),
        yaxis=dict(title="CCS"),
        template="plotly_dark",
        legend=dict(itemclick="toggle", itemdoubleclick="toggleothers"),
    )

    return fig


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

    # **Filter out rows where the sample text is "None"**
    before_sample_removal = len(filtered_df)
    filtered_df["Sample_Info"] = filtered_df.apply(get_sample_info, axis=1)
    filtered_df = filtered_df[filtered_df["Sample_Info"] != "None"]
    after_sample_removal = len(filtered_df)

    print(
        f"[INFO] Removed {before_sample_removal - after_sample_removal} rows with 'None' sample info."
    )

    # ✅ Ensure repeating units are passed correctly
    print(
        f"[DEBUG] Passing repeating units to mz_repeating_unit_analysis: {repeating_units}"
    )
    mass_groups = mz_repeating_unit_analysis(
        filtered_df, repeating_units=repeating_units
    )

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
        mass_only_groups,  # ✅ Ensure mass-only groups are passed properly
    )

    print("[INFO] Graph update successful.")
    return fig


def main():
    """Runs full analysis pipeline and generates an interactive Plotly plot."""
    file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set test.csv"
    adjusted_df = pd.read_csv(file_path)

    repeating_units = ["CF2", "OCF2", "CF2CF2O", "CH2CF2"]

    print("\n[INFO] Starting mz_repeating_unit_analysis...")

    # **Step 1: Identify homologous series**
    mass_groups = mz_repeating_unit_analysis(
        adjusted_df, repeating_units=repeating_units
    )

    if mass_groups.empty:
        print("\n[WARNING] No homologous series groups identified. Exiting.")
        return

    print(f"[DEBUG] Identified {len(mass_groups)} homologous series.")

    # **Step 2: Perform CCS vs. m/z analysis**
    refined_groups, branched_isomer_groups, post_source_decay_groups = [], [], []
    mass_only_groups = {}  # ✅ Store mass-only groups in a dictionary

    print("\n[INFO] Performing CCS_v_mz_analysis on identified mass groups...")
    for idx, (group_id, group_df) in enumerate(mass_groups.groupby("GroupID")):
        print(f"[DEBUG] Analyzing Group {idx + 1} (GroupID: {group_id})")

        IM_group, post_source_decay, branched_isomer, mass_only_group = (
            CCS_v_mz_analysis(group_df)
        )

        # Append results for plotting
        refined_groups.append(IM_group)
        branched_isomer_groups.append(branched_isomer)
        post_source_decay_groups.append(post_source_decay)

        # ✅ Store each group in the dictionary correctly
        if isinstance(mass_only_group, list) and len(mass_only_group) > 0:
            mass_only_groups[f"Group {idx + 1}"] = (
                mass_only_group  # ✅ Dictionary format
            )

    # **Step 3: Print Debugging Before Plotting**
    print("\n[INFO] Final Data Sent to Plot:")
    print(f"  - IM Groups: {sum(len(group) for group in refined_groups)} points")
    print(
        f"  - Branched Isomers: {sum(len(group) for group in branched_isomer_groups)} points"
    )
    print(
        f"  - Post Source Decay: {sum(len(group) for group in post_source_decay_groups)} points"
    )
    print(
        f"  - Mass-Only Groups: {sum(len(group) for group in mass_only_groups.values())} points"
    )

    # **Step 4: Generate Plotly plot**
    fig = make_plotly_graph(
        adjusted_df,
        refined_groups,
        branched_isomer_groups,
        post_source_decay_groups,
        mass_only_groups,  # ✅ Now correctly formatted as a dictionary
    )

    # **Step 5: Display the Plotly plot**
    print("[INFO] Plot generation complete. Displaying plot...")
    pio.show(fig)


if __name__ == "__main__":
    main()
