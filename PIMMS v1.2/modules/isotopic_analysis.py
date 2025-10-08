import numpy as np


def heavy_halogen_hunter(df):
    """
    Checks each row for an M+2 isotopic signature characteristic of Cl or Br,
    and adds a column with the raw M+2/M isotopic ratio.
    This version uses np.select for efficient, vectorized operation.

    Args:
        df (pd.DataFrame): DataFrame containing 'Intensity_1' and 'Intensity_3'.

    Returns:
        pd.DataFrame: The input DataFrame with new 'M/M+2 Distribution' and 'Heavy_Halogen' columns.
    """
    # --- NEW: Calculate the ratio and add it as a new column ---
    # Initialize the new column with NaN (Not a Number)
    df["M/M+2 Distribution"] = np.nan

    # Create a mask for rows where division is safe (Intensity_1 > 0)
    safe_division_mask = df["Intensity_1"] > 0

    # Calculate the ratio only for the safe rows and fill the new column
    df.loc[safe_division_mask, "M/M+2 Distribution"] = (
        df.loc[safe_division_mask, "Intensity_3"]
        / df.loc[safe_division_mask, "Intensity_1"]
    )
    # --- End of New Code ---

    # Define the conditions in order of priority, now using the new ratio column
    conditions = [
        df["M/M+2 Distribution"] > 0.28,
        (df["Intensity_3"] == 0) | (df["Intensity_3"].isna()),
    ]

    # Define the choices corresponding to each condition
    choices = [
        "Potential Cl, Br present",
        "No M+2 peak detected - insufficient signal",
    ]

    # The default value if no conditions are met
    default_choice = "No Cl or Br isotopic pattern detected"

    # Create the 'Isotopic_analysis' classification column using np.select
    df["Isotopic_analysis"] = np.select(conditions, choices, default=default_choice)

    return df
