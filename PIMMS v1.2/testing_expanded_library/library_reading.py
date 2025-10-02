# Save this code as a file named, for example, 'analyze_data.py'

import pandas as pd
import re
from collections import defaultdict

ELEMENT_MASSES = {
    "H": 1.007825,
    "C": 12.000000,
    "N": 14.003074,
    "O": 15.994915,
    "F": 18.9984032,
    "Mg": 23.98505,
    "P": 30.973763,
    "S": 31.972072,
    "Cl": 34.968853,  # Mass of Chlorine-35 isotope
    "K": 38.963708,
    "Br": 78.918336,  # Mass of Bromine-79 isotope
    "I": 126.904477,
    "Li": 7.016005,  # Mass of Lithium-7 isotope
}


def read_and_clean_csv(file_path):
    """
    Reads a CSV file into a pandas DataFrame and cleans the column names.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        pd.DataFrame: A DataFrame with cleaned column names, or None if an error occurs.
    """
    try:
        print(f"--- Reading and preparing file: {file_path} ---")
        df = pd.read_csv(file_path)
        # Clean whitespace from all column names
        df.columns = [col.strip() for col in df.columns]
        print("✔️ File read and columns cleaned successfully.")
        return df
    except FileNotFoundError:
        print(f"Error: The file was not found at the specified path: {file_path}")
    except pd.errors.EmptyDataError:
        print(f"Error: The file is empty and has no columns: {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred while reading the file: {e}")
    return None


def extract_pfas_features(input_df):
    """
    [MODIFIED] Filters for a specific PFAS-like SMILES pattern and EXCLUDES
    any features containing Cl, Br, or I in their molecular formula.
    """
    # --- 1. Validate that required columns exist ---
    smiles_col = "SMILES_Dashboard"
    formula_col = "Molecular_Formula"

    if smiles_col not in input_df.columns or formula_col not in input_df.columns:
        print(
            f"Warning: DataFrame is missing required columns ('{smiles_col}' or '{formula_col}'). Skipping PFAS filter."
        )
        return pd.DataFrame()

    # --- 2. Define the two filtering conditions ---

    # Condition A: Rows MUST contain the F)(F SMILES pattern
    pfas_pattern = r"F\)\(F"
    pfas_condition = input_df[smiles_col].str.contains(pfas_pattern, na=False)

    # Condition B: Rows MUST NOT contain Cl, Br, or I in their formula
    halogen_pattern = "Br|Cl|I"
    # The '~' (tilde) symbol inverts the condition, effectively meaning 'NOT CONTAINS'
    no_halogen_condition = ~input_df[formula_col].str.contains(
        halogen_pattern, na=False
    )

    # --- 3. Combine both conditions with AND (&) ---
    final_condition = pfas_condition & no_halogen_condition

    # Apply the final combined filter
    pfas_df = input_df[final_condition].copy()

    print(
        f"Found {len(pfas_df)} rows matching the PFAS SMILES pattern that do not contain Cl, Br, or I."
    )
    return pfas_df


def extract_halogenated_features(input_df):
    """
    Filters a DataFrame to find rows containing specified halogens in their formula.

    Args:
        input_df (pd.DataFrame): The DataFrame to filter.

    Returns:
        pd.DataFrame: A new DataFrame containing only the filtered halogenated features.
    """
    column_to_search = "Molecular_Formula"
    if column_to_search not in input_df.columns:
        print(
            f"Warning: Column '{column_to_search}' not found for Halogen filtering. Skipping."
        )
        return pd.DataFrame()

    # The pipe character '|' acts as an "OR" in the search
    search_pattern = "Br|Cl|I"

    condition = input_df[column_to_search].str.contains(search_pattern, na=False)
    halogen_df = input_df[condition].copy()

    print(
        f"Found {len(halogen_df)} rows containing 'Br', 'Cl', or 'I' in their formula."
    )
    return halogen_df


def extract_unique_elements(input_df):
    column_to_parse = "Molecular_Formula"
    if column_to_parse not in input_df.columns:
        print(f"Error: Column '{column_to_parse}' not found in the DataFrame.")
    else:
        # Select the column, drop any empty rows, and ensure it's treated as text
        formulas = input_df[column_to_parse].dropna().astype(str)

        # Define a regular expression to find element symbols (e.g., C, Cl)
    element_pattern = r"[A-Z][a-z]*"

    # Find all occurrences of the pattern in every row
    all_found_elements = formulas.str.findall(element_pattern)

    # Flatten the list of lists into a single set to get the unique elements
    unique_elements = set()
    for element_list in all_found_elements:
        unique_elements.update(element_list)

    # Convert to a sorted list for clean printing
    sorted_unique_elements = sorted(list(unique_elements))
    print(f"Unique elements found in '{column_to_parse}': {sorted_unique_elements}")

    return sorted_unique_elements


