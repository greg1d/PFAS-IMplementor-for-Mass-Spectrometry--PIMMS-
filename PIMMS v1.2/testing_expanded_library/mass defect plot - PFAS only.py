import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def optimize_linear_bounds(pfas_df, lipid_df):
    """
    Optimizes classification bounds using a parallel-line linear quantile regression model.
    """
    print("\n--- Optimizing LINEAR BOUNDS Model (Parallel Gradient) ---")

    # --- 1. Define Model Parameters ---
    target_col_y = "Mass_Defect_from_Integer"
    target_col_x = "M-H-"
    formula = f'{target_col_y} ~ Q("{target_col_x}")'

    # --- 2. Fit Median Regression (q=0.5) to find the central slope ---
    print(f"Fitting median regression (q=0.5) using formula: {formula}")
    model_median = smf.quantreg(formula, data=pfas_df)
    result_median = model_median.fit(q=0.5)

    # Extract the common slope and the median intercept
    slope = result_median.params[f'Q("{target_col_x}")']
    intercept_median = result_median.params["Intercept"]

    # --- 3. Calculate Residuals from the Median Line ---
    predicted_median = slope * pfas_df[target_col_x] + intercept_median
    residuals = pfas_df[target_col_y] - predicted_median

    # --- 4. Find Percentiles of Residuals to use as offsets ---
    resid_q05 = residuals.quantile(0.05)
    resid_q95 = residuals.quantile(0.95)

    # --- 5. Define Final Intercepts for the parallel lines ---
    intercept_lower = intercept_median + resid_q05
    intercept_upper = intercept_median + resid_q95

    print("\nOptimal Model Parameters:")
    print(f"  - Slope (m): {slope:.6E}")
    print(f"  - Lower Intercept (b_lower): {intercept_lower:.6f}")
    print(f"  - Upper Intercept (b_upper): {intercept_upper:.6f}")

    # --- 6. Create callable lambda functions for the bounds ---
    lower_bound_func = lambda x: slope * x + intercept_lower
    upper_bound_func = lambda x: slope * x + intercept_upper

    # --- 7. Evaluate Performance ---
    print("\nEvaluating linear bounds model...")
    performance_results = calculate_performance(
        pfas_df, lipid_df, lower_bound_func, upper_bound_func
    )

    if performance_results:
        print("\nPerformance Metrics:")
        for key, value in performance_results["metrics"].items():
            print(f"  - {key}: {value:.2%}")

        # --- 8. Generate Plot, passing the model parameters ---
        print("\nGenerating performance plot for linear bounds model...")
        model_params = (
            slope,
            intercept_lower,
            intercept_upper,
            False,
        )  # log_mode is False
        plot_model_performance(
            pfas_df,
            lipid_df,
            lower_bound_func,
            upper_bound_func,
            performance_results,
            "Linear Parallel Bounds",
            model_params=model_params,
        )


def calculate_performance(pfas_df, lipid_df, lower_bound, upper_bound):
    target_col_x = "M-H-"
    target_col_y = "Mass_Defect_from_Integer"
    is_dynamic = callable(lower_bound)
    pfas_lower = lower_bound(pfas_df[target_col_x]) if is_dynamic else lower_bound
    pfas_upper = upper_bound(pfas_df[target_col_x]) if is_dynamic else upper_bound
    lipid_lower = lower_bound(lipid_df[target_col_x]) if is_dynamic else lower_bound
    lipid_upper = upper_bound(lipid_df[target_col_x]) if is_dynamic else upper_bound

    tp = pfas_df[
        (pfas_df[target_col_y] >= pfas_lower) & (pfas_df[target_col_y] <= pfas_upper)
    ].shape[0]
    fn = pfas_df.shape[0] - tp

    tn = lipid_df[
        (lipid_df[target_col_y] < lipid_lower) | (lipid_df[target_col_y] > lipid_upper)
    ].shape[0]
    fp = lipid_df.shape[0] - tn

    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    selectivity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    return {
        "confusion_matrix": {"TP": tp, "FN": fn, "TN": tn, "FP": fp},
        "metrics": {
            "Accuracy": accuracy,
            "Sensitivity": sensitivity,
            "Selectivity": selectivity,
        },
    }


