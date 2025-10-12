import json
import os

# Assuming you have created 'utils.py' in your 'GUI' folder.
# This import path works if this Config file is in the project root.
try:
    from GUI.utils import resource_path
except ImportError:
    # Fallback for different execution contexts
    print(
        "[WARNING] Could not import 'resource_path' helper. Default paths may not work in a packaged app."
    )
    # Define a dummy function so the app doesn't crash if the import fails
    resource_path = lambda x: x


class Config:
    """
    A centralized configuration class to hold all parameters for the PIMMS workflow.
    This object is populated by the GUI and passed to the workflow function.
    """

    def __init__(self):
        # --- File and Directory Paths (CORRECTED) ---
        # All paths for bundled data files have had the "PIMMS v1.2/" prefix removed.
        # The resource_path() function handles finding the correct base directory.

        self.raw_data_input_location = resource_path("")
        self.standards_file = resource_path(
            "Import libraries/Mass Labeled PFAS Standards (MPFAC HIF ES SIL).csv"
        )
        self.level_2_library = resource_path(
            "Import libraries/Level 2 Library Baker_Group_RPLC_DTIMS_MS_PFAS_Library_Negative.csv"
        )
        self.level_5_library = resource_path(
            "Import libraries/Level 5 Library NORMAN_PFAS_Negative_ESI.csv"
        )
        self.experimental_filepath = resource_path("")
        self.library_filepath = resource_path(
            "Import libraries/Baker_Group_RPLC_DTIMS_MS_PFAS_Library_Negative.csv"
        )

        self.output_path = resource_path("")

        # --- (The rest of the __init__ method is unchanged) ---
        # --- Column Mappings ---
        self.metadata_mapping = {
            "ID": "A",
            "RT": "B",
            "DT": "C",
            "CCS": "D",
            "m/z": "E",
        }
        self.control_start_col = ""
        self.control_end_col = ""
        self.experimental_start_col = ""
        self.experimental_end_col = ""
        self.level_2_library_mapping = {
            "Name": "B",
            "Adduct": "D",
            "CCS": "E",
            "RT": "F",
            "m/z": "G",
        }
        self.level_5_library_mapping = {"Name": "B", "m/z": "AD"}
        self.standards_library_mapping = {"m/z": "C", "CCS": "B"}
        # --- Workflow Parameters ---
        self.blank_subtraction_method = "2"
        # --- Tolerances ---
        self.mass_error_ppm = 15.0
        self.ccs_tolerance = 2.0
        self.rt_tolerance = 0.5
        self.include_rt_scoring = False
        # --- Filter Settings ---
        self.min_intensity = 100
        self.rt_min = 2.0
        self.rt_max = 16.0
        self.mz_min = 100.0
        self.mz_max = 2000.0
        self.mass_defect_lower = -0.194
        self.mass_defect_upper = 0.090
        self.frequency_threshold = 15.0
        self.rt_regression_filter = False
        self.ccs_regression_filter = True
        self.repeating_units = {}

        self.load_from_json()

        self.experimental_mapping = {
            "Name": "A",
            "m/z": "H",
            "CCS": "G",
            "RT": "E",
            "ID": "D",
        }
        self.library_mapping = {"Name": "B", "m/z": "G", "CCS": "E", "RT": "", "ID": ""}

    def load_from_json(self, filepath=None):
        """
        Loads configuration settings from a JSON file.
        The path is now resolved using the resource_path helper correctly.
        """
        if filepath is None:
            filepath = resource_path("modules/config.json")

        try:
            with open(filepath, "r") as f:
                config_data = json.load(f)
                self.repeating_units = config_data.get("repeating_units", {})
                print(
                    f"[INFO] Loaded {len(self.repeating_units)} repeating units from {os.path.basename(filepath)}."
                )
        except FileNotFoundError:
            print(
                f"[WARNING] Configuration file '{os.path.basename(filepath)}' not found. Using default values."
            )
            self.repeating_units = {"CF2": 49.9968}
        except Exception as e:
            print(f"[ERROR] Failed to load config file: {e}")
