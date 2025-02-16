import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from CCS_mz_trend_analysis import CCS_v_mz_analysis, mz_repeating_unit_analysis
from scipy.stats import linregress

HOMOLOGOUS_SERIES_COLORS = [
    "cyan",
    "magenta",
    "lime",
    "deepskyblue",
    "orchid",
    "chartreuse",
]


def add_homologous_series_trendlines(
    fig, refined_groups, branched_isomers, post_source_decay, adjusted_df, mass_groups
):
    """
    Adds homologous series trendlines and uniquely classifies their corresponding points,
    including branched isomers and post-source decay points.
    """

    if not refined_groups or all(len(group) < 3 for group in refined_groups):
        print(
            "[WARNING] No valid homologous series found. Skipping trendline plotting."
        )
        return

    print(f"\n[INFO] Total Refined Homologous Series: {len(refined_groups)}")
    print(f"[INFO] Total Post Source Decay Groups: {len(post_source_decay)}")

    if "Repeating Unit" not in adjusted_df.columns:
        print("[DEBUG] Merging mass_groups to include Repeating Unit in adjusted_df...")
        adjusted_df = adjusted_df.merge(
            mass_groups[["m/z", "Repeating Unit"]], on="m/z", how="left"
        )
        print("merged df", adjusted_df.head())

    # ✅ Function to match homologous series points with branched/post-source points
    def is_point_in_series(mz, series_mz_values, mz_tol=0.1):
        return any(abs(mz - series_mz) < mz_tol for series_mz in series_mz_values)

    for idx, group in enumerate(refined_groups):
        if len(group) < 3:
            continue  # Skip small groups

        print(
            f"\n[DEBUG] Checking Group {idx + 1}: First element type -> {type(group[0])}"
        )
        print(
            f"[DEBUG] Group {idx + 1} Raw Data: {group[:5]}"
        )  # Print first 5 elements

        # ✅ Convert tuples to dictionaries
        if isinstance(group[0], tuple):
            print(
                f"[WARNING] Group {idx + 1} contains tuples instead of dictionaries. Converting..."
            )
            group = [{"m/z": point[0], "CCS": point[1]} for point in group]

        # ✅ Extract homologous series point information
        mz_values = [point["m/z"] for point in group]
        ccs_values = [point["CCS"] for point in group]

        hover_texts = []

        for mz in mz_values:
            row = adjusted_df.loc[adjusted_df["m/z"] == mz]

            # ✅ Extract metadata
            match_name = row["Match"].values[0] if not row.empty else "No Match"
            classification = (
                row["Classification Type"].values[0] if not row.empty else "Unknown"
            )
            RT = row["RT"].values[0] if not row.empty else "N/A"

            # ✅ Extract the correct CCS value **for this individual point**
            ccs = row["CCS"].values[0] if not row.empty else "N/A"
            print("[DEBUG] Columns in adjusted_df:", adjusted_df.columns.tolist())
            repeating_unit = row["Repeating Unit"].values[0] if not row.empty else "N/A"
            # ✅ Extract sample-related information
            sample_columns = [col for col in adjusted_df.columns if ".d.DeMP" in col]
            sample_info = []

            for col in sample_columns:
                if not row.empty and col.strip() in row:
                    val = row[col.strip()].values[0]
                    val = pd.to_numeric(val, errors="coerce")  # ✅ Convert to numeric

                    if pd.notna(val) and val > 0:  # ✅ Ensure valid number
                        sample_info.append(f"{col.strip()}: {val:.2f}")

            sample_text = "<br>".join(sample_info) if sample_info else "None"

            # ✅ Construct hover text
            hover_text = (
                f"Match: {match_name}<br>"
                f"m/z: {mz:.4f}<br>"
                f"CCS: {ccs:.2f}<br>"
                f"RT: {RT:.2f}<br>"
                f"Classification: {classification}<br>"
                f"Repeating Unit: {repeating_unit}<br>"
                f"Samples:<br>{sample_text}<extra></extra>"
            )

            hover_texts.append(hover_text)

        # Perform linear regression for trendline
        slope, intercept, r_value, _, _ = linregress(mz_values, ccs_values)
        r_squared = r_value**2

        reg_line_x = sorted(mz_values)
        reg_line_y = [slope * mz + intercept for mz in reg_line_x]

        # **Assign unique color for each homologous series**
        series_color = HOMOLOGOUS_SERIES_COLORS[idx % len(HOMOLOGOUS_SERIES_COLORS)]
        legend_group_name = f"homologous_series_{idx + 1}"

        print(f"\n[DEBUG] Homologous Series {idx + 1} Regression: R²={r_squared:.4f}")
        print(f"[DEBUG] m/z Values: {mz_values}")
        print(f"[DEBUG] CCS Values: {ccs_values}")

        # 🔹 Add trendline
        fig.add_trace(
            go.Scatter(
                x=reg_line_x,
                y=reg_line_y,
                mode="lines",
                name=f"Homologous Series {idx + 1}",
                line=dict(color=series_color, dash="dash"),
                legendgroup=legend_group_name,
                hoverinfo="skip",
                visible="legendonly",  # Hidden until toggled
                showlegend=False,
            )
        )

        # 🔹 Overlay main homologous series points with metadata
        fig.add_trace(
            go.Scatter(
                x=mz_values,
                y=ccs_values,
                mode="markers",
                marker=dict(size=8, color=series_color),
                name=f"Homologous Series {idx + 1}",
                legendgroup=legend_group_name,
                showlegend=True,
                visible="legendonly",
                text=hover_texts,  # ✅ Full metadata in hover
                hovertemplate="%{text}<extra></extra>",  # ✅ Injects metadata dynamically
            )
        )


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