def plot_model_performance(
    pfas_df, lipid_df, lower_bound, upper_bound, results, model_type, model_params=None
):
    """
    Generates a scatter plot visualizing model performance for PFAS vs Lipids.
    """
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(7, 4))
    target_col_x = "M-H-"
    target_col_y = "Mass_Defect_from_Integer"

    is_dynamic = callable(lower_bound)
    pfas_lower = lower_bound(pfas_df[target_col_x]) if is_dynamic else lower_bound
    pfas_upper = upper_bound(pfas_df[target_col_x]) if is_dynamic else upper_bound

    # Identify True Positives (PFAS inside bounds)
    tp_df = pfas_df[
        (pfas_df[target_col_y] >= pfas_lower) & (pfas_df[target_col_y] <= pfas_upper)
    ]
    # Identify False Negatives (PFAS outside bounds)
    fn_df = pfas_df.drop(tp_df.index)

    # Identify True Negatives (Lipids outside bounds)
    tn_df = lipid_df[
        (
            lipid_df[target_col_y]
            < (lower_bound(lipid_df[target_col_x]) if is_dynamic else lower_bound)
        )
        | (
            lipid_df[target_col_y]
            > (upper_bound(lipid_df[target_col_x]) if is_dynamic else upper_bound)
        )
    ]
    # Identify False Positives (Lipids inside bounds)
    fp_df = lipid_df.drop(tn_df.index)

    # --- Plotting ---

    # 1. True Negatives (Lipids, correct)
    ax.scatter(
        tn_df[target_col_x],
        tn_df[target_col_y],
        c="blue",
        marker="o",
        alpha=0.6,
        label=f"True Negatives: {len(tn_df)}",
    )

    # 2. True Positives (PFAS, correct) - Single group now
    ax.scatter(
        tp_df[target_col_x],
        tp_df[target_col_y],
        c="green",
        marker="o",
        alpha=0.6,
        label=f"True Positives (PFAS): {len(tp_df)}",
    )

    # 3. False Positives (Lipids, incorrect)
    ax.scatter(
        fp_df[target_col_x],
        fp_df[target_col_y],
        c="red",
        marker="x",
        s=50,
        label=f"False Positives: {len(fp_df)}",
    )

    # 4. False Negatives (PFAS, incorrect)
    ax.scatter(
        fn_df[target_col_x],
        fn_df[target_col_y],
        c="orange",
        marker="x",
        s=50,
        label=f"False Negatives: {len(fn_df)}",
    )

    # --- Model Boundary Lines ---
    x_range = np.linspace(
        pd.concat([pfas_df[target_col_x], lipid_df[target_col_x]]).min(),
        pd.concat([pfas_df[target_col_x], lipid_df[target_col_x]]).max(),
        200,
    )
    if is_dynamic:
        ax.plot(x_range, lower_bound(x_range), color="darkred", linestyle="--")
        ax.plot(x_range, upper_bound(x_range), color="darkred", linestyle="--")
    else:
        ax.axhline(lower_bound, color="darkred", linestyle="--")
        ax.axhline(upper_bound, color="darkred", linestyle="--")

    # --- Text Annotations for Equations ---
    text_x_pos = 2000
    box = dict(boxstyle="round,pad=0.3", fc="wheat", alpha=1)

    if is_dynamic and model_params:
        m, b_lower, b_upper, log_mode = model_params
        x_var = "log(x)" if log_mode else "x"
        eq_lower = f"$y = {m:.2E} \\cdot {x_var} + {b_lower:.3f}$ (5th percentile)"
        eq_upper = f"$y = {m:.2E} \\cdot {x_var} + {b_upper:.3f}$ (95th percentile)"

        ax.text(
            text_x_pos,
            lower_bound(text_x_pos),
            eq_lower,
            color="black",
            va="top",
            ha="right",
            fontsize=8,
            fontweight="bold",
            bbox=box,
        )
        ax.text(
            text_x_pos,
            upper_bound(text_x_pos),
            eq_upper,
            color="black",
            va="bottom",
            ha="right",
            fontsize=8,
            fontweight="bold",
            bbox=box,
        )

    else:
        eq_lower = f"$y = {lower_bound:.3f}$ (5th percentile)"
        eq_upper = f"$y = {upper_bound:.3f}$ (95th percentile)"

        ax.text(
            text_x_pos,
            lower_bound,
            eq_lower,
            color="black",
            va="top",
            ha="right",
            fontsize=8,
            bbox=box,
        )
        ax.text(
            text_x_pos,
            upper_bound,
            eq_upper,
            color="black",
            va="bottom",
            ha="right",
            fontsize=8,
            bbox=box,
        )

    # --- Statistics Box ---
    metrics = results["metrics"]
    stats_text = (
        f"Accuracy: {metrics['Accuracy']:.2%}\n"
        f"Sensitivity: {metrics['Sensitivity']:.2%}\n"
        f"Selectivity: {metrics['Selectivity']:.2%}"
    )

    ax.text(
        0.95,
        0.05,
        stats_text,
        transform=ax.transAxes,
        fontsize=8,
        va="bottom",
        ha="right",
        bbox=dict(boxstyle="round,pad=0.5", fc="wheat", alpha=1),
    )

    ax.set_title(
        f"{model_type} Model Performance (PFAS Only)", fontsize=8, fontweight="bold"
    )
    ax.set_xlabel("M-H-", fontsize=8)
    ax.set_ylabel("Mass Defect", fontsize=8)
    ax.legend(fontsize=8, loc="upper right", framealpha=1.0)
    ax.tick_params(axis="both", which="major", labelsize=8)
    plt.tight_layout()

    # Make sure directory exists before saving
    # output_path = r"PIMMS v1.2\testing_expanded_library\halogenated_performance\fixed_combined_performance.png"
    # plt.savefig(output_path)
    plt.show()


