class Config:
    """
    A centralized configuration class to hold all parameters for the PIMMS workflow.
    This object is populated by the GUI and passed to the workflow function.
    """

    def __init__(self):
        # --- File and Directory Paths ---
        self.raw_data_input_location = ""
        self.standards_file = ""
        self.output_path = ""
        self.level_2_library = ""
        self.level_5_library = ""

        # --- Column Mappings ---
        self.metadata_mapping = {
            "ID": "A",
            "RT": "B",
            "DT": "C",
            "CCS": "D",
            "m/z": "E",
        }
        self.control_start_col = "AY"
        self.control_end_col = "BG"
        self.experimental_start_col = "F"
        self.experimental_end_col = "AX"
        self.level_2_library_mapping = {
            "name": "B",
            "adduct": "D",
            "ccs": "E",
            "rt": "F",
            "mz": "G",
        }
        self.level_5_library_mapping = {"name": "A", "mz": "D"}

        # --- Workflow Parameters ---
        self.blank_subtraction_method = "1"  # Default to method 1

        # --- Tolerances ---
        self.mass_error_ppm = 15.0
        self.ccs_tolerance = 2.0
        self.rt_tolerance = 0.5
        self.include_rt_scoring = False

        # --- Filter Settings ---
        self.min_intensity = 10.0
        self.rt_min = 2.0
        self.rt_max = 16.0
        self.mass_min = 68.98
        self.mass_max = 1700.0
        self.mass_defect_lower = -0.11
        self.mass_defect_upper = 0.12
        self.frequency_threshold = 15.0
        self.rt_regression_filter = False
        self.ccs_regression_filter = True