def filter_by_allowed_elements(df_to_filter, allowed_elements_set):
    """
    Filters a DataFrame to keep only rows where the 'Molecular_Formula'
    contains elements exclusively from an allowed set.

    Args:
        df_to_filter (pd.DataFrame): The DataFrame to filter.
        allowed_elements_set (set): A set of allowed element symbols (e.g., {'C', 'H', 'O'}).

    Returns:
        pd.DataFrame: A new, filtered DataFrame.
    """
    column_to_parse = "Molecular_Formula"

    # Handle cases where the DataFrame is empty or the column is missing
    if df_to_filter.empty or column_to_parse not in df_to_filter.columns:
        print(
            f"Input DataFrame is empty or missing '{column_to_parse}' column. Returning as is."
        )
        return df_to_filter

    # --- Helper function to check a single formula string ---
    def has_only_allowed_elements(formula, allowed_set):
        # Ignore empty/non-string values
        if not isinstance(formula, str):
            return False

        # Find all element symbols in the formula
        found_elements = set(re.findall(r"[A-Z][a-z]*", formula))

        # Return True only if the set of found elements is a subset of the allowed set
        return found_elements.issubset(allowed_set)

    # --- Apply the filter ---
    # Create a boolean mask by applying the helper function to each row
    mask = df_to_filter[column_to_parse].apply(
        has_only_allowed_elements, args=(allowed_elements_set,)
    )

    # Create the new DataFrame from the mask
    filtered_df = df_to_filter[mask].copy()

    rows_removed = len(df_to_filter) - len(filtered_df)
    print(f"✔️ Filtered by allowed elements. Removed {rows_removed} rows.")

    return filtered_df


def count_elements_in_formula(formula):
    """
    Parses a chemical formula string and counts the atoms of each element.
    """
    if not isinstance(formula, str):
        return {}
    counts = defaultdict(int)
    element_pattern = r"([A-Z][a-z]*)(\d*)"
    for element, count in re.findall(element_pattern, formula):
        counts[element] += int(count) if count else 1
    return dict(counts)


def calculate_total_mass_defect(formula):
    """
    Calculates the total mass defect for a molecular formula.
    Total Defect = SUM[(Nominal Mass - Exact Mass) * Atom Count] for all atoms.
    """
    element_masses_dict = {
        "H": 1.007825,
        "C": 12.000000,
        "N": 14.003074,
        "O": 15.994915,
        "F": 18.9984032,
        "Mg": 23.98505,
        "P": 30.973763,
        "S": 31.972072,
        "Cl": 34.968853,  # Mass of Chlorine-35 isotope
        "K": 38.963708,
        "Br": 78.918336,  # Mass of Bromine-79 isotope
        "I": 126.904477,
        "Li": 7.016005,  # Mass of Lithium-7 isotope
    }
    # First, parse the formula to get the count of each element
    element_counts = count_elements_in_formula(formula)

    if not element_counts:
        return 0.0  # Return 0 for empty or invalid formulas

    total_defect = 0.0

    # Iterate through the elements found in the formula
    for element, count in element_counts.items():
        if element in element_masses_dict:
            exact_mass = element_masses_dict[element]
            # Nominal mass is the nearest integer to the exact mass
            nominal_mass = round(exact_mass)
            # Calculate the defect for a single atom of this element
            element_defect = exact_mass - nominal_mass
            # Add the total defect for this element to the running total
            total_defect += element_defect * count
        else:
            # If an element in the formula is not in our dictionary, print a warning
            print(
                f"[Warning] Mass for element '{element}' not found. It will be ignored in the calculation."
            )

    return total_defect


def main():
    """
    Main workflow to read, process, and filter the data.
    """
    # Define the file to be analyzed
    file_path = r"PIMMS v1.2\testing_expanded_library\susdat_2025-06-03-092022.csv"

    # 1. Read and prepare the main DataFrame
    main_df = read_and_clean_csv(file_path)
    allowed_elements = {
        "F",
        "H",
        "I",
        "O",
        "P",
        "S",
        "C",
        "Br",
        "Cl",
        "N",
    }
    main_df = filter_by_allowed_elements(main_df, allowed_elements)
    # 2. Apply initial filter to get the 'negative_esi_mode' subset
    print("\nApplying initial filter for ESI mode and Platform...")
    condition = (main_df["Pred. ESI mode"] == "Negative ESI") & (
        main_df["Preferable Platform by decision Tree"] == "RPLC_-ESI"
    )

    negative_esi_df = main_df[condition].copy()

    # 3. From the 'negative_esi_df', extract PFAS features
    PFAS_library = extract_pfas_features(negative_esi_df)

    # 4. From the 'negative_esi_df', extract halogenated features
    halogenated_library = extract_halogenated_features(negative_esi_df)
    # 5. Extract and print unique elements from the 'Molecular_Formula' column
    extract_unique_elements(negative_esi_df)
    PFAS_library["Element_Counts"] = PFAS_library["Molecular_Formula"].apply(
        count_elements_in_formula
    )

    halogenated_library["Element_Counts"] = halogenated_library[
        "Molecular_Formula"
    ].apply(count_elements_in_formula)

    PFAS_library["Mass_Defect"] = PFAS_library["Molecular_Formula"].apply(
        lambda formula: calculate_total_mass_defect(formula)
    )

    halogenated_library["Mass_Defect"] = halogenated_library["Molecular_Formula"].apply(
        lambda formula: calculate_total_mass_defect(formula)
    )


if __name__ == "__main__":
    main()
