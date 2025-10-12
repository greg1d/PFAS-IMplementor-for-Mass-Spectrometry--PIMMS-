import pandas as pd

# Make sure this file is in the same directory


def find_kmd_series(df, mass_error_ppm):
    """
    Efficiently identifies potential homologous series within multiple KMD columns.
    (This function is unchanged)
    """
    start_time = pd.Timestamp.now()
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df

    if "m/z" not in df.columns:
        return df

    df_out = df.copy()

    kmd_columns = [col for col in df.columns if col.startswith("KMD")]
    if not kmd_columns:
        return df

    print(f"[INFO] Finding KMD series for {len(kmd_columns)} KMD types...")

    for kmd_col in kmd_columns:
        series_col_name = kmd_col.replace("KMD", "Series")
        df_sorted = df_out.sort_values(by=kmd_col)

        prev_mz = df_sorted["m/z"].shift(1)
        prev_kmd = df_sorted[kmd_col].shift(1)

        kmd_difference = (df_sorted[kmd_col] - prev_kmd).abs()
        error_margin = (df_sorted["m/z"] + prev_mz) * 10 / 1000000
        is_new_series = kmd_difference < error_margin
        is_new_series.iloc[0] = True
        series_ids = is_new_series.cumsum()

        df_out[series_col_name] = series_ids.reindex(df_out.index)

        print(f"  - Found {series_ids.max()} potential series for {series_col_name}.")

    end_time = pd.Timestamp.now()
    elapsed_time = (end_time - start_time).total_seconds()
    print(f"[INFO] KMD series identification completed in {elapsed_time:.2f} seconds.")
    return df_out
