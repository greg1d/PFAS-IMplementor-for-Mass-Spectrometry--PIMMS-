import re
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from library_reading import (  # type: ignore
    calculate_total_mass_defect,
    extract_halogenated_features,
    extract_pfas_features,
    filter_by_allowed_elements,
    read_and_clean_csv,
)
from patsy import dmatrix
from statsmodels.regression.quantile_regression import QuantReg

# --- 1. The Refactored Quantile Regression Model ---


def count_elements_in_formula(formula):
    """
    Parses a chemical formula string and returns a dictionary of element counts.
    """
    if not isinstance(formula, str):
        return {}
    counts = defaultdict(int)
    element_pattern = r"([A-Z][a-z]*)(\d*)"
    for element, count in re.findall(element_pattern, formula):
        counts[element] += int(count) if count else 1
    return dict(counts)


def fit_quantile_regression(df, x_col, y_col):
    """
    Fits a logarithmic quantile regression model to a given DataFrame
    for the 5th and 95th percentiles.
    """
    model_df = df[[x_col, y_col]].dropna().copy()
    model_df["log_x"] = np.log(model_df[x_col])

    X = dmatrix("1 + log_x", model_df, return_type="dataframe")
    model_05 = QuantReg(model_df[y_col], X).fit(q=0.10)
    model_95 = QuantReg(model_df[y_col], X).fit(q=0.90)

    return {
        "q10_intercept": model_05.params["Intercept"],
        "q10_slope": model_05.params["log_x"],
        "q90_intercept": model_95.params["Intercept"],
        "q90_slope": model_95.params["log_x"],
    }


def plot_multi_class_quantile_bounds(
    pfas_df, halogen_df, lipid_df, x_col="M-H-", y_col="Mass_Defect"
):
    """
    [MODIFIED] Generates a scatter plot with separate 95% prediction intervals
    for the PFAS, Halogenated, and Lipid data series.
    """
    print("\n--- Generating Scatter Plot with 3-Class Quantile Regression Bounds ---")

    fig, ax = plt.subplots(figsize=(12, 8))

    # --- Plotting Block for HALOGENATED Data ---
    print("\nFitting model for Halogenated data...")
    if not halogen_df.empty:
        coeffs = fit_quantile_regression(halogen_df, x_col, y_col)
        ax.scatter(
            halogen_df[x_col],
            halogen_df[y_col],
            label="Halogenated Features",
            color="blue",
            marker="o",
            alpha=0.4,
        )
        x_line = np.linspace(halogen_df[x_col].min(), halogen_df[x_col].max(), 100)
        y_line_05 = coeffs["q10_slope"] * np.log(x_line) + coeffs["q10_intercept"]
        y_line_95 = coeffs["q90_slope"] * np.log(x_line) + coeffs["q90_intercept"]
        ax.fill_between(
            x_line,
            y_line_05,
            y_line_95,
            color="blue",
            alpha=0.15,
            label="Halogenated 95% Interval",
        )
        ax.plot(x_line, y_line_05, color="blue", linestyle="--")
        ax.plot(x_line, y_line_95, color="blue", linestyle="--")

    # --- Plotting Block for PFAS Data ---
    print("\nFitting model for PFAS data...")
    if not pfas_df.empty:
        coeffs = fit_quantile_regression(pfas_df, x_col, y_col)
        ax.scatter(
            pfas_df[x_col],
            pfas_df[y_col],
            label="PFAS Features",
            color="red",
            marker="x",
            alpha=0.6,
        )
        x_line = np.linspace(pfas_df[x_col].min(), pfas_df[x_col].max(), 100)
        y_line_05 = coeffs["q10_slope"] * np.log(x_line) + coeffs["q10_intercept"]
        y_line_95 = coeffs["q90_slope"] * np.log(x_line) + coeffs["q90_intercept"]
        ax.fill_between(
            x_line,
            y_line_05,
            y_line_95,
            color="red",
            alpha=0.15,
            label="PFAS 95% Interval",
        )
        ax.plot(x_line, y_line_05, color="red", linestyle="--")
        ax.plot(x_line, y_line_95, color="red", linestyle="--")

    # --- NEW: Plotting Block for LIPID Data ---
    print("\nFitting model for Lipid data...")
    if not lipid_df.empty:
        coeffs = fit_quantile_regression(lipid_df, x_col, y_col)
        ax.scatter(
            lipid_df[x_col],
            lipid_df[y_col],
            label="Lipid Features",
            color="green",
            marker="^",
            alpha=0.5,
        )
        x_line = np.linspace(lipid_df[x_col].min(), lipid_df[x_col].max(), 100)
        y_line_05 = coeffs["q10_slope"] * np.log(x_line) + coeffs["q10_intercept"]
        y_line_95 = coeffs["q90_slope"] * np.log(x_line) + coeffs["q90_intercept"]
        ax.fill_between(
            x_line,
            y_line_05,
            y_line_95,
            color="green",
            alpha=0.15,
            label="Lipid 95% Interval",
        )
        ax.plot(x_line, y_line_05, color="green", linestyle="--")
        ax.plot(x_line, y_line_95, color="green", linestyle="--")

    # --- Finalize the plot ---
    ax.set_xlabel(x_col, fontsize=12)
    ax.set_ylabel(y_col, fontsize=12)
    ax.set_title(f"95% Prediction Intervals for {y_col} vs. {x_col}", fontsize=16)
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.6)

    print("\n✔️ Plot generated. Displaying now...")
    plt.show()


