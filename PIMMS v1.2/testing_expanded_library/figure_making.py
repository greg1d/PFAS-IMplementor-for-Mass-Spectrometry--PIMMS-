import pandas as pd
import numpy as np
from patsy import dmatrix
from statsmodels.regression.quantile_regression import QuantReg
from matplotlib import pyplot as plt
import seaborn as sns

# --- Import your custom functions ---
# This assumes your other functions are in these files and are correct
from library_reading import (
    read_and_clean_csv,
    extract_pfas_features,
    extract_halogenated_features,
    calculate_total_mass_defect,
    filter_by_allowed_elements,
)
from plotting_relationship import (
    remove_duplicate_formulas,
    calculate_m_minus_h,
)

# --- CONSTANTS ---
ELEMENT_MASSES = {
    "H": 1.007825,
    "C": 12.000000,
    "N": 14.003074,
    "O": 15.994915,
    "F": 18.998403,
    "P": 30.973762,
    "S": 31.972071,
    "Cl": 34.968853,
    "Br": 78.918337,
    "I": 126.904473,
    "K": 38.963707,
    "Li": 7.016003,
    "Mg": 23.985042,
}
path_pfas = r"PIMMS v1.2\testing_expanded_library\pfas_processed.csv"
path_halogen = r"PIMMS v1.2\testing_expanded_library\halogenated_processed.csv"
path_lipid = r"PIMMS v1.2\testing_expanded_library\lipid_processed.csv"


# --- HELPER FUNCTIONS ---
def fit_quantile_regression(df, x_col, y_col):
    """Fits a logarithmic quantile regression model for the 5th and 95th percentiles."""
    model_df = df[[x_col, y_col]].dropna().copy()
    if model_df.empty or (model_df[x_col] <= 0).any():
        print(
            f"Warning: Cannot fit model for {y_col} due to empty data or non-positive x-values."
        )
        return None
    model_df["log_x"] = np.log(model_df[x_col])
    X = dmatrix("1 + log_x", model_df, return_type="dataframe")
    model_05 = QuantReg(model_df[y_col], X).fit(q=0.01)
    model_95 = QuantReg(model_df[y_col], X).fit(q=0.99)
    return {
        "q05_intercept": model_05.params["Intercept"],
        "q05_slope": model_05.params["log_x"],
        "q95_intercept": model_95.params["Intercept"],
        "q95_slope": model_95.params["log_x"],
    }


def is_within_bounds(row, x_col, y_col, model_coeffs):
    """Checks if a feature falls within the provided model bounds."""
    # (This function is unchanged from our previous versions)
    mz_value = row[x_col]
    actual_value = row[y_col]
    if pd.isna(mz_value) or pd.isna(actual_value) or mz_value <= 0:
        return False
    slope_keys = sorted([k for k in model_coeffs if "slope" in k])
    intercept_keys = sorted([k for k in model_coeffs if "intercept" in k])
    if len(slope_keys) != 2 or len(intercept_keys) != 2:
        return False
    log_mz = np.log(mz_value)
    lower_bound = model_coeffs[slope_keys[0]] * log_mz + model_coeffs[intercept_keys[0]]
    upper_bound = model_coeffs[slope_keys[1]] * log_mz + model_coeffs[intercept_keys[1]]
    return (
        min(lower_bound, upper_bound) <= actual_value <= max(lower_bound, upper_bound)
    )


# --- NEW COMPREHENSIVE PERFORMANCE CALCULATION FUNCTION ---
def calculate_comprehensive_performance(
    pfas_df, halogen_df, lipid_df, x_col="M-H-", y_col="Mass_Defect"
):
    """
    Calculates comprehensive performance metrics (Accuracy, Specificity, etc.)
    for the PFAS and Halogenated models.
    """
    datasets = {"PFAS": pfas_df, "Halogenated": halogen_df, "Lipid": lipid_df}
    performance_results = {}

    # --- First, fit a model for each class ---
    print("\n--- Fitting All Models ---")
    coeffs_pfas = fit_quantile_regression(pfas_df, x_col, y_col)
    coeffs_halogen = fit_quantile_regression(halogen_df, x_col, y_col)

    # We don't need to fit the Lipid model if we are only evaluating PFAS and Halogenated
    models_to_evaluate = {"PFAS": coeffs_pfas, "Halogenated": coeffs_halogen}

    # --- Now, evaluate each model ---
    for model_name, model_coeffs in models_to_evaluate.items():
        if not model_coeffs:
            print(
                f"Skipping performance calculation for '{model_name}' as model fitting failed."
            )
            continue

        # Define the "positive" and "negative" datasets for this model
        positive_df = datasets[model_name]
        negative_df = pd.concat(
            [df for name, df in datasets.items() if name != model_name]
        )

        # Calculate the confusion matrix values
        TP = positive_df.apply(
            is_within_bounds, axis=1, args=(x_col, y_col, model_coeffs)
        ).sum()
        FN = len(positive_df) - TP
        FP = negative_df.apply(
            is_within_bounds, axis=1, args=(x_col, y_col, model_coeffs)
        ).sum()
        TN = len(negative_df) - FP

        # Calculate metrics
        total_population = TP + TN + FP + FN
        accuracy = (TP + TN) / total_population if total_population > 0 else 0
        sensitivity = TP / (TP + FN) if (TP + FN) > 0 else 0
        specificity = TN / (TN + FP) if (TN + FP) > 0 else 0
        precision = TP / (TP + FP) if (TP + FP) > 0 else 0

        performance_results[model_name] = {
            "Accuracy": accuracy,
            "Sensitivity (Recall)": sensitivity,
            "Specificity": specificity,
            "Selectivity (Precision)": precision,
        }
    return performance_results