def optimize_fixed_bounds(pfas_df, lipid_df):
    print("\n--- Optimizing FIXED BOUNDS Model (Gradient = 0) ---")
    target_col = "Mass_Defect_from_Integer"
    lower_bound = pfas_df[target_col].quantile(0.05)
    upper_bound = pfas_df[target_col].quantile(0.95)
    print(f"Optimal Lower Bound (5th percentile): y = {lower_bound:.6f}")
    print(f"Optimal Upper Bound (95th percentile): y = {upper_bound:.6f}")

    print("\nEvaluating fixed bounds model...")
    performance_results = calculate_performance(
        pfas_df, lipid_df, lower_bound, upper_bound
    )

    if performance_results:
        print("\nPerformance Metrics:")
        for key, value in performance_results["metrics"].items():
            print(f"  - {key}: {value:.2%}")

        print("\nGenerating performance plot for fixed bounds model...")
        plot_model_performance(
            pfas_df,
            lipid_df,
            lower_bound,
            upper_bound,
            performance_results,
            "Fixed Bounds",
        )


def load_data(pfas_path, lipid_path):
    """
    Loads only the PFAS and Lipid libraries.
    """
    print("--- Loading Data (PFAS Only) ---")
    try:
        pfas_lib = pd.read_csv(pfas_path)
        lipid_lib = pd.read_csv(lipid_path)
        print("  - Files loaded successfully.")
    except FileNotFoundError as e:
        print(f"\n[ERROR] File not found during data loading: {e}")
        return None, None

    # Define the essential columns for the model
    key_cols = ["M-H-", "Mass_Defect_from_Integer"]

    # Ensure columns exist
    pfas_subset = pfas_lib.reindex(columns=key_cols)
    lipid_subset = lipid_lib.reindex(columns=key_cols)

    # Filter out any rows that might have NaN in key columns
    pfas_subset.dropna(subset=key_cols, inplace=True)
    lipid_subset.dropna(subset=key_cols, inplace=True)

    print(f"  - Loaded {len(pfas_subset)} PFAS compounds.")
    print(f"  - Loaded {len(lipid_subset)} Lipid compounds.")

    return pfas_subset, lipid_subset


def main():
    # Update the FILES dictionary - removed halogenated
    FILES = {
        "pfas": r"PIMMS v1.2\testing_expanded_library\pfas_processed_with_mass_defect.csv",
        "lipids": r"PIMMS v1.2\testing_expanded_library\lipid_processed_with_defect.csv",
    }

    try:
        # Load only PFAS and Lipids
        pfas_data, lipid_data = load_data(FILES["pfas"], FILES["lipids"])

        if pfas_data is not None:
            # You can run either model here. Uncomment the one you want to use.

            # 1. Linear Parallel Bounds Model

            # 2. Fixed Bounds Model (Horizontal Lines)
            optimize_fixed_bounds(pfas_data, lipid_data)

    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred in main: {e}")


if __name__ == "__main__":
    main()
