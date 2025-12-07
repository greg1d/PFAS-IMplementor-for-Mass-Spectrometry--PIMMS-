import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# --- HELPER: Performance Calculation ---
def calculate_metrics(tp, fn, tn, fp):
    """Standardizes metric calculation across functions."""
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    selectivity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    # FDR = FP / (FP + TP)
    fdr = fp / (fp + tp) if (fp + tp) > 0 else 0.0

    return {
        "Accuracy": accuracy,
        "Sensitivity": sensitivity,
        "Selectivity": selectivity,
        "False Discovery Rate": fdr,
    }


def calculate_performance(positive_df, negative_df, lower_bound, upper_bound):
    target_col_x = "M-H-"
    target_col_y = "Mass_Defect_from_Integer"

    is_dynamic = callable(lower_bound)
    pos_lower = lower_bound(positive_df[target_col_x]) if is_dynamic else lower_bound
    pos_upper = upper_bound(positive_df[target_col_x]) if is_dynamic else upper_bound
    neg_lower = lower_bound(negative_df[target_col_x]) if is_dynamic else lower_bound
    neg_upper = upper_bound(negative_df[target_col_x]) if is_dynamic else upper_bound

    # TP: Positive class inside bounds
    tp = positive_df[
        (positive_df[target_col_y] >= pos_lower)
        & (positive_df[target_col_y] <= pos_upper)
    ].shape[0]
    fn = positive_df.shape[0] - tp

    # TN: Negative class outside bounds
    tn = negative_df[
        (negative_df[target_col_y] < neg_lower)
        | (negative_df[target_col_y] > neg_upper)
    ].shape[0]
    fp = negative_df.shape[0] - tn

    metrics = calculate_metrics(tp, fn, tn, fp)

    return {
        "confusion_matrix": {"TP": tp, "FN": fn, "TN": tn, "FP": fp},
        "metrics": metrics,
    }


