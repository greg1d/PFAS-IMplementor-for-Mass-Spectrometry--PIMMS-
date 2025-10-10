import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


# calculate_performance function is unchanged and correct
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


# --- MODIFIED: plot_model_performance now adds equation text ---
def plot_model_performance(
    pfas_df, lipid_df, lower_bound, upper_bound, results, model_type, model_params=None
):
    """
    Generates a scatter plot visualizing the model's performance and overlays line equations.
    """
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(7, 4))
    target_col_x = "M-H-"
    target_col_y = "Mass_Defect_from_Integer"

    is_dynamic = callable(lower_bound)
    x_range = np.linspace(
        pd.concat([pfas_df[target_col_x], lipid_df[target_col_x]]).min(),
        pd.concat([pfas_df[target_col_x], lipid_df[target_col_x]]).max(),
        200,
    )

    # Plot the model boundaries
    if is_dynamic:
        ax.plot(x_range, lower_bound(x_range), color="darkred", linestyle="--")
        ax.plot(x_range, upper_bound(x_range), color="darkred", linestyle="--")
    else:  # It's a constant value
        ax.axhline(lower_bound, color="darkred", linestyle="--")
        ax.axhline(upper_bound, color="darkred", linestyle="--")

    # --- MODIFIED: Add text annotations for the line equations on the RIGHT side ---
    # Position the text near the right edge of the plot
    text_x_pos = 2000

    if is_dynamic and model_params:  # For Linear/Log models
        m, b_lower, b_upper, log_mode = model_params
        x_var = "log(x)" if log_mode else "x"
        eq_lower = f"$y = {m:.2E} \\cdot {x_var} + {b_lower:.3f}$ (5th percentile)"
        eq_upper = f"$y = {m:.2E} \\cdot {x_var} + {b_upper:.3f}$ (95th percentile)"
        # Define the style for the background box. You can reuse this for both text elements.
        bbox_style = dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.75)

        # For the lower bound equation
        ax.text(
            text_x_pos,
            lower_bound(text_x_pos) + 0.22,
            eq_lower,
            color="black",
            va="top",
            ha="right",
            fontsize=8,
            fontweight="bold",
            bbox=bbox_style,  # Add the bbox argument here
        )

        # For the upper bound equation
        ax.text(
            text_x_pos,
            upper_bound(text_x_pos) + 0.22,
            eq_upper,
            color="darkred",
            va="bottom",
            ha="right",
            fontsize=8,
            fontweight="bold",
            bbox=bbox_style,  # And also here
        )

    else:  # For Fixed Bounds model
        bbox_style = dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.75)

        eq_lower = f"$y = {lower_bound:.3f}$ (5th percentile)"
        eq_upper = f"$y = {upper_bound:.3f}$ (95th percentile)"
        # Use ha='right' to align the text to the right
        ax.text(
            text_x_pos,
            lower_bound,
            eq_lower,
            color="darkred",
            va="bottom",
            ha="right",
            fontsize=8,
            fontweight="bold",
            bbox=bbox_style,  # And also here
        )
        ax.text(
            text_x_pos,
            upper_bound,
            eq_upper,
            color="darkred",
            va="bottom",
            ha="right",
            fontsize=8,
            fontweight="bold",
            bbox=bbox_style,  # And also here
        )

    # The rest of the plotting logic is unchanged
    pfas_lower = lower_bound(pfas_df[target_col_x]) if is_dynamic else lower_bound
    pfas_upper = upper_bound(pfas_df[target_col_x]) if is_dynamic else upper_bound
    tp_df = pfas_df[
        (pfas_df[target_col_y] >= pfas_lower) & (pfas_df[target_col_y] <= pfas_upper)
    ]
    fn_df = pfas_df.drop(tp_df.index)
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
    fp_df = lipid_df.drop(tn_df.index)
    ax.scatter(
        tn_df[target_col_x],
        tn_df[target_col_y],
        c="blue",
        marker="o",
        alpha=0.6,
        label=f"True Negatives: {results['confusion_matrix']['TN']}",
    )
    ax.scatter(
        tp_df[target_col_x],
        tp_df[target_col_y],
        c="green",
        marker="o",
        alpha=0.6,
        label=f"True Positives: {results['confusion_matrix']['TP']}",
    )
    ax.scatter(
        fp_df[target_col_x],
        fp_df[target_col_y],
        c="red",
        marker="x",
        s=50,
        label=f"False Positives: {results['confusion_matrix']['FP']}",
    )
    ax.scatter(
        fn_df[target_col_x],
        fn_df[target_col_y],
        c="orange",
        marker="x",
        s=50,
        label=f"False Negatives: {results['confusion_matrix']['FN']}",
    )
    metrics = results["metrics"]
    stats_text = f"Accuracy: {metrics['Accuracy']:.2%}\nSensitivity: {metrics['Sensitivity']:.2%}\nSelectivity: {metrics['Selectivity']:.2%}"
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
    ax.set_title(f"{model_type} Model Performance", fontsize=8, fontweight="bold")
    ax.set_xlabel("M-H-", fontsize=8)
    ax.set_ylabel("Mass Defect", fontsize=8)

    ax.tick_params(axis="both", which="major", labelsize=8)
    plt.tight_layout()
    plt.savefig(
        r"PIMMS v1.2\testing_expanded_library\PFAS_performance\fixed_performance.png"
    )
    plt.show()


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
    # These functions match the 'is_dynamic' structure in your helper functions
    lower_bound_func = lambda x: slope * x + intercept_lower
    upper_bound_func = lambda x: slope * x + intercept_upper

    # --- 7. Evaluate Performance ---
    print("\nEvaluating linear bounds model...")
    performance_results = calculate_performance(
        pfas_df, lipid_df, lower_bound_func, upper_bound_func
    )

    if performance_results:
        print("\nPerformance Metrics:")
        [
            print(f"  - {key}: {value:.2%}")
            for key, value in performance_results["metrics"].items()
        ]

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


def optimize_fixed_bounds(pfas_df, lipid_df):
    """
    Calculates and evaluates a fixed-bound model using 5th/95th percentiles.
    """
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
        [
            print(f"  - {key}: {value:.2%}")
            for key, value in performance_results["metrics"].items()
        ]
        print("\nGenerating performance plot for fixed bounds model...")
        plot_model_performance(
            pfas_df,
            lipid_df,
            lower_bound,
            upper_bound,
            performance_results,
            "Fixed Bounds",  # This string is used for the dynamic filename
        )


def main():
    FILES = {
        "pfas": r"PIMMS v1.2\testing_expanded_library\halogenated_processed_with_mass_defect.csv",
        "lipids": r"PIMMS v1.2\testing_expanded_library\lipid_processed_with_defect.csv",
    }
    try:
        pfas_data = pd.read_csv(FILES["pfas"])
        lipid_data = pd.read_csv(FILES["lipids"])
        optimize_fixed_bounds(pfas_data, lipid_data)
    except FileNotFoundError as e:
        print(f"\n[ERROR] File not found: {e}")
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
