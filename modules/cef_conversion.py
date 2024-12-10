import pandas as pd
import pyarrow.feather as feather
import os
import xml.etree.ElementTree as ET
import time
from concurrent.futures import ThreadPoolExecutor
from line_profiler import LineProfiler
import threading
import sys

# Add the directory containing data_importing.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.data_importing import DragDropListWidget
from PyQt6.QtWidgets import QApplication

# Global variable to store the temporary directory path
TEMP_DIR = None

# Create an Event object
file_processed_event = threading.Event()
all_files_processed_event = threading.Event()


def process_cef_file(cef_file, processing_hub):
    # Extract the sample name from the file name
    sample_name = os.path.basename(cef_file).replace(".cef", "")
    print(f"Processing file: {sample_name}")

    # Parse the CEF file
    tree = ET.parse(cef_file)
    root = tree.getroot()

    all_features_data = []

    # Extract <Compound> data
    compounds = root.findall(".//Compound")
    for i, compound in enumerate(compounds):
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
        processing_hub.update_progress(cef_file, int((i + 1) / len(compounds) * 100))

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

    # Update the progress bar for the file completion
    processing_hub.update_progress(cef_file, 100)

    # Print a statement indicating the file has finished processing
    print(f"Finished processing {sample_name}")

    # Show the check mark
    processing_hub.show_check_mark(cef_file)

    # Signal the event
    print(f"Setting event for: {sample_name}")
    file_processed_event.set()

    return feather_file


def convert_files(dropped_files, processing_hub):
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
                futures.append(
                    executor.submit(process_cef_file, cef_file, processing_hub)
                )
        for future in futures:
            feather_file = future.result()
            feather_files.append(feather_file)
            # Call color_row_green after processing each file
            sample_name = os.path.basename(feather_file).replace(".feather", "")

            print(f"Waiting for event to be set for: {sample_name}")
            event_set = file_processed_event.wait(timeout=0.0001)  # Add a timeout
            if event_set:
                print(f"Event set for: {sample_name}")
            else:
                print(f"Timeout waiting for event for: {sample_name}")
            # Clear the event for the next file
            file_processed_event.clear()
            print(f"Event cleared for: {sample_name}")

    end_time = time.time()  # Record the end time
    conversion_time = end_time - start_time  # Calculate the conversion time
    print("All files finished")
    print(f"Converted all CEF files in {conversion_time:.2f} seconds")

    # Print a message indicating all files have been processed
    all_files_processed_event.set()

    return feather_files


def cleanup_temp_dir(dropped_files):
    global TEMP_DIR
    if TEMP_DIR and os.path.exists(TEMP_DIR):
        for cef_file in dropped_files:
            sample_name = os.path.basename(cef_file).replace(".cef", "")
            feather_file_path = os.path.join(TEMP_DIR, f"{sample_name}.feather")
            if os.path.exists(feather_file_path):
                file_mod_time = os.path.getmtime(cef_file)
                feather_file_mod_time = os.path.getmtime(feather_file_path)

                if file_mod_time > feather_file_mod_time:
                    os.remove(feather_file_path)
        for root, dirs, files in os.walk(TEMP_DIR, topdown=False):
            for name in dirs:
                dir_path = os.path.join(root, name)
                if not os.listdir(dir_path):  # Check if the directory is empty
                    os.rmdir(dir_path)
        if not os.listdir(TEMP_DIR):  # Check if the TEMP_DIR is empty
            os.rmdir(TEMP_DIR)


def profile_conversion(dropped_files, processing_hub):
    profiler = LineProfiler()
    profiler.add_function(process_cef_file)
    profiler.add_function(convert_files)
    profiler.enable_by_count()
    convert_files(dropped_files, processing_hub)


if __name__ == "__main__":
    app = QApplication([])  # Create a QApplication instance
    dropped_files = [
        "F:/PFAS-IMplementor-for-Mass-Spectrometry--PIMMS-/data/Importing work/104 B2 MB-2.d.DeMP.cef",
        "F:/PFAS-IMplementor-for-Mass-Spectrometry--PIMMS-/data/Importing work/103 B2 MB-1.d.DeMP.cef",
        "F:/PFAS-IMplementor-for-Mass-Spectrometry--PIMMS-/data/Importing work/148 B2 16632.d.DeMP.cef",
        "F:/PFAS-IMplementor-for-Mass-Spectrometry--PIMMS-/data/Importing work/261 B4 MB-2.d.DeMP.cef",
    ]
    processing_hub = (
        DragDropListWidget()
    )  # Create the DragDropListWidget instance after QApplication
    profile_conversion(dropped_files, processing_hub)
    cleanup_temp_dir(dropped_files)
    all_files_processed_event.wait()  # Wait for the final event to be set
    app.exec()  # Start the QApplication event loop
