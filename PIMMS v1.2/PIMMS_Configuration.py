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
    Sets up Documents\PIMMS folder structure on first run,
    copies default library .csv files and bundled .cef files into user-accessible locations,
    and points config attributes to the user's copies by default.
    """

    def __init__(self):
        # === Locate User Documents Folder ===
        self.user_documents = os.path.join(os.path.expanduser("~"), "Documents")

        # === Define Folder Structure ===
        self.pimms_root = os.path.join(self.user_documents, "PIMMS")
        self.raw_data_folder = os.path.join(self.pimms_root, "Raw Data")
        self.import_libraries_folder = os.path.join(self.pimms_root, "Import libraries")
        self.output_folder = os.path.join(self.pimms_root, "PIMMS output")
        self.cef_data_folder = os.path.join(self.pimms_root, "CEF_data")
        self.training_cef_folder = os.path.join(
            self.cef_data_folder, "Training CEF data"
        )

        # === Create the Folder Structure ===
        os.makedirs(self.raw_data_folder, exist_ok=True)
        os.makedirs(self.import_libraries_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
        os.makedirs(self.cef_data_folder, exist_ok=True)
        os.makedirs(self.training_cef_folder, exist_ok=True)

        # === Copy default library CSV files to Import libraries ===
        bundled_files = {
            "Mass Labeled PFAS Standards (MPFAC HIF ES SIL).csv": resource_path(
                r"Import libraries\Mass Labeled PFAS Standards (MPFAC HIF ES SIL).csv"
            ),
            "Level 1 Library Baker_Group_RPLC_DTIMS_MS_PFAS_Library_Negative.csv": resource_path(
                r"Import libraries\Level 1 Library Baker_Group_RPLC_DTIMS_MS_PFAS_Library_Negative.csv"
            ),
            "M-H Level 5 Library.csv": resource_path(
                r"Import libraries\M-H Level 5 Library.csv"
            ),
        }

        for filename, src_path in bundled_files.items():
            dest_path = os.path.join(self.import_libraries_folder, filename)
            try:
                if not os.path.exists(dest_path):
                    if os.path.exists(src_path):
                        shutil.copy2(src_path, dest_path)
                        print(f"[INFO] Copied '{filename}' → {dest_path}")
                    else:
                        print(
                            f"[WARNING] Bundled file missing: {src_path} (could not copy {filename})."
                        )
                else:
                    print(f"[INFO] '{filename}' already exists — using user copy.")
            except Exception as e:
                print(f"[WARNING] Failed to copy {filename}: {e}")

        # === Copy .CEF files to Training CEF data folder ===
        try:
            bundled_cef_dir = resource_path(r"CEF_reading")
        except Exception:
            bundled_cef_dir = None

        if (
            bundled_cef_dir
            and os.path.exists(bundled_cef_dir)
            and os.path.isdir(bundled_cef_dir)
        ):
            for fname in os.listdir(bundled_cef_dir):
                if fname.lower().endswith(".cef"):
                    src = os.path.join(bundled_cef_dir, fname)
                    dest = os.path.join(self.training_cef_folder, fname)
                    try:
                        if os.path.isfile(src) and not os.path.exists(dest):
                            shutil.copy2(src, dest)
                            print(f"[INFO] Copied CEF: '{fname}' → {dest}")
                        elif os.path.exists(dest):
                            print(
                                f"[INFO] CEF already present: '{fname}' — not overwritten."
                            )
                    except Exception as e:
                        print(f"[WARNING] Could not copy CEF file '{fname}': {e}")
        else:
            print(
                f"[INFO] No bundled CEF_reading directory found at: {bundled_cef_dir}"
            )

        # === Copy NIST SRM raw data to Raw Data folder ===
        try:
            nist_src = resource_path(r"Raw data\Training data set raw feature list.csv")
            nist_dest = os.path.join(
                self.raw_data_folder, "Training raw data set raw feature list.csv"
            )
            if os.path.exists(nist_src) and not os.path.exists(nist_dest):
                shutil.copy2(nist_src, nist_dest)
                print(f"[INFO] Copied Training data set raw feature list → {nist_dest}")
            else:
                print(
                    f"[INFO] Training data set raw feature list already exists or source missing → {nist_dest}"
                )
        except Exception as e:
            print(f"[WARNING] Could not copy Training data set raw feature list: {e}")

        # === ALWAYS point to the user's copies for imports ===
        self.standards_file = os.path.join(
            self.import_libraries_folder,
            "Mass Labeled PFAS Standards (MPFAC HIF ES SIL).csv",
        )
        self.level_2_library = os.path.join(
            self.import_libraries_folder,
            "Level 1 Library Baker_Group_RPLC_DTIMS_MS_PFAS_Library_Negative.csv",
        )
        self.level_5_library = os.path.join(
            self.import_libraries_folder, "M-H Level 5 Library.csv"
        )
        self.library_filepath = self.level_2_library  # Default import target

        # === Input / Output Paths (empty by default) ===
        self.raw_data_input_location = ""
        self.experimental_filepath = ""
        self.output_path = ""

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
        self.level_5_library_mapping = {"Name": "A", "m/z": "E"}
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
        self.rt_min = 0.5
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
