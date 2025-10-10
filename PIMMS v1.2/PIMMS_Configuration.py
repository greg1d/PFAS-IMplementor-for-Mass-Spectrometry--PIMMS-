import json


class Config:
    """
    A centralized configuration class to hold all parameters for the PIMMS workflow.
    This object is populated by the GUI and passed to the workflow function.
    """

    def __init__(self):
        # --- File and Directory Paths ---
        self.raw_data_input_location = (
            "PIMMS v1.2\data\Dummy test blank subtracted data.csv"
        )
        self.standards_file = "PIMMS v1.2\import folder\MPFAC HIF ES SIL peaks.csv"
        self.output_path = "PIMMS v1.2\import folder\Dummy test output.csv"
        self.level_2_library = "PIMMS v1.2\import folder\Baker_Group_RPLC_DTIMS_MS_PFAS_Library_Negative.csv"
        self.level_5_library = r"PIMMS v1.2\import folder\NORMAN_PFAS_Negative_ESI.csv"
        self.experimental_filepath = "PIMMS v1.2\\data\\250918_SealsPIMMS.csv"
        self.library_filepath = "PIMMS v1.2\\import folder\\Baker_Group_RPLC_DTIMS_MS_PFAS_Library_Negative.csv"

        # --- Column Mappings ---
        self.metadata_mapping = {
            "ID": "A",
            "RT": "B",
            "DT": "C",
            "CCS": "D",
            "m/z": "E",
        }
        self.control_start_col = "I"
        self.control_end_col = "K"
        self.experimental_start_col = "F"
        self.experimental_end_col = "H"
        self.level_2_library_mapping = {
            "Name": "B",
            "Adduct": "D",
            "CCS": "E",
            "RT": "F",
            "m/z": "G",
        }
        self.level_5_library_mapping = {"Name": "B", "m/z": "AD"}
        self.standards_library_mapping = {
            "m/z": "C",
            "CCS": "B",
        }
        # --- Workflow Parameters ---
        self.blank_subtraction_method = "2"  # Default to method 2

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
        self.repeating_units = {}  # Initialize as empty dictionary
        self.load_from_json()

        self.experimental_mapping = {
            "Name": "A",
            "m/z": "H",
            "CCS": "G",
            "RT": "E",
            "ID": "D",
        }

        self.library_mapping = {
            "Name": "B",
            "m/z": "G",
            "CCS": "E",
            "RT": "",  # Optional, leave blank if not applicable
            "ID": "",  # Optional, leave blank if not applicable
        }

    def load_from_json(self, filepath="PIMMS v1.2\GUI\widgets\config.json"):
        """Loads configuration settings from a JSON file."""
        try:
            with open(filepath, "r") as f:
                config_data = json.load(f)
                # Load the repeating units into the config object
                self.repeating_units = config_data.get("repeating_units", {})
                print(
                    f"[INFO] Loaded {len(self.repeating_units)} repeating units from {filepath}."
                )
        except FileNotFoundError:
            print(
                f"[WARNING] Configuration file '{filepath}' not found. Using default values."
            )
            # Define a default in case the file is missing
            self.repeating_units = {"CF2": 49.9968}
        except Exception as e:
            print(f"[ERROR] Failed to load config file: {e}")
