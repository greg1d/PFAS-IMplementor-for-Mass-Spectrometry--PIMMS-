# Save this code as a file named, for example, 'analyze_data.py'

import pandas as pd


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
    Filters a DataFrame to find rows containing a specific PFAS-like SMILES pattern.

    Args:
        input_df (pd.DataFrame): The DataFrame to filter.

    Returns:
        pd.DataFrame: A new DataFrame containing only the filtered PFAS features.
    """
    column_to_search = "SMILES_Dashboard"
    if column_to_search not in input_df.columns:
        print(
            f"Warning: Column '{column_to_search}' not found for PFAS filtering. Skipping."
        )
        return pd.DataFrame()  # Return an empty DataFrame

    # Escape the parentheses for the search pattern
    substring_pattern = r"F\)\(F"

    condition = input_df[column_to_search].str.contains(substring_pattern, na=False)
    pfas_df = input_df[condition].copy()

    print(
        f"Found {len(pfas_df)} rows matching the PFAS SMILES pattern '{substring_pattern}'."
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


def main():
    """
    Main workflow to read, process, and filter the data.
    """
    # Define the file to be analyzed
    file_path = r"PIMMS v1.2\testing_expanded_library\susdat_2025-06-03-092022.csv"

    # 1. Read and prepare the main DataFrame
    main_df = read_and_clean_csv(file_path)

    # 2. Apply initial filter to get the 'negative_esi_mode' subset
    print("\nApplying initial filter for ESI mode and Platform...")
    condition = (main_df["Pred. ESI mode"] == "Negative ESI") & (
        main_df["Preferable Platform by decision Tree"] == "RPLC_-ESI"
    )

    negative_esi_df = main_df[condition].copy()

    # 3. From the 'negative_esi_df', extract PFAS features
    extract_pfas_features(negative_esi_df)

    # 4. From the 'negative_esi_df', extract halogenated features
    extract_halogenated_features(negative_esi_df)


if __name__ == "__main__":
    main()
