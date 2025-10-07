import pandas as pd
import os
import numpy as np


def compute_kaufman_constants(cef_data_df):
    """
    Computes Kaufman C and derived metrics. Now also extracts the 3rd peak's intensity.
    """
    kaufman_data = []
    grouped = cef_data_df.groupby(["SourceFile", "Compound"])
    for (source_file, compound_id), group in grouped:
        if len(group) < 2:
            continue

        sorted_group = group.sort_values("Peak_mz").reset_index(drop=True)
        intensity1 = sorted_group.loc[0, "Peak_intensity"]
        intensity2 = sorted_group.loc[1, "Peak_intensity"]
        mz1 = sorted_group.loc[0, "Peak_mz"]
        mz2 = sorted_group.loc[1, "Peak_mz"]

        # NEW: Safely get the third peak's intensity if it exists
        intensity3 = np.nan
        if len(sorted_group) >= 3:
            intensity3 = sorted_group.loc[2, "Peak_intensity"]

        if intensity1 == 0:
            continue
        kaufman_C = (intensity2 / intensity1) * (1 / 0.011145)
        if kaufman_C == 0:
            continue

        mass_defect = mz1 - round(mz1)
        sample_name = os.path.splitext(source_file)[0].strip()

        kaufman_data.append(
            {
                "Sample": sample_name,
                "Compound": compound_id,
                "Peak_mz_1": mz1,
                "Intensity_1": intensity1,
                "Peak_mz_2": mz2,
                "Intensity_2": intensity2,
                "Intensity_3": intensity3,  # Add the new field
                "Kaufman_C": kaufman_C,
                "m_over_C": mz1 / kaufman_C,
                "mass_defect": mass_defect,
                "md_over_C": mass_defect / kaufman_C,
            }
        )
    return pd.DataFrame(kaufman_data)
