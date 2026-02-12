import pandas as pd
import numpy as np


def run_transformation_checker(params):
    """
    Core logic for identifying chemical transformations.

    Args:
        params (dict): Dictionary containing:
            - paths: {experimental, suspect, exclusion}
            - mappings: {experimental: 'A', suspect: 'B', exclusion: 'C'}
            - ppm: float (e.g., 5.0)
            - units: list of dicts [{'name': 'CF2', 'mass': 49.99, 'min': -1, 'max': 3}, ...]

    Returns:
        pd.DataFrame: A table of identified transformation pairs.
    """
    print("--- Starting Transformation Analysis ---")

    # 1. LOAD AND STANDARDIZE DATA
    try:
        exp_df = _load_and_map(
            params["paths"]["experimental"],
            params["mappings"]["experimental"],
            "Experimental",
        )

        # Add a unique ID if one doesn't exist to track parent/product relationships
        if "ID" not in exp_df.columns:
            exp_df["ID"] = range(1, len(exp_df) + 1)

    except Exception as e:
        return pd.DataFrame({"Error": [f"Failed to load experimental data: {str(e)}"]})

    # 2. OPTIONAL: EXCLUSION FILTERING
    # If an exclusion library exists, remove matching masses from exp_df
    if params["paths"].get("exclusion") and params["mappings"].get("exclusion"):
        try:
            excl_df = _load_and_map(
                params["paths"]["exclusion"],
                params["mappings"]["exclusion"],
                "Exclusion",
            )
            print(f"Applying Exclusion Filter ({len(excl_df)} entries)...")
            exp_df = _remove_excluded_features(exp_df, excl_df, params["ppm"])
            print(f"Features remaining after exclusion: {len(exp_df)}")
        except Exception as e:
            print(f"[WARNING] Exclusion filtering failed: {e}")

    if exp_df.empty:
        return pd.DataFrame(
            {"Status": ["No experimental features remaining after filtering."]}
        )

    # 3. TRANSFORMATION SEARCH (The "Comb")
    results = []

    # Convert dataframe to simple lists for faster iteration
    exp_masses = exp_df["m/z"].values
    exp_ids = exp_df["ID"].values

    # Pre-calculate ppm tolerance factor
    # tolerance = mass * (ppm / 1e6)
    ppm_factor = params["ppm"] / 1e6

    print(
        f"Scanning {len(exp_df)} features against {len(params['units'])} transformation types..."
    )

    # Iterate through every feature as a potential "Parent"
    for i, parent_mass in enumerate(exp_masses):
        parent_id = exp_ids[i]

        # Check against every unit configured by the user
        for unit_def in params["units"]:
            unit_name = unit_def["name"]
            unit_mass = unit_def["mass"]

            # Check the specific range (e.g., -1 to +3)
            # We iterate through every integer multiplier in the range
            for n in range(unit_def["min"], unit_def["max"] + 1):
                if n == 0:
                    continue  # Skip identity

                # Calculate Theoretical Product Mass
                theoretical_mass = parent_mass + (unit_mass * n)

                # Calculate the search window for this theoretical mass
                tol = theoretical_mass * ppm_factor
                min_mass = theoretical_mass - tol
                max_mass = theoretical_mass + tol

                # SEARCH: Look for this mass in the experimental data
                # (Finding indices where mass is within range)
                matches = np.where((exp_masses >= min_mass) & (exp_masses <= max_mass))[
                    0
                ]

                for match_idx in matches:
                    product_id = exp_ids[match_idx]
                    product_real_mass = exp_masses[match_idx]

                    # Prevent self-matching (though n!=0 usually handles this)
                    if parent_id == product_id:
                        continue

                    # Calculate actual PPM error of the match
                    error_ppm = (
                        abs(product_real_mass - theoretical_mass)
                        / theoretical_mass
                        * 1e6
                    )

                    results.append(
                        {
                            "Parent ID": parent_id,
                            "Parent m/z": round(parent_mass, 4),
                            "Transformation": f"{unit_name}",
                            "n": n,
                            "Theoretical m/z": round(theoretical_mass, 4),
                            "Product ID": product_id,
                            "Product m/z": round(product_real_mass, 4),
                            "PPM Error": round(error_ppm, 2),
                        }
                    )

    results_df = pd.DataFrame(results)

    # 4. SUSPECT MATCHING (Optional)
    # If a suspect library is loaded, check if the *Product* is a known suspect
    if not results_df.empty and params["paths"].get("suspect"):
        try:
            print("Checking matches against Suspect Library...")
            suspect_df = _load_and_map(
                params["paths"]["suspect"], params["mappings"]["suspect"], "Suspect"
            )
            results_df = _match_suspects(results_df, suspect_df, params["ppm"])
        except Exception as e:
            print(f"[WARNING] Suspect matching failed: {e}")

    print(f"--- Analysis Complete. Found {len(results_df)} relationships. ---")
    return results_df


# --- HELPER FUNCTIONS ---


def _load_and_map(filepath, mz_col, label):
    """Reads a CSV and standardizes the m/z column."""
    if not filepath or not mz_col:
        raise ValueError(f"Missing path or mapping for {label}")

    df = pd.read_csv(filepath)

    # 1. Identify the column name from the letter (e.g. "A" -> "Column 0")
    if len(mz_col) == 1 and mz_col.isalpha():
        col_idx = ord(mz_col.upper()) - 65  # 'A' is 65
        if col_idx >= len(df.columns):
            raise ValueError(f"Column {mz_col} out of range for {label}")
        target_col = df.columns[col_idx]
    else:
        # Assume it's a header name
        if mz_col not in df.columns:
            raise ValueError(f"Column '{mz_col}' not found in {label}")
        target_col = mz_col

    # 2. Rename to standardized 'm/z'
    df = df.rename(columns={target_col: "m/z"})

    # 3. Ensure numeric
    df["m/z"] = pd.to_numeric(df["m/z"], errors="coerce")
    df = df.dropna(subset=["m/z"])

    return df


def _remove_excluded_features(exp_df, excl_df, ppm):
    """Removes rows from exp_df that match any mass in excl_df."""
    # This is a brute-force filter. For huge files, a KDTree is faster,
    # but this is safer for general compatibility.

    keep_indices = []
    excl_masses = excl_df["m/z"].values

    for idx, row in exp_df.iterrows():
        mass = row["m/z"]
        tol = mass * (ppm / 1e6)

        # Check if this mass exists in exclusion list
        # (True if ANY exclusion mass is within tolerance)
        is_excluded = np.any(np.abs(excl_masses - mass) <= tol)

        if not is_excluded:
            keep_indices.append(idx)

    return exp_df.loc[keep_indices].reset_index(drop=True)


def _match_suspects(results_df, suspect_df, ppm):
    """Annotates the results DataFrame with Suspect Library matches."""
    results_df["Suspect Match"] = None  # Default column

    suspect_masses = suspect_df["m/z"].values
    # Try to find a Name column, otherwise use "Unknown"
    name_col = next((c for c in suspect_df.columns if "name" in c.lower()), None)
    suspect_names = (
        suspect_df[name_col].values if name_col else ["Unknown"] * len(suspect_df)
    )

    for idx, row in results_df.iterrows():
        product_mass = row["Product m/z"]
        tol = product_mass * (ppm / 1e6)

        # Find matches
        match_indices = np.where(np.abs(suspect_masses - product_mass) <= tol)[0]

        if len(match_indices) > 0:
            # Join all matching names (e.g., "PFOS; PFOA")
            matches = [str(suspect_names[i]) for i in match_indices]
            results_df.at[idx, "Suspect Match"] = "; ".join(matches)

    return results_df
