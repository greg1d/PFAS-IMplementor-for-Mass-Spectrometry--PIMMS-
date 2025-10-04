import pandas as pd


def calculate_KMD(df):
    """
    Calculates multiple variations of the Kendrick Mass Defect (KMD) for each
    feature based on its m/z and adds them as new columns to the DataFrame.

    The function calculates KMD for the following repeating units:
    - CF2
    - OCF2
    - CH2
    - CHF
    - OCH2

    Args:
        df (pd.DataFrame): The input DataFrame which must contain an 'm/z' column.

    Returns:
        pd.DataFrame: The DataFrame with new KMD columns added for each variation.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        print(
            "[WARNING] KMD calculation: Input is not a valid DataFrame. Returning as is."
        )
        return df

    df_out = df.copy()

    # --- Validation ---
    if "m/z" not in df_out.columns:
        print("[ERROR] KMD calculation: 'm/z' column not found. Cannot calculate KMDs.")
        return df_out

    if not pd.api.types.is_numeric_dtype(df_out["m/z"]):
        print(
            "[ERROR] KMD calculation: 'm/z' column is not numeric. Cannot calculate KMDs."
        )
        return df_out

    # --- Define all KMD calculations ---
    # Dictionary format: {'Output Column Name': multiplier}
    kmd_rules = {
        "KMD (CF2)": 50 / 49.99681,
        "KMD (OCF2)": 66 / 65.99172,
        "KMD (CH2)": 14 / 14.01565,
        "KMD (CHF)": 32 / 32.00623,
        "KMD (OCH2)": 30 / 30.01056,
    }

    # --- Loop through the rules and calculate each KMD ---
    for column_name, multiplier in kmd_rules.items():
        # 1. Multiply the m/z value by the factor
        multiplied_value = df_out["m/z"] * multiplier

        # 2. Round the result to the nearest integer
        rounded_integer_value = multiplied_value.round(0)

        # 3. Calculate KMD and assign it to the new column
        df_out[column_name] = rounded_integer_value - multiplied_value

    return df_out


def main():
    adjusted_df = pd.read_csv("PIMMS v1.2/import folder/Dummy test output.csv")

    adjusted_df = calculate_KMD(adjusted_df)
    print(adjusted_df.head())


if __name__ == "__main__":
    main()
