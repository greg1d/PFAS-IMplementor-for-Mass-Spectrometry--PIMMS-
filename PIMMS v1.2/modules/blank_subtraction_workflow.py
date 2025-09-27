import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "modules"))
from blank_subtraction import (
    method_1_blank_subtraction,
    method_2_blank_subtraction,
)


def perform_blank_subtraction(method, control_df, experimental_df):
    """
    Performs blank subtraction based on the selected method.

    Args:
        method (str): The method number ('1', '2', or '3').
        control_df (pd.DataFrame): Control DataFrame.
        experimental_df (pd.DataFrame): Experimental DataFrame.

    Returns:
        pd.DataFrame: Adjusted experimental DataFrame.
    """
    if method == "1":
        adjusted_df, control_mean, control_std = method_1_blank_subtraction(
            control_df, experimental_df
        )

        return adjusted_df, control_mean, control_std

    elif method == "2":
        std_deviation_factor = float(
            input("Enter the number of standard deviations for subtraction: ")
        )
        adjusted_df, control_mean, control_std = method_2_blank_subtraction(
            control_df, experimental_df, std_deviation_factor
        )
        return adjusted_df, control_mean, control_std

    else:
        raise ValueError("Invalid method selected.")