def is_within_fixed_bounds(row, y_col, lower_bound, upper_bound):
    """
    Checks if a feature's y-value falls within simple horizontal bounds.
    """
    actual_value = row[y_col]
    if pd.isna(actual_value):
        return False
    return lower_bound <= actual_value <= upper_bound


def calculate_fixed_bounds_performance(
    pfas_df,
    halogen_df,
    lipid_df,
    y_col="Mass_Defect",
    lower_bound=-0.11,
    upper_bound=0.12,
):
    """
    Calculates performance metrics for a simple fixed-bounds classifier.
    Assumes 'PFAS' is the positive class.
    """
    print(
        f"\n--- Calculating Performance for Fixed Bounds Model [{lower_bound}, {upper_bound}] ---"
    )

    positive_df = pfas_df
    negative_df = pd.concat([halogen_df, lipid_df], ignore_index=True)

    # Calculate the confusion matrix values
    TP = positive_df.apply(
        is_within_fixed_bounds, axis=1, args=(y_col, lower_bound, upper_bound)
    ).sum()
    FN = len(positive_df) - TP
    FP = negative_df.apply(
        is_within_fixed_bounds, axis=1, args=(y_col, lower_bound, upper_bound)
    ).sum()
    TN = len(negative_df) - FP

    # Calculate metrics
    total_population = TP + TN + FP + FN
    accuracy = (TP + TN) / total_population if total_population > 0 else 0
    sensitivity = TP / (TP + FN) if (TP + FN) > 0 else 0
    specificity = TN / (TN + FP) if (TN + FP) > 0 else 0
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0

    return {
        "Accuracy": accuracy,
        "Sensitivity (Recall)": sensitivity,
        "Specificity": specificity,
        "Selectivity (Precision)": precision,
    }


def plot_fixed_bounds_comparison(
    pfas_df,
    halogen_df,
    lipid_df,
    x_col="M-H-",
    y_col="Mass_Defect",
    lower_bound=-0.11,
    upper_bound=0.12,
):
    """
    Generates a scatter plot showing the performance of the fixed-bounds model.
    """
    # Prepare a combined DataFrame for plotting
    pfas_df["Type"] = "PFAS"
    lipid_df["Type"] = "Lipid"
    combined_df = pd.concat([pfas_df, lipid_df], ignore_index=True)

    # Determine classification result for each point
    combined_df["Prediction"] = combined_df.apply(
        is_within_fixed_bounds, axis=1, args=(y_col, lower_bound, upper_bound)
    )

    def determine_classification(row):
        is_positive_class = row["Type"] == "PFAS"
        prediction_is_positive = row["Prediction"]
        if is_positive_class and prediction_is_positive:
            return "True Positive"
        if is_positive_class and not prediction_is_positive:
            return "False Negative"
        if not is_positive_class and prediction_is_positive:
            return "False Positive"
        if not is_positive_class and not prediction_is_positive:
            return "True Negative"

    combined_df["Classification_Result"] = combined_df.apply(
        determine_classification, axis=1
    )

    # Plotting
    print("\n--- Generating Fixed Bounds Debugging Plot ---")
    fig, ax = plt.subplots(figsize=(12, 8))
    palette = {
        "True Positive": "green",
        "False Negative": "orange",
        "False Positive": "red",
        "True Negative": "gray",
    }
    markers = {"PFAS": "o", "Halogenated": "X", "Lipid": "^"}

    sns.scatterplot(
        data=combined_df,
        x=x_col,
        y=y_col,
        hue="Classification_Result",
        style="Type",
        palette=palette,
        markers=markers,
        s=150,
        ax=ax,
    )

    # Draw the fixed horizontal boundary lines
    ax.axhline(
        y=lower_bound,
        color="black",
        linestyle="--",
        label=f"Fixed Bounds [{lower_bound}, {upper_bound}]",
    )
    ax.axhline(y=upper_bound, color="black", linestyle="--")
    ax.axhspan(lower_bound, upper_bound, color="gray", alpha=0.15)

    ax.set_title("Fixed Bounds Model Performance", fontsize=16)
    ax.legend(title="Classification Result")
    plt.show()


