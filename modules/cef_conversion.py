import pandas as pd
import pyarrow.feather as feather
import os
import xml.etree.ElementTree as ET
import time

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

    all_features_data = []

    start_time = time.time()  # Record the start time

    for cef_file in dropped_files:
        # Extract the sample name from the file name
        sample_name = os.path.basename(cef_file).replace(".cef", "")

        # Parse the CEF file
        tree = ET.parse(cef_file)
        root = tree.getroot()

        # Extract <Compound> data
        for compound in root.findall(".//Compound"):
            mppid = compound.get("mppid")

            # Extract <Location> data
            location_data = compound.find(".//Location")
            rt = location_data.get("rt")
            dt = location_data.get("dt")
            ccs = location_data.get("ccs")

            # Extract <MSPeaks> data
            ms_peaks_data = []
            for mspeaks in compound.findall(".//MSPeaks/p"):
                x = mspeaks.get("x")
                y = mspeaks.get("y")
                z = mspeaks.get("z")
                s = mspeaks.get("s")
                ms_peaks_data.append(
                    {
                        "Sample Feature ID": mppid,
                        "m/z": x,
                        "Adduct": s,
                        "Retention Time": rt,
                        "Drift Time": dt,
                        "CCS": ccs,
                        "Charge": z,
                        "Intensity": y,
                        "Sample Name": sample_name,
                    }
                )

            all_features_data.extend(ms_peaks_data)

    # Convert the data to a DataFrame with the specified column order
    df = pd.DataFrame(
        all_features_data,
        columns=[
            "Sample Feature ID",
            "m/z",
            "Adduct",
            "Retention Time",
            "Drift Time",
            "CCS",
            "Charge",
            "Intensity",
            "Sample Name",
        ],
    )

    # Convert the DataFrame to a Feather file
    feather_file = os.path.join(TEMP_DIR, "features.feather")
    feather.write_feather(df, feather_file)

    end_time = time.time()  # Record the end time
    conversion_time = end_time - start_time  # Calculate the conversion time

    print(f"Converted CEF files to {feather_file} in {conversion_time:.2f} seconds")

    # View the Feather file
    view_feather_file(feather_file)


def view_feather_file(feather_file):
    # Read the Feather file into a DataFrame
    df = pd.read_feather(feather_file)

    # Display the DataFrame
    print(f"Contents of {feather_file}:")
    print(df)


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
