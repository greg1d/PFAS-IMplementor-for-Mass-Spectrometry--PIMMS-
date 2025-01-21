import pandas as pd


def process_file(file_path):
    """
    Reads a .feather file and converts it to a NumPy array.
    """
    print(f"Processing file: {file_path}")
    try:
        df = pd.read_feather(file_path)
        print(df.head())  # Print the first few rows for debugging
        data_array = df.to_numpy()  # Convert DataFrame to NumPy array
        return data_array
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None


def align_peaks(data_arrays):
    """
    Executes the peak alignment algorithm on a list of data arrays.
    """
    print(data_arrays)
    if not data_arrays:
        print("No data arrays provided for alignment.")
        return

    print("Starting peak alignment algorithm...")
    for idx, data_array in enumerate(data_arrays):
        print(f"Processing data array {idx + 1}/{len(data_arrays)}")
        # Extract the m/z column (column number 2)
        mz_column = data_array[:, 1]
        print(len(mz_column))
        print(f"m/z column for data array {idx + 1}: {mz_column}")
        # Example: Replace with your actual alignment logic
        print(f"Data array shape: {data_array.shape}")

    print("Peak alignment completed successfully.")