# --- CONSTANTS ---
# It's best practice to define constants like this at the top level of the script.
ELEMENT_MASSES = {
    "H": 1.007825,
    "C": 12.000000,
    "N": 14.003074,
    "O": 15.994915,
    "F": 18.998403,
    "P": 30.973762,
    "S": 31.972071,
    "Cl": 34.968853,
    "Br": 78.918337,
    "I": 126.904473,
    "K": 38.963707,
    "Li": 7.016003,
    "Mg": 23.985042,
}


# --- MAIN WORKFLOW ---
def main():
    """Main workflow to load, process, and analyze the data."""

    # --- 1. Data Loading ---
    print("--- Loading and Pre-processing Data Files ---")
    file_path = r"PIMMS v1.2\testing_expanded_library\susdat_2025-06-03-092022.csv"
    lipid_path = r"PIMMS v1.2\testing_expanded_library\Negative_lipid_library.csv"

    # Load and clean main experimental data
    main_df = read_and_clean_csv(file_path)
    allowed_elements = {"F", "H", "I", "O", "P", "S", "C", "Br", "Cl", "N"}
    main_df = filter_by_allowed_elements(main_df, allowed_elements)

    # Load and clean lipid library data
    lipid_df = read_and_clean_csv(lipid_path)
    lipid_df = remove_duplicate_formulas(lipid_df, formula_col="Molecular_Formula")

    # --- 2. Feature Extraction ---
    print("\n--- Extracting Feature Subsets ---")
    # Apply initial filter for ESI mode and Platform
    condition = (main_df["Pred. ESI mode"] == "Negative ESI") & (
        main_df["Preferable Platform by decision Tree"] == "RPLC_-ESI"
    )
    negative_esi_df = main_df[condition].copy()

    # Create the specific feature sets
    pfas_df = extract_pfas_features(negative_esi_df)
    halogen_df = extract_halogenated_features(negative_esi_df)
    print(f"PFAS features count: {len(pfas_df)}")
    print(f"Halogenated features count: {len(halogen_df)}")
    print("\n--- Calculating 'M-H-' and 'Mass_Defect' Columns ---")

    # List of DataFrames to process
    dfs_to_process = [pfas_df, halogen_df, lipid_df]

    for df in dfs_to_process:
        if df.empty or "Molecular_Formula" not in df.columns:
            continue

        # FIX 1: Add 'M-H-' column to ALL dataframes
        df["M-H-"] = df["Molecular_Formula"].apply(
            lambda formula: calculate_m_minus_h(formula, ELEMENT_MASSES)
        )
        # FIX 2: Pass the required ELEMENT_MASSES dictionary to the calculation
        df["Mass_Defect"] = df["Molecular_Formula"].apply(
            lambda formula: calculate_total_mass_defect(formula)
        )

    """Main workflow to load, process, and analyze the data."""
    # (Code for loading and preparing main_df, lipid_df unchanged)
    # (Code for extracting pfas_df, halogen_df unchanged)

    # --- Column Calculation ---
    print("\n--- Calculating 'M-H-' and 'Mass_Defect' Columns ---")
    dfs_to_process = [pfas_df, halogen_df, lipid_df]
    for df in dfs_to_process:
        if df.empty or "Molecular_Formula" not in df.columns:
            continue
        df["M-H-"] = df["Molecular_Formula"].apply(
            lambda f: calculate_m_minus_h(f, ELEMENT_MASSES)
        )
        # --- FIX: Pass the required ELEMENT_MASSES dictionary ---
        df["Mass_Defect"] = df["Molecular_Formula"].apply(
            lambda f: calculate_total_mass_defect(f)
        )

    # --- Data Cleaning for Plotting/Modeling ---
    # (This is the cleaning block from a previous step, which is still required)
    print("\n--- Cleaning and Validating Data for Analysis ---")
    for df in dfs_to_process:
        if df.empty:
            continue
        plot_cols = ["M-H-", "Mass_Defect"]
        for col in plot_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df.dropna(subset=plot_cols, inplace=True)
        if "M-H-" in df.columns:
            df.drop(df[df["M-H-"] <= 0].index, inplace=True)

    # --- Performance Analysis ---
    # This single function call replaces all previous performance calculations
    performance_metrics = calculate_comprehensive_performance(
        pfas_df, halogen_df, lipid_df
    )

    if performance_metrics:
        print("\n\n--- Comprehensive Model Performance Summary ---")
        for model_name, metrics in performance_metrics.items():
            print(f"\nPerformance of '{model_name}' Model Bounds:")
            print(f"  Accuracy:                {metrics['Accuracy']:.2%}")
            print(f"  Sensitivity (Recall):    {metrics['Sensitivity (Recall)']:.2%}")
            print(f"  Specificity:             {metrics['Specificity']:.2%}")
            print(
                f"  Selectivity (Precision): {metrics['Selectivity (Precision)']:.2%}"
            )

    plot_fixed_bounds_comparison(pfas_df.copy(), lipid_df.copy(), lipid_df.copy())


if __name__ == "__main__":
    main()
