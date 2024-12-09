import pandas as pd
import pyarrow.feather as feather
import os
import xml.etree.ElementTree as ET
import time
from concurrent.futures import ThreadPoolExecutor
from line_profiler import LineProfiler
from datetime import datetime

# Global variable to store the temporary directory path
TEMP_DIR = None


def process_cef_file(cef_file):
    # Extract the sample name from the file name
    sample_name = os.path.basename(cef_file).replace(".cef", "")

    # Parse the CEF file
    tree = ET.parse(cef_file)
    root = tree.getroot()

    all_features_data = []

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
    feather_file = os.path.join(TEMP_DIR, f"{sample_name}.feather")
    feather.write_feather(df, feather_file)

    return feather_file


def convert_files(dropped_files):
    global TEMP_DIR

    # Perform cleanup first
    cleanup_temp_dir(dropped_files)

    # Create a temporary directory in the parent directory of the project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(project_dir)
    TEMP_DIR = os.path.join(parent_dir, ".temp")
    os.makedirs(TEMP_DIR, exist_ok=True)

    start_time = time.time()  # Record the start time

    feather_files = []
    with ThreadPoolExecutor() as executor:
        futures = []
        for cef_file in dropped_files:
            sample_name = os.path.basename(cef_file).replace(".cef", "")
            feather_file_path = os.path.join(TEMP_DIR, f"{sample_name}.feather")
            if not os.path.exists(feather_file_path):
                futures.append(executor.submit(process_cef_file, cef_file))
        for future in futures:
            feather_file = future.result()
            feather_files.append(feather_file)

    end_time = time.time()  # Record the end time
    conversion_time = end_time - start_time  # Calculate the conversion time

    print(f"Converted all CEF files in {conversion_time:.2f} seconds")

    return feather_files


def cleanup_temp_dir(dropped_files):
    global TEMP_DIR
    print("Starting cleanup_temp_dir function")
    if TEMP_DIR and os.path.exists(TEMP_DIR):
        print(f"Cleaning up temporary directory: {TEMP_DIR}")
        for cef_file in dropped_files:
            sample_name = os.path.basename(cef_file).replace(".cef", "")
            feather_file_path = os.path.join(TEMP_DIR, f"{sample_name}.feather")
            print(f"Checking file: {cef_file}")
            if os.path.exists(feather_file_path):
                file_mod_time = os.path.getmtime(cef_file)
                feather_file_mod_time = os.path.getmtime(feather_file_path)
                file_mod_time_str = datetime.fromtimestamp(file_mod_time).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                feather_file_mod_time_str = datetime.fromtimestamp(
                    feather_file_mod_time
                ).strftime("%Y-%m-%d %H:%M:%S")
                print(
                    f"File mod time: {file_mod_time_str}, Feather mod time: {feather_file_mod_time_str}"
                )
                if file_mod_time > feather_file_mod_time:
                    print(f"Removing file: {feather_file_path}")
                    os.remove(feather_file_path)
        for root, dirs, files in os.walk(TEMP_DIR, topdown=False):
            for name in dirs:
                dir_path = os.path.join(root, name)
                if not os.listdir(dir_path):  # Check if the directory is empty
                    print(f"Removing empty directory: {dir_path}")
                    os.rmdir(dir_path)
        if not os.listdir(TEMP_DIR):  # Check if the TEMP_DIR is empty
            print(f"Removing empty TEMP_DIR: {TEMP_DIR}")
            os.rmdir(TEMP_DIR)
        print("Temporary directory cleaned up")
    else:
        print("TEMP_DIR does not exist or is not set")


def profile_conversion(dropped_files):
    profiler = LineProfiler()
    profiler.add_function(process_cef_file)
    profiler.add_function(convert_files)
    profiler.enable_by_count()
    convert_files(dropped_files)
    profiler.print_stats()
