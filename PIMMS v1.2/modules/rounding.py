import pandas as pd


def significant_figures_rounding(df):
    """
    Rounds specific columns in a DataFrame to a set number of decimal places.

    This function identifies the 'CCS', 'RT', 'm/z', and 'DT' columns if they
    exist and rounds their values. It handles missing columns gracefully.

    Args:
        df (pd.DataFrame): The input DataFrame to be processed.

    Returns:
        pd.DataFrame: A new DataFrame with the specified columns rounded.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        print("[WARNING] Input is not a valid or non-empty DataFrame. Returning as is.")
        return df

    # Create a copy to avoid modifying the original DataFrame
    df_rounded = df.copy()

    # Define the rounding rules: {'column_name': decimal_places}
    rounding_rules = {"CCS": 1, "RT": 1, "m/z": 4, "DT": 2}

    print("[INFO] Applying rounding rules...")
    for column, decimal_places in rounding_rules.items():
        # Check if the column exists in the DataFrame
        if column in df_rounded.columns:
            # Check if the column is of a numeric type before rounding
            if pd.api.types.is_numeric_dtype(df_rounded[column]):
                df_rounded[column] = df_rounded[column].round(decimals=decimal_places)
                print(
                    f"  - Column '{column}' rounded to {decimal_places} decimal places."
                )
            else:
                print(
                    f"  - [WARNING] Column '{column}' is not numeric and will not be rounded."
                )
        else:
            print(f"  - [INFO] Column '{column}' not found. Skipping.")

    return df_rounded