def calculate_m_minus_h(formula, element_masses_dict):
    """
    Calculates the [M-H]- mass for a given molecular formula.

    This is done by summing the exact masses of all atoms in the formula and
    then subtracting the mass of a single hydrogen atom.

    Args:
        formula (str): The chemical formula string (e.g., "C8H4F15O2").
        element_masses_dict (dict): A dictionary of element symbols to their exact masses.

    Returns:
        float: The calculated [M-H]- mass, or 0.0 for invalid input.
    """
    element_counts = count_elements_in_formula(formula)

    if not element_counts:
        return 0.0

    total_exact_mass = 0.0

    for element, count in element_counts.items():
        if element in element_masses_dict:
            total_exact_mass += element_masses_dict[element] * count
        else:
            print(
                f"[Warning] Mass for element '{element}' in formula '{formula}' not found. It will be ignored."
            )

    # Subtract the mass of one hydrogen atom
    m_minus_h_mass = total_exact_mass

    return m_minus_h_mass


def plot_multi_class_scatter(
    pfas_df, halogen_df, lipid_df, x_col="M-H-", y_col="Mass_Defect"
):
    """
    Generates and displays a scatter plot with three distinct series:
    PFAS, Halogenated, and Lipid features.

    Args:
        pfas_df (pd.DataFrame): DataFrame containing the PFAS features.
        halogen_df (pd.DataFrame): DataFrame containing the Halogenated features.
        lipid_df (pd.DataFrame): DataFrame containing the Lipid features.
        x_col (str): The column name to use for the x-axis.
        y_col (str): The column name to use for the y-axis.
    """
    print("\n--- Generating 3-Class Scatter Plot ---")

    # --- Validation: Check if the required columns exist in all DataFrames ---
    for df, name in [
        (pfas_df, "PFAS"),
        (halogen_df, "Halogenated"),
        (lipid_df, "Lipid"),
    ]:
        if not all(col in df.columns for col in [x_col, y_col]):
            raise KeyError(
                f"The '{name}' DataFrame is missing one of the required plotting columns: '{x_col}' or '{y_col}'."
            )

    # --- Plotting Logic ---
    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot the PFAS library series
    ax.scatter(
        x=pfas_df[x_col],
        y=pfas_df[y_col],
        label="PFAS Features",
        color="red",
        marker="x",
        alpha=0.7,
    )

    # Plot the halogenated library series
    ax.scatter(
        x=halogen_df[x_col],
        y=halogen_df[y_col],
        label="Halogenated Features",
        color="blue",
        marker="o",
        alpha=0.6,
    )

    # Plot the lipid series
    ax.scatter(
        x=lipid_df[x_col],
        y=lipid_df[y_col],
        label="Lipid Features",
        color="green",
        marker="^",  # Triangle marker
        alpha=0.6,
    )

    # Add labels, title, and a legend to make the plot informative
    ax.set_xlabel(x_col, fontsize=12)
    ax.set_ylabel(y_col, fontsize=12)
    ax.set_title(f"{y_col} vs. {x_col} by Class", fontsize=16)
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.6)

    # Display the plot
    print("✔️ Plot generated. Displaying now...")
    plt.show()


import json


def remove_duplicate_formulas(df, formula_col="Molecular_Formula"):
    """
    Removes duplicate rows from a DataFrame based on a specified formula column,
    keeping only the first occurrence of each unique formula.

    Args:
        df (pd.DataFrame): The DataFrame to filter.
        formula_col (str): The name of the column containing the molecular formulas.

    Returns:
        pd.DataFrame: A new DataFrame with duplicate formulas removed.
    """
    # Gracefully handle an empty DataFrame or a missing column
    if df.empty or formula_col not in df.columns:
        print(
            f"Input DataFrame is empty or missing '{formula_col}' column. Returning as is."
        )
        return df

    initial_rows = len(df)

    # Use drop_duplicates to find and remove rows with non-unique formulas
    # 'subset' tells pandas which column(s) to check for duplicates
    # 'keep' tells pandas which of the duplicates to keep ('first', 'last', or False to remove all)
    unique_df = df.drop_duplicates(subset=[formula_col], keep="first").reset_index(
        drop=True
    )

    final_rows = len(unique_df)
    rows_removed = initial_rows - final_rows

    print(f"✔️ Removed {rows_removed} duplicate rows based on '{formula_col}'.")

    return unique_df