def make_plotly_graph(
    adjusted_df,
    refined_groups,
    branched_isomers,
    post_source_decay,
    mass_only_groups,
    mass_groups,
):
    fig = go.Figure()
    add_legend_entries(fig)
    adjusted_df.columns = adjusted_df.columns.str.strip()

    # **Step 1: Collect all homologous series points (to exclude from other groups)**
    homologous_series_points = {
        (point[0], point[1]) for group in refined_groups for point in group
    }

    # **Step 2: Plot Homologous Series Trendlines & Points Separately**
    add_homologous_series_trendlines(
        fig,
        refined_groups,
        branched_isomers,
        post_source_decay,
        adjusted_df,
        mass_groups,
    )

    # **Step 3: Filter Adjusted Data to Remove Homologous Series Points**
    filtered_df = adjusted_df[
        ~adjusted_df.apply(
            lambda row: (row["m/z"], row["CCS"]) in homologous_series_points, axis=1
        )
    ]

    # **Step 4: Separate Remaining DataFrames (Without Homologous Series Points)**
    tentative_df = filtered_df[filtered_df["Classification Type"] == "tentative"]
    unmatched_df = filtered_df[filtered_df["Classification Type"] == "unmatched"]
    likely_df = filtered_df[filtered_df["Classification Type"] == "likely"]

    sample_columns = [col.strip() for col in adjusted_df.columns if ".d" in col]

    # **Step 5: Plot Data Points for Different Groups**
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

    for group in branched_isomers:
        for point in group:
            mz = point["m/z"]
            ccs = point["CCS"]

            # Extract metadata for the current point
            row = adjusted_df.loc[adjusted_df["m/z"] == mz]

            match_name = row["Match"].iloc[0] if not row.empty else "No Match"
            classification = (
                row["Classification Type"].iloc[0] if not row.empty else "Unknown"
            )
            RT = row["RT"].iloc[0] if not row.empty else "N/A"

            # Extract sample information
            sample_columns = [col for col in adjusted_df.columns if ".d.DeMP" in col]
            sample_info = [
                f"{col.strip()}: {row[col.strip()].iloc[0]:.2f}"
                for col in sample_columns
                if not row.empty
                and pd.notna(row[col.strip()].iloc[0])
                and row[col.strip()].iloc[0] > 0
            ]
            sample_text = "<br>".join(sample_info) if sample_info else "None"

            fig.add_trace(
                go.Scatter(
                    x=[mz],
                    y=[ccs],
                    mode="markers",
                    marker=dict(size=8, color="#FF69B4"),
                    name="Branched Isomers",
                    legendgroup="branched_isomers",
                    showlegend=False,
                    hovertemplate=f"Match: {match_name}<br>m/z: {mz:.4f}<br>CCS: {ccs:.2f}<br>RT: {RT:.2f}<br>"
                    f"Classification: {classification}<br>Samples:<br>{sample_text}<extra></extra>",
                    visible=True,
                )
            )

    for group in post_source_decay:
        for point in group:
            mz = point["m/z"]
            ccs = point["CCS"]

            # Extract metadata for the current point
            row = adjusted_df.loc[adjusted_df["m/z"] == mz]

            match_name = row["Match"].iloc[0] if not row.empty else "No Match"
            classification = (
                row["Classification Type"].iloc[0] if not row.empty else "Unknown"
            )
            RT = row["RT"].iloc[0] if not row.empty else "N/A"

            # Extract sample information
            sample_columns = [col for col in adjusted_df.columns if ".d.DeMP" in col]
            sample_info = [
                f"{col.strip()}: {row[col.strip()].iloc[0]:.2f}"
                for col in sample_columns
                if not row.empty
                and pd.notna(row[col.strip()].iloc[0])
                and row[col.strip()].iloc[0] > 0
            ]
            sample_text = "<br>".join(sample_info) if sample_info else "None"

            fig.add_trace(
                go.Scatter(
                    x=[mz],
                    y=[ccs],
                    mode="markers",
                    marker=dict(size=8, color="red"),
                    name="Post Source Decay",
                    legendgroup="post_source_decay",
                    showlegend=False,
                    hovertemplate=f"Match: {match_name}<br>m/z: {mz:.4f}<br>CCS: {ccs:.2f}<br>RT: {RT:.2f}<br>"
                    f"Classification: {classification}<br>Samples:<br>{sample_text}<extra></extra>",
                    visible=True,
                )
            )

    # **Step 8: Plot Mass-Only Points**
    for group_name, group in mass_only_groups.items():
        for point in group:
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

    # **Final Layout Update**
    fig.update_layout(
        title=dict(
            text="CCS vs <i>m/z</i> Trend Analysis",
            font=dict(family="NormativePro", size=20, color="white", weight="bold"),
            x=0.1,  # Centering the title
            y=0.95,
            xanchor="left",
            yanchor="top",
        ),
        xaxis=dict(
            title=r"<b><i>m/z</i></b>",  # ✅ Bold and italicized using HTML
            title_font=dict(family="NormativePro", size=16, color="white"),
            tickfont=dict(
                family="NormativePro", size=14, color="white", weight="bold"
            ),  # ✅ Tick labels
        ),
        yaxis=dict(
            title="CCS (&#8491;<sup>2</sup>)",
            title_font=dict(family="NormativePro", size=16, color="white"),
            tickfont=dict(
                family="NormativePro", size=14, color="white", weight="bold"
            ),  # ✅ Tick labels
        ),
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
        mass_only_groups,
        mass_groups,  # ✅ Ensure mass-only groups are passed properly
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
        mass_only_groups,
        mass_groups,  # ✅ Now correctly formatted as a dictionary
    )

    # **Step 5: Display the Plotly plot**
    print("[INFO] Plot generation complete. Displaying plot...")
    pio.show(fig)


if __name__ == "__main__":
    main()
