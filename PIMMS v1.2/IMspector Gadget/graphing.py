import os
import sys
import pandas as pd
import plotly.io as pio

# ✅ Ensure Python Can Find the Module
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get current script's directory
MODULE_PATH_1 = os.path.join(BASE_DIR, "ccs_v_mz_modules")
MODULE_PATH_2 = os.path.join(BASE_DIR, "ccs_v_mz_library_search_modules")

sys.path.append(MODULE_PATH_1)  # Add `ccs_v_mz_modules` to sys.path
sys.path.append(MODULE_PATH_2)  # Add `ccs_v_mz_library_search_modules` to sys.path

from plotly_graphing import make_plotly_graph  # ✅ Import from `ccs_v_mz_modules`
from analysis import run_analysis  # ✅ Import `run_analysis()` instead of redefining


def main():
    """Runs full analysis pipeline and generates an interactive Plotly plot."""
    file_path = "PIMMS v1.2/Data_output/PIMMS Processed Data set.csv"
    adjusted_df = pd.read_csv(file_path)

    print("\n[INFO] Running `run_analysis()`...")

    # ✅ Run full analysis using imported function
    (
        refined_groups,
        branched_isomer_groups,
        post_source_decay_groups,
        mass_only_groups,
        mass_groups,
    ) = run_analysis(adjusted_df)

    # ✅ Check if valid homologous series were identified
    if mass_groups.empty:
        print("\n[WARNING] No homologous series groups identified. Exiting.")
        return

    print(f"[DEBUG] Identified {mass_groups['GroupID'].nunique()} homologous series.")

    # ✅ Debugging: Check contents of `refined_groups`
    print("\n[DEBUG] Checking refined_groups structure:")
    for idx, group in enumerate(refined_groups):
        print(f"  - Group {idx + 1}: {len(group)} points") if isinstance(
            group, pd.DataFrame
        ) else print(f"  - Group {idx + 1}: Invalid type {type(group)}")

    # ✅ Check if the homologous series trendlines exist
    if all(isinstance(group, pd.DataFrame) and group.empty for group in refined_groups):
        print("\n[WARNING] All refined_groups are empty! Trendlines may not appear.")
    else:
        print("\n[INFO] Some homologous series groups contain data.")

    # **Step 3: Print Debugging Before Plotting**
    print("\n[INFO] Final Data Sent to Plot:")
    print(
        f"  - IM Groups: {sum(len(group) for group in refined_groups if isinstance(group, pd.DataFrame))} points"
    )
    print(
        f"  - Branched Isomers: {sum(len(group) for group in branched_isomer_groups if isinstance(group, pd.DataFrame))} points"
    )
    print(
        f"  - Post Source Decay: {sum(len(group) for group in post_source_decay_groups if isinstance(group, pd.DataFrame))} points"
    )
    print(
        f"  - Mass-Only Groups: {sum(len(group) for group in mass_only_groups.values() if isinstance(group, pd.DataFrame))} points"
    )

    # **Step 4: Generate Plotly plot**
    print("\n[INFO] Generating Plotly plot...")

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
