import pandas as pd

# Make sure this file is in the same directory
from calculating_kendrick_lamar_defect import calculate_KMD


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


def main():
    """Main function to run the analysis and print results."""
    try:
        adjusted_df = pd.read_csv("PIMMS v1.2/data/stacked_output.csv")
        df_with_kmds = calculate_KMD(adjusted_df)
        df_with_series = find_kmd_series(df_with_kmds, mass_error_ppm=10)

        # --- UPDATED: Step 3 - Filter and Print VALID Series with New Rule ---
        print("\n" + "=" * 60)
        print(
            "DISPLAYING VALID SERIES (POINTS > 1 AND AT LEAST ONE PAIR IS >= 10 m/z APART)"
        )
        print("=" * 60 + "\n")

        series_columns = [
            col for col in df_with_series.columns if col.startswith("Series")
        ]

        for series_col in series_columns:
            kmd_col = series_col.replace("Series", "KMD")

            # Group by the series ID to analyze each group
            grouped = df_with_series.groupby(series_col)

            # For each group, calculate its size and total m/z span (max - min)
            series_stats = grouped.agg(
                point_count=("m/z", "size"),
                mz_span=(
                    "m/z",
                    lambda x: x.max() - x.min(),
                ),  # The span from min to max m/z
            )

            # A valid series must have at least 2 points AND a span of at least 10 m/z.
            # The mz_span check efficiently confirms your rule: if the total span is >= 10,
            # then at least two points (the min and max) are >= 10 units apart.
            valid_series = series_stats[
                (series_stats["point_count"] > 1) & (series_stats["mz_span"] >= 10)
            ]

            valid_series_ids = valid_series.index

            if len(valid_series_ids) > 0:
                # Filter the main DataFrame to get only the rows from valid series
                series_rows = df_with_series[
                    df_with_series[series_col].isin(valid_series_ids)
                ]
                sorted_series_rows = series_rows.sort_values(by=[series_col, "m/z"])

                print(f"--- Valid series found in '{series_col}' ---")
                print(sorted_series_rows[["m/z", "CCS", kmd_col, series_col]])
                print("\n")
            else:
                print(f"--- No valid series found for '{series_col}' ---\n")

    except FileNotFoundError:
        print(
            "[ERROR] Could not find the input file: 'PIMMS v1.2/data/stacked_output.csv'"
        )
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