# --- PLOTTING FUNCTION ---
def plot_model_performance(
    positive_df,
    negative_df,
    lower_bound,
    upper_bound,
    results,
    model_type,
    title_suffix="",
):
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(9, 6))
    target_col_x = "M-H-"
    target_col_y = "Mass_Defect_from_Integer"

    is_dynamic = callable(lower_bound)
    pos_lower = lower_bound(positive_df[target_col_x]) if is_dynamic else lower_bound
    pos_upper = upper_bound(positive_df[target_col_x]) if is_dynamic else upper_bound

    # --- 1. Identify Groups ---
    # We split positive_df based on the "Origin" column created in main()
    # If "Origin" doesn't exist (PFAS only case), we treat it as one group

    if "Origin" in positive_df.columns:
        pfas_subset = positive_df[positive_df["Origin"] == "PFAS"]
        halo_subset = positive_df[positive_df["Origin"] == "Halogenated"]

        # PFAS TP/FN
        p_lower = lower_bound(pfas_subset[target_col_x]) if is_dynamic else lower_bound
        p_upper = upper_bound(pfas_subset[target_col_x]) if is_dynamic else upper_bound
        tp_pfas = pfas_subset[
            (pfas_subset[target_col_y] >= p_lower)
            & (pfas_subset[target_col_y] <= p_upper)
        ]
        fn_pfas = pfas_subset.drop(tp_pfas.index)

        # Halo TP/FN
        h_lower = lower_bound(halo_subset[target_col_x]) if is_dynamic else lower_bound
        h_upper = upper_bound(halo_subset[target_col_x]) if is_dynamic else upper_bound
        tp_halo = halo_subset[
            (halo_subset[target_col_y] >= h_lower)
            & (halo_subset[target_col_y] <= h_upper)
        ]
        fn_halo = halo_subset.drop(tp_halo.index)

        # Plot PFAS (Green) and Halogenated (Purple) separately
        ax.scatter(
            tp_pfas[target_col_x],
            tp_pfas[target_col_y],
            c="green",
            marker="o",
            alpha=0.5,
            label=f"TP (PFAS): {len(tp_pfas)}",
        )
        ax.scatter(
            tp_halo[target_col_x],
            tp_halo[target_col_y],
            c="purple",
            marker="o",
            alpha=0.5,
            label=f"TP (Halogenated): {len(tp_halo)}",
        )

        # Combine for FN plotting (Orange)
        fn_df = pd.concat([fn_pfas, fn_halo])

    else:
        # Standard Single-Class Plotting
        tp_df = positive_df[
            (positive_df[target_col_y] >= pos_lower)
            & (positive_df[target_col_y] <= pos_upper)
        ]
        fn_df = positive_df.drop(tp_df.index)
        ax.scatter(
            tp_df[target_col_x],
            tp_df[target_col_y],
            c="green",
            marker="o",
            alpha=0.5,
            label=f"True Positives: {len(tp_df)}",
        )

    # Negatives (Lipids)
    tn_df = negative_df[
        (
            negative_df[target_col_y]
            < (lower_bound(negative_df[target_col_x]) if is_dynamic else lower_bound)
        )
        | (
            negative_df[target_col_y]
            > (upper_bound(negative_df[target_col_x]) if is_dynamic else upper_bound)
        )
    ]
    fp_df = negative_df.drop(tn_df.index)

    ax.scatter(
        tn_df[target_col_x],
        tn_df[target_col_y],
        c="blue",
        marker="o",
        alpha=0.5,
        label=f"True Negatives: {len(tn_df)}",
    )
    ax.scatter(
        fp_df[target_col_x],
        fp_df[target_col_y],
        c="red",
        marker="x",
        s=50,
        label=f"False Positives: {len(fp_df)}",
    )
    ax.scatter(
        fn_df[target_col_x],
        fn_df[target_col_y],
        c="orange",
        marker="x",
        s=50,
        label=f"False Negatives: {len(fn_df)}",
    )

    # --- 3. Draw Boundary Lines ---
    x_range = np.linspace(
        pd.concat([positive_df[target_col_x], negative_df[target_col_x]]).min(),
        pd.concat([positive_df[target_col_x], negative_df[target_col_x]]).max(),
        200,
    )
    if not is_dynamic:
        ax.axhline(lower_bound, color="darkred", linestyle="--")
        ax.axhline(upper_bound, color="darkred", linestyle="--")
    else:
        ax.plot(x_range, lower_bound(x_range), color="darkred", linestyle="--")
        ax.plot(x_range, upper_bound(x_range), color="darkred", linestyle="--")

    # --- 4. Statistics Box ---
    metrics = results["metrics"]
    stats_text = (
        f"Accuracy: {metrics['Accuracy']:.2%}\n"
        f"Sensitivity: {metrics['Sensitivity']:.2%}\n"
        f"Selectivity: {metrics['Selectivity']:.2%}\n"
        f"Overall FDR: {metrics['False Discovery Rate']:.2%}"
    )

    # Check if we have split component FDRs in the results (from the combined analysis)
    if "PFAS Component FDR" in results:
        stats_text += f"\nPFAS Component FDR: {results['PFAS Component FDR']:.2%}"
    if "Halogen Component FDR" in results:
        stats_text += f"\nHalogen Component FDR: {results['Halogen Component FDR']:.2%}"

    ax.text(
        0.95,
        0.05,
        stats_text,
        transform=ax.transAxes,
        fontsize=9,
        va="bottom",
        ha="right",
        bbox=dict(boxstyle="round,pad=0.5", fc="wheat", alpha=1),
    )

    ax.set_title(
        f"{model_type} Model Performance ({title_suffix})",
        fontsize=10,
        fontweight="bold",
    )
    ax.set_xlabel("M-H-", fontsize=9)
    ax.set_ylabel("Mass Defect", fontsize=9)
    ax.legend(fontsize=8, loc="upper right", framealpha=1.0)
    plt.tight_layout()
    plt.show()


# --- OPTIMIZATION FUNCTION ---
def optimize_fixed_bounds_combined(positive_df, negative_df, label="Combined"):
    """
    Analyzes the Combined library but breaks down FDR by component (PFAS vs Halogenated).
    """
    print(f"\n--- Analysis for: {label} ---")
    target_col = "Mass_Defect_from_Integer"
    target_col_x = "M-H-"

    # 1. Calculate Bounds on the COMBINED positive dataset
    lower_bound = positive_df[target_col].quantile(0.05)
    upper_bound = positive_df[target_col].quantile(0.95)
    print(f"Optimal Lower Bound (Combined 5th): y = {lower_bound:.6f}")
    print(f"Optimal Upper Bound (Combined 95th): y = {upper_bound:.6f}")

    # 2. Calculate Overall Performance
    results = calculate_performance(positive_df, negative_df, lower_bound, upper_bound)

    # 3. Calculate Component-Specific FDRs
    # We need the False Positives (Lipids inside bounds) count from the overall calculation
    # Note: The 'False Positives' count is constant because it depends only on the negative library (Lipids)
    # and the bounds. The 'True Positives' change based on which component we look at.
    fp_count = results["confusion_matrix"]["FP"]

    # --- Component A: PFAS ---
    pfas_subset = positive_df[positive_df["Origin"] == "PFAS"]
    tp_pfas = pfas_subset[
        (pfas_subset[target_col] >= lower_bound)
        & (pfas_subset[target_col] <= upper_bound)
    ].shape[0]

    # FDR_pfas = FP / (FP + TP_pfas)
    fdr_pfas = fp_count / (fp_count + tp_pfas) if (fp_count + tp_pfas) > 0 else 0.0

    # --- Component B: Halogenated ---
    halo_subset = positive_df[positive_df["Origin"] == "Halogenated"]
    tp_halo = halo_subset[
        (halo_subset[target_col] >= lower_bound)
        & (halo_subset[target_col] <= upper_bound)
    ].shape[0]

    # FDR_halo = FP / (FP + TP_halo)
    fdr_halo = fp_count / (fp_count + tp_halo) if (fp_count + tp_halo) > 0 else 0.0

    # 4. Inject these new metrics into the results dictionary for plotting
    results["PFAS Component FDR"] = fdr_pfas
    results["Halogen Component FDR"] = fdr_halo

    print("Performance Metrics:")
    for key, value in results["metrics"].items():
        print(f"  - {key}: {value:.2%}")
    print(f"  - PFAS Component FDR: {fdr_pfas:.2%}")
    print(f"  - Halogen Component FDR: {fdr_halo:.2%}")

    plot_model_performance(
        positive_df,
        negative_df,
        lower_bound,
        upper_bound,
        results,
        "Fixed Bounds",
        title_suffix=label,
    )


