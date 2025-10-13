import json
import os
import shutil

# Import helper functions
try:
    from GUI.utils import get_app_path, resource_path
except ImportError:
    print("[WARNING] Could not import helper functions. Paths may not work correctly.")
    resource_path = lambda x: x
    get_app_path = lambda x: x


class Config:
    """
    Central configuration for PIMMS workflow.
    Automatically sets up a Documents/PIMMS directory structure on first run,
    copies default library files there for user access, and reads from them by default.
    """

    def __init__(self):
        # === Locate User Documents Folder ===
        self.user_documents = os.path.join(os.path.expanduser("~"), "Documents")

        # === Define Folder Structure ===
        self.pimms_root = os.path.join(self.user_documents, "PIMMS")
        self.raw_data_folder = os.path.join(self.pimms_root, "Raw Data")
        self.import_libraries_folder = os.path.join(self.pimms_root, "Import libraries")
        self.output_folder = os.path.join(self.pimms_root, "PIMMS output")
        self.cef_data_folder = os.path.join(self.pimms_root, "CEF_data")  # NEW FOLDER

        # === Create the Folder Structure ===
        os.makedirs(self.raw_data_folder, exist_ok=True)
        os.makedirs(self.import_libraries_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
        os.makedirs(self.cef_data_folder, exist_ok=True)  # CREATE NEW FOLDER

        # === Define Bundled Library Sources ===
        bundled_files = {
            "Mass Labeled PFAS Standards (MPFAC HIF ES SIL).csv": resource_path(
                r"Import libraries\Mass Labeled PFAS Standards (MPFAC HIF ES SIL).csv"
            ),
            "Level 2 Library Baker_Group_RPLC_DTIMS_MS_PFAS_Library_Negative.csv": resource_path(
                r"Import libraries\Level 2 Library Baker_Group_RPLC_DTIMS_MS_PFAS_Library_Negative.csv"
            ),
            "Level 5 Library NORMAN_PFAS_Negative_ESI.csv": resource_path(
                r"Import libraries\Level 5 Library NORMAN_PFAS_Negative_ESI.csv"
            ),
        }

        # === Copy Default Library Files to Documents\PIMMS ===
        for filename, src_path in bundled_files.items():
            dest_path = os.path.join(self.import_libraries_folder, filename)
            try:
                if not os.path.exists(dest_path):
                    shutil.copy2(src_path, dest_path)
                    print(f"[INFO] Copied '{filename}' → {dest_path}")
                else:
                    print(f"[INFO] '{filename}' already exists — using user copy.")
            except Exception as e:
                print(f"[WARNING] Failed to copy {filename}: {e}")

        # === ALWAYS point to the user's copies for imports ===
        self.standards_file = os.path.join(
            self.import_libraries_folder,
            "Mass Labeled PFAS Standards (MPFAC HIF ES SIL).csv",
        )
        self.level_2_library = os.path.join(
            self.import_libraries_folder,
            "Level 2 Library Baker_Group_RPLC_DTIMS_MS_PFAS_Library_Negative.csv",
        )
        self.level_5_library = os.path.join(
            self.import_libraries_folder, "Level 5 Library NORMAN_PFAS_Negative_ESI.csv"
        )
        self.library_filepath = self.level_2_library  # Default import target

        # === Input / Output Paths ===
        self.raw_data_input_location = self.raw_data_folder
        self.experimental_filepath = os.path.join(
            self.raw_data_folder, "Experimental Data.csv"
        )
        self.output_path = os.path.join(self.output_folder, "PIMMS_output.csv")

        # === Column Mappings ===
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

        # === Workflow Parameters ===
        self.blank_subtraction_method = "2"

        # === Tolerances ===
        self.mass_error_ppm = 15.0
        self.ccs_tolerance = 2.0
        self.rt_tolerance = 0.5
        self.include_rt_scoring = False

        # === Filter Settings ===
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

        # Load repeating units from JSON config if present
        self.load_from_json()

        # === Experimental & Library Mapping ===
        self.experimental_mapping = {
            "Name": "A",
            "m/z": "H",
            "CCS": "G",
            "RT": "E",
            "ID": "D",
        }
        self.library_mapping = {"Name": "B", "m/z": "G", "CCS": "E", "RT": "", "ID": ""}

    def load_from_json(self, filepath=None):
        """Load repeating units from config.json."""
        if filepath is None:
            filepath = resource_path(r"modules\config.json")

        try:
            with open(filepath, "r") as f:
                config_data = json.load(f)
                self.repeating_units = config_data.get("repeating_units", {})
                print(
                    f"[INFO] Loaded {len(self.repeating_units)} repeating units from {os.path.basename(filepath)}."
                )
        except FileNotFoundError:
            print(
                f"[WARNING] Configuration file '{os.path.basename(filepath)}' not found. Using default repeating units."
            )
            self.repeating_units = {"CF2": 49.9968}
        except Exception as e:
            print(f"[ERROR] Failed to load config file: {e}")
