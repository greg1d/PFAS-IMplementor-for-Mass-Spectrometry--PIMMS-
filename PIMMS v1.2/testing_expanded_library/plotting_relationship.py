from library_reading import (  # type: ignore
    read_and_clean_csv,
    extract_pfas_features,
    extract_halogenated_features,
    calculate_total_mass_defect,
    filter_by_allowed_elements,
)
import re
from collections import defaultdict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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

    print("Fitted Quantile Regression Equations for the combined dataset:")
    print(
        f"  5th Percentile: y = {model_05.params['log_x']:.4f} * log(x) + {model_05.params['Intercept']:.4f}"
    )
    print(
        f" 95th Percentile: y = {model_95.params['log_x']:.4f} * log(x) + {model_95.params['Intercept']:.4f}"
    )

    return {
        "q05_intercept": model_05.params["Intercept"],
        "q05_slope": model_05.params["log_x"],
        "q95_intercept": model_95.params["Intercept"],
        "q95_slope": model_95.params["log_x"],
    }


# --- 2. The New Plotting Function ---


def plot_dual_quantile_bounds(pfas_df, halogen_df, x_col="M-H-", y_col="Mass_Defect"):
    """
    Generates a scatter plot with separate 95% prediction intervals
    for both the PFAS and Halogenated data series.
    """
    print("\n--- Generating Scatter Plot with Dual Quantile Regression Bounds ---")

    # --- Create the main plot figure ---
    fig, ax = plt.subplots(figsize=(12, 8))

    # --- Plotting Block for HALOGENATED Data ---
    print("\nFitting model for Halogenated data...")
    if not halogen_df.empty:
        coeffs_halogen = fit_quantile_regression(halogen_df, x_col, y_col)
        ax.scatter(
            halogen_df[x_col],
            halogen_df[y_col],
            label="Halogenated Features",
            color="blue",
            marker="o",
            alpha=0.4,
        )
        x_line_halogen = np.linspace(
            halogen_df[x_col].min(), halogen_df[x_col].max(), 100
        )
        log_x_halogen = np.log(x_line_halogen)
        y_line_05_h = (
            coeffs_halogen["q05_slope"] * log_x_halogen
            + coeffs_halogen["q05_intercept"]
        )
        y_line_95_h = (
            coeffs_halogen["q95_slope"] * log_x_halogen
            + coeffs_halogen["q95_intercept"]
        )
        ax.fill_between(
            x_line_halogen,
            y_line_05_h,
            y_line_95_h,
            color="blue",
            alpha=0.15,
            label="Halogenated 95% Interval",
        )
        ax.plot(x_line_halogen, y_line_05_h, color="blue", linestyle="--")
        ax.plot(x_line_halogen, y_line_95_h, color="blue", linestyle="--")

    # --- Plotting Block for PFAS Data ---
    print("\nFitting model for PFAS data...")
    if not pfas_df.empty:
        coeffs_pfas = fit_quantile_regression(pfas_df, x_col, y_col)
        ax.scatter(
            pfas_df[x_col],
            pfas_df[y_col],
            label="PFAS Features",
            color="red",
            marker="x",
            alpha=0.6,
        )
        x_line_pfas = np.linspace(pfas_df[x_col].min(), pfas_df[x_col].max(), 100)
        log_x_pfas = np.log(x_line_pfas)
        y_line_05_p = (
            coeffs_pfas["q05_slope"] * log_x_pfas + coeffs_pfas["q05_intercept"]
        )
        y_line_95_p = (
            coeffs_pfas["q95_slope"] * log_x_pfas + coeffs_pfas["q95_intercept"]
        )
        ax.fill_between(
            x_line_pfas,
            y_line_05_p,
            y_line_95_p,
            color="red",
            alpha=0.15,
            label="PFAS 95% Interval",
        )
        ax.plot(x_line_pfas, y_line_05_p, color="red", linestyle="--")
        ax.plot(x_line_pfas, y_line_95_p, color="red", linestyle="--")

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
    lipid_path = r"PIMMS v1.2\testing_expanded_library\Negative_lipid_library.csv"

    lipid_df = read_and_clean_csv(lipid_path)
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

    print(lipid_df)
    # --- FIX 2: Ensure plotting columns are numeric and valid for log ---
    plot_cols = ["M-H-", "Mass_Defect"]
    for col in plot_cols:
        # Convert to numbers, turning any non-numeric text into NaN (Not a Number)
        PFAS_library[col] = pd.to_numeric(PFAS_library[col], errors="coerce")
        halogenated_library[col] = pd.to_numeric(
            halogenated_library[col], errors="coerce"
        )

    # Drop rows where the conversion failed
    PFAS_library.dropna(subset=plot_cols, inplace=True)
    halogenated_library.dropna(subset=plot_cols, inplace=True)

    # --- 5. Call the plotting function with the cleaned data ---
    plot_dual_quantile_bounds(
        pfas_df=PFAS_library,
        halogen_df=halogenated_library,
        x_col="M-H-",
        y_col="Mass_Defect",
    )


if __name__ == "__main__":
    main()