def optimize_fixed_bounds_single(positive_df, negative_df, label="PFAS Only"):
    """
    Standard analysis for a single library (PFAS Only).
    """
    print(f"\n--- Analysis for: {label} ---")
    target_col = "Mass_Defect_from_Integer"
    lower_bound = positive_df[target_col].quantile(0.05)
    upper_bound = positive_df[target_col].quantile(0.95)

    print(f"Optimal Lower Bound (5th): y = {lower_bound:.6f}")
    print(f"Optimal Upper Bound (95th): y = {upper_bound:.6f}")

    results = calculate_performance(positive_df, negative_df, lower_bound, upper_bound)

    if results:
        print("Performance Metrics:")
        for key, value in results["metrics"].items():
            print(f"  - {key}: {value:.2%}")

        plot_model_performance(
            positive_df,
            negative_df,
            lower_bound,
            upper_bound,
            results,
            "Fixed Bounds",
            title_suffix=label,
        )


# --- DATA LOADING ---
def load_data(pfas_path, halogenated_path, lipid_path):
    print("--- Loading Data Files ---")
    try:
        pfas_lib = pd.read_csv(pfas_path)
        halogen_lib = pd.read_csv(halogenated_path)
        lipid_lib = pd.read_csv(lipid_path)
    except FileNotFoundError as e:
        print(f"\n[ERROR] File not found: {e}")
        return None, None, None

    key_cols = ["M-H-", "Mass_Defect_from_Integer"]

    # Process PFAS
    pfas_subset = pfas_lib.reindex(columns=key_cols).dropna()
    pfas_subset["Origin"] = "PFAS"  # Tag origin

    # Process Halogenated
    halogen_subset = halogen_lib.reindex(columns=key_cols).dropna()
    halogen_subset["Origin"] = "Halogenated"  # Tag origin

    # Process Lipids
    lipid_subset = lipid_lib.reindex(columns=key_cols).dropna()

    return pfas_subset, halogen_subset, lipid_subset


# --- MAIN ---
def main():
    FILES = {
        "pfas": r"PIMMS v1.2\testing_expanded_library\pfas_processed_with_mass_defect.csv",
        "halogenated": r"PIMMS v1.2\testing_expanded_library\halogenated_processed_with_mass_defect.csv",
        "lipids": r"PIMMS v1.2\testing_expanded_library\lipid_processed_with_defect.csv",
    }

    try:
        pfas_data, halogen_data, lipid_data = load_data(
            FILES["pfas"], FILES["halogenated"], FILES["lipids"]
        )

        if pfas_data is not None:
            # 1. SCENARIO A: PFAS ONLY vs LIPIDS
            print("\n" + "=" * 40)
            print(" CALCULATING FDR FOR PFAS ONLY LIBRARY")
            print("=" * 40)
            optimize_fixed_bounds_single(pfas_data, lipid_data, label="PFAS Only")

            # 2. SCENARIO B: COMBINED (PFAS + HALOGENATED) vs LIPIDS
            # This function will now breakdown FDR by component
            print("\n" + "=" * 40)
            print(" CALCULATING FDR FOR COMBINED (PFAS + HALOGENATED)")
            print("=" * 40)
            combined_positive = pd.concat([pfas_data, halogen_data], ignore_index=True)
            optimize_fixed_bounds_combined(
                combined_positive, lipid_data, label="Combined Library"
            )

    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
