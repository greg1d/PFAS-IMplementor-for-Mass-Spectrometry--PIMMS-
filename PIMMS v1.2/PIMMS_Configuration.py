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
        self.level_5_library = "PIMMS v1.2\import folder\Kauffman_M-H_external_PFAS_library_mz_only test.csv"

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
            "Name": "B",
            "Adduct": "D",
            "CCS": "E",
            "RT": "F",
            "m/z": "G",
        }
        self.level_5_library_mapping = {"Name": "A", "m/z": "D"}
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