def save_coefficients_to_json(coeffs_dict, file_path):
    """Saves a dictionary of model coefficients to a JSON file."""
    try:
        with open(file_path, "w") as f:
            # json.dump writes the dictionary to the file
            # indent=4 makes the file nicely formatted and easy to read
            json.dump(coeffs_dict, f, indent=4)
        print(f"✔️ Model boundaries successfully saved to: {file_path}")
    except Exception as e:
        print(f"Error: Failed to save coefficients to {file_path}. Reason: {e}")


def main():
    """
    Main workflow to read, process, and filter the data.
    """
    ELEMENT_MASSES = {
        "H": 1.007825,
        "C": 12.000000,
        "N": 14.003074,
        "O": 15.994915,
        "F": 18.998403,
        "P": 30.973762,
        "S": 31.972071,
        "Cl": 34.968853,  # Mass of Chlorine-35 isotope
        "Br": 78.918337,  # Mass of Bromine-79 isotope
        "I": 126.904473,
        "K": 38.963707,
        "Li": 7.016003,  # Mass of Lithium-7 isotope
        "Mg": 23.985042,
    }
    # Define the file to be analyzed
    file_path = r"PIMMS v1.2\testing_expanded_library\susdat_2025-06-03-092022.csv"
    lipid_path = (
        r"PIMMS v1.2\testing_expanded_library\Negative_lipid_library_processed.csv"
    )

    lipid_df = read_and_clean_csv(lipid_path)
    lipid_df = remove_duplicate_formulas(lipid_df, formula_col="Molecular_Formula")
    # 1. Read and prepare the main DataFrame
    main_df = read_and_clean_csv(file_path)
    allowed_elements = {"F", "H", "I", "O", "P", "S", "C", "Br", "Cl", "N"}
    main_df = filter_by_allowed_elements(main_df, allowed_elements)

    # 2. Apply initial filter
    print("\nApplying initial filter for ESI mode and Platform...")
    condition = (main_df["Pred. ESI mode"] == "Negative ESI") & (
        main_df["Preferable Platform by decision Tree"] == "RPLC_-ESI"
    )
    negative_esi_df = main_df[condition].copy()

    # 3. Extract feature subsets
    PFAS_library = extract_pfas_features(negative_esi_df)
    halogenated_library = extract_halogenated_features(negative_esi_df)

    # 4. Calculate Mass Defect for both libraries
    #    --- FIX 1: Pass the required ELEMENT_MASSES dictionary ---
    PFAS_library["Mass_Defect"] = PFAS_library["Molecular_Formula"].apply(
        lambda formula: calculate_total_mass_defect(formula)
    )
    halogenated_library["Mass_Defect"] = halogenated_library["Molecular_Formula"].apply(
        lambda formula: calculate_total_mass_defect(formula)
    )
    lipid_df["Mass_Defect"] = lipid_df["Molecular_Formula"].apply(
        lambda formula: calculate_total_mass_defect(formula)
    )
    lipid_df["M-H-"] = lipid_df["Molecular_Formula"].apply(
        lambda formula: calculate_m_minus_h(formula, ELEMENT_MASSES)
    )

    # --- FIX 2: Ensure plotting columns are numeric and valid for log ---
    plot_cols = ["M-H-", "Mass_Defect"]
    for col in plot_cols:
        # Convert to numbers, turning any non-numeric text into NaN (Not a Number)
        PFAS_library[col] = pd.to_numeric(PFAS_library[col], errors="coerce")
        halogenated_library[col] = pd.to_numeric(
            halogenated_library[col], errors="coerce"
        )
    lipid_df.to_csv(
        r"PIMMS v1.2\testing_expanded_library\Negative_lipid_library_processed.csv",
        index=False,
    )
    halogenated_library.to_csv(
        r"PIMMS v1.2\testing_expanded_library\halogenated_processed_with_mass_defect.csv",
        index=False,
    )
    PFAS_library.to_csv(
        r"PIMMS v1.2\testing_expanded_library\pfas_processed_with_mass_defect.csv",
        index=False,
    )
    x_col, y_col = "M-H-", "Mass_Defect"

    coeffs_halogen = fit_quantile_regression(halogenated_library, x_col, y_col)
    coeffs_pfas = fit_quantile_regression(PFAS_library, x_col, y_col)
    coeffs_lipid = fit_quantile_regression(lipid_df, x_col, y_col)
    print("\nHalogenated Coefficients:", coeffs_halogen)
    print("PFAS Coefficients:", coeffs_pfas)
    print("Lipid Coefficients:", coeffs_lipid)
    all_model_coeffs = {
        "PFAS": coeffs_pfas,
        "Halogenated": coeffs_halogen,
        "Lipid": coeffs_lipid,
    }
    save_coefficients_to_json(all_model_coeffs, "model_boundaries.json")

    plot_multi_class_scatter(PFAS_library, halogenated_library, lipid_df)
    plot_multi_class_quantile_bounds(PFAS_library, halogenated_library, lipid_df)


if __name__ == "__main__":
    main()
