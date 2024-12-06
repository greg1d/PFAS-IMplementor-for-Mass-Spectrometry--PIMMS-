import pandas as pd
import pyarrow.feather as feather
import os

# Global variable to store the temporary directory path
TEMP_DIR = None


def convert_files(dropped_files):
    global TEMP_DIR
    print("Convert files functionality goes here.")

    # Create a temporary directory in the parent directory of the project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(project_dir)
    TEMP_DIR = os.path.join(parent_dir, ".temp")
    os.makedirs(TEMP_DIR, exist_ok=True)
    print(f"Temporary directory created at: {TEMP_DIR}")

    for cef_file in dropped_files:
        # Read the CEF file into a DataFrame (replace this with actual CEF reading logic)
        df = pd.read_csv(
            cef_file
        )  # Assuming CEF files can be read as CSV for this example

        # Convert the DataFrame to a Feather file
        feather_file = os.path.join(
            TEMP_DIR, os.path.basename(cef_file).replace(".cef", ".feather")
        )
        feather.write_feather(df, feather_file)

        print(f"Converted {cef_file} to {feather_file}")


def cleanup_temp_dir():
    global TEMP_DIR
    if TEMP_DIR and os.path.exists(TEMP_DIR):
        print(f"Cleaning up temporary directory: {TEMP_DIR}")
        for root, dirs, files in os.walk(TEMP_DIR, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(TEMP_DIR)
        print("Temporary directory cleaned up")


# Example usage
if __name__ == "__main__":
    convert_files(["path/to/your/cef_file1.cef", "path/to/your/cef_file2.cef"])
    cleanup_temp_dir()
