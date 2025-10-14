import tkinter as tk
from tkinter import messagebox, ttk

# Make sure the Tooltip class is in the same 'widgets' folder
try:
    from .tooltip import Tooltip
except ImportError:
    # Fallback if Tooltip is in a different relative path
    from tooltip import Tooltip


class ControlsWidget(ttk.Labelframe):
    """A self-contained widget for all user input controls for the analysis pipeline."""

    def __init__(
        self, parent, config, load_exp_callback, load_lib_callback, analyze_callback
    ):
        super().__init__(parent, text="Workflow Controls")

        self.config = config
        self.load_exp_callback = load_exp_callback
        self.load_lib_callback = load_lib_callback
        self.analyze_callback = analyze_callback

        self._create_widgets()

    def _create_widgets(self):
        """Creates and arranges all the widgets with their tooltips."""

        # --- Define all help texts for this widget ---
        help_texts = {
            "load_exp": "Load the main experimental data file containing all detected features.",
            "load_lib": "Load the library file used for matching and annotation.",
            "col_pos": "Specify the column letter (A, B, C...) for the required data.",
            "repeating_unit": "Select the chemical moiety (e.g., CF2) to search for when identifying homologous series.",
            "ppm_error": "The mass tolerance in parts-per-million (ppm) used to find the next member of a homologous series.",
            "min_series_points": "A homologous series must contain at least this many well-spaced points to be considered valid.",
            "min_lib_points": "A refined homologous series must contain at least this many points originating from a library (e.g., 'External Standard').",
            "trend_ccs_thresh": "The maximum allowed error for a point to be included in a trend, as a percentage of the average CCS.",
        }

        # --- Layout Configuration ---
        self.columnconfigure(0, weight=1)  # File selection area will expand
        self.columnconfigure(1, weight=0)  # Parameters area is fixed size
        self.columnconfigure(2, weight=0)  # Run button is fixed size

        # --- Column 0: File Loading & Column Mapping ---
        file_frame = ttk.Labelframe(self, text="Input Files & Column Mapping")
        file_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        file_frame.columnconfigure(1, weight=1)

        # Get default column mappings from the config object
        lib_cols = (
            self.config.library_mapping
            if hasattr(self.config, "library_mapping")
            else {}
        )
        exp_cols = (
            self.config.experimental_mapping
            if hasattr(self.config, "experimental_mapping")
            else {}
        )

        # --- Experimental File Widgets ---
        ttk.Button(
            file_frame, text="Load Experimental File...", command=self.load_exp_callback
        ).grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.exp_file_label = ttk.Label(
            file_frame, text="No file loaded.", width=40, anchor="w"
        )
        self.exp_file_label.grid(row=0, column=1, sticky="ew", padx=5)
        help_exp = ttk.Label(file_frame, text=" (?) ", cursor="question_arrow")
        help_exp.grid(row=0, column=2, sticky="w", padx=(0, 5))
        Tooltip(help_exp, text=help_texts["load_exp"])

        # --- NEW: Frame for Experimental Column Selectors ---
        exp_cols_frame = ttk.Frame(file_frame)
        exp_cols_frame.grid(
            row=1, column=0, columnspan=3, sticky="w", padx=15, pady=(0, 5)
        )

        ttk.Label(exp_cols_frame, text="Name:").pack(side=tk.LEFT, padx=(0, 2))
        self.exp_name_pos_entry = ttk.Entry(exp_cols_frame, width=3)
        self.exp_name_pos_entry.insert(0, exp_cols.get("Name", ""))
        self.exp_name_pos_entry.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(exp_cols_frame, text="m/z:").pack(side=tk.LEFT, padx=(0, 2))
        self.exp_mz_pos_entry = ttk.Entry(exp_cols_frame, width=3)
        self.exp_mz_pos_entry.insert(0, exp_cols.get("m/z", ""))
        self.exp_mz_pos_entry.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(exp_cols_frame, text="CCS:").pack(side=tk.LEFT, padx=(0, 2))
        self.exp_ccs_pos_entry = ttk.Entry(exp_cols_frame, width=3)
        self.exp_ccs_pos_entry.insert(0, exp_cols.get("CCS", ""))
        self.exp_ccs_pos_entry.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(exp_cols_frame, text="RT:").pack(side=tk.LEFT, padx=(0, 2))
        self.exp_rt_pos_entry = ttk.Entry(exp_cols_frame, width=3)
        self.exp_rt_pos_entry.insert(0, exp_cols.get("RT", ""))
        self.exp_rt_pos_entry.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(exp_cols_frame, text="ID:").pack(side=tk.LEFT, padx=(0, 2))
        self.exp_id_pos_entry = ttk.Entry(exp_cols_frame, width=3)
        self.exp_id_pos_entry.insert(0, exp_cols.get("ID", ""))
        self.exp_id_pos_entry.pack(side=tk.LEFT, padx=(0, 5))

        help_exp_cols = ttk.Label(exp_cols_frame, text=" (?) ", cursor="question_arrow")
        help_exp_cols.pack(side=tk.LEFT)
        Tooltip(help_exp_cols, text=help_texts["col_pos"])

        # --- Library File Widgets ---
        ttk.Button(
            file_frame, text="Load Library File...", command=self.load_lib_callback
        ).grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.lib_file_label = ttk.Label(
            file_frame, text="No file loaded.", width=40, anchor="w"
        )
        self.lib_file_label.grid(row=2, column=1, sticky="ew", padx=5)
        help_lib = ttk.Label(file_frame, text=" (?) ", cursor="question_arrow")
        help_lib.grid(row=2, column=2, sticky="w", padx=(0, 5))
        Tooltip(help_lib, text=help_texts["load_lib"])

        # --- NEW: Frame for Library Column Selectors ---
        lib_cols_frame = ttk.Frame(file_frame)
        lib_cols_frame.grid(
            row=3, column=0, columnspan=3, sticky="w", padx=15, pady=(0, 5)
        )

        ttk.Label(lib_cols_frame, text="Name:").pack(side=tk.LEFT, padx=(0, 2))
        self.lib_name_pos_entry = ttk.Entry(lib_cols_frame, width=3)
        self.lib_name_pos_entry.insert(0, lib_cols.get("Name", ""))
        self.lib_name_pos_entry.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(lib_cols_frame, text="m/z:").pack(side=tk.LEFT, padx=(0, 2))
        self.lib_mz_pos_entry = ttk.Entry(lib_cols_frame, width=3)
        self.lib_mz_pos_entry.insert(0, lib_cols.get("m/z", ""))
        self.lib_mz_pos_entry.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(lib_cols_frame, text="CCS:").pack(side=tk.LEFT, padx=(0, 2))
        self.lib_ccs_pos_entry = ttk.Entry(lib_cols_frame, width=3)
        self.lib_ccs_pos_entry.insert(0, lib_cols.get("CCS", ""))
        self.lib_ccs_pos_entry.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(lib_cols_frame, text="RT (Opt):").pack(side=tk.LEFT, padx=(0, 2))
        self.lib_rt_pos_entry = ttk.Entry(lib_cols_frame, width=3)
        self.lib_rt_pos_entry.insert(0, lib_cols.get("RT", ""))
        self.lib_rt_pos_entry.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(lib_cols_frame, text="ID (Opt):").pack(side=tk.LEFT, padx=(0, 2))
        self.lib_id_pos_entry = ttk.Entry(lib_cols_frame, width=3)
        self.lib_id_pos_entry.insert(0, lib_cols.get("ID", ""))
        self.lib_id_pos_entry.pack(side=tk.LEFT, padx=(0, 5))

        help_lib_cols = ttk.Label(lib_cols_frame, text=" (?) ", cursor="question_arrow")
        help_lib_cols.pack(side=tk.LEFT)
        Tooltip(help_lib_cols, text=help_texts["col_pos"])

        # --- Column 1: Analysis Parameters ---
        params_frame = ttk.Labelframe(self, text="Analysis Parameters")
        params_frame.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="ns")
        # ... (rest of parameter widgets are unchanged) ...
        # Repeating Unit
        ttk.Label(params_frame, text="Repeating Unit:").grid(
            row=0, column=0, sticky="w", padx=5, pady=2
        )
        self.unit_selector = ttk.Combobox(params_frame, state="readonly", width=12)
        unit_names = list(self.config.repeating_units.keys())
        self.unit_selector["values"] = unit_names
        if unit_names:
            self.unit_selector.current(0)
        self.unit_selector.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        help_unit = ttk.Label(params_frame, text=" (?) ", cursor="question_arrow")
        help_unit.grid(row=0, column=2, sticky="w")
        Tooltip(help_unit, text=help_texts["repeating_unit"])

        # PPM Error
        ttk.Label(params_frame, text="PPM Error:").grid(
            row=1, column=0, sticky="w", padx=5, pady=2
        )
        self.ppm_error_var = tk.IntVar(value=15)
        ttk.Spinbox(
            params_frame, from_=1, to=100, textvariable=self.ppm_error_var, width=5
        ).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        help_ppm = ttk.Label(params_frame, text=" (?) ", cursor="question_arrow")
        help_ppm.grid(row=1, column=2, sticky="w")
        Tooltip(help_ppm, text=help_texts["ppm_error"])

        # Min Series Points
        ttk.Label(params_frame, text="Min. Series Points:").grid(
            row=2, column=0, sticky="w", padx=5, pady=2
        )
        self.min_series_points_var = tk.IntVar(value=3)
        ttk.Spinbox(
            params_frame,
            from_=3,
            to=100,
            textvariable=self.min_series_points_var,
            width=5,
        ).grid(row=2, column=1, sticky="w", padx=5, pady=2)
        help_series = ttk.Label(params_frame, text=" (?) ", cursor="question_arrow")
        help_series.grid(row=2, column=2, sticky="w")
        Tooltip(help_series, text=help_texts["min_series_points"])

        # Min Library Points
        ttk.Label(params_frame, text="Min. Library Points:").grid(
            row=3, column=0, sticky="w", padx=5, pady=2
        )
        self.min_lib_points_var = tk.IntVar(value=0)
        ttk.Spinbox(
            params_frame, from_=0, to=100, textvariable=self.min_lib_points_var, width=5
        ).grid(row=3, column=1, sticky="w", padx=5, pady=2)
        help_lib_pts = ttk.Label(params_frame, text=" (?) ", cursor="question_arrow")
        help_lib_pts.grid(row=3, column=2, sticky="w")
        Tooltip(help_lib_pts, text=help_texts["min_lib_points"])

        # Trend CCS Threshold
        ttk.Label(params_frame, text="Trend CCS Threshold (%):").grid(
            row=4, column=0, sticky="w", padx=5, pady=2
        )
        self.trend_ccs_thresh_var = tk.DoubleVar(value=2.0)
        ttk.Spinbox(
            params_frame,
            from_=0.1,
            to=10.0,
            increment=0.1,
            textvariable=self.trend_ccs_thresh_var,
            width=5,
        ).grid(row=4, column=1, sticky="w", padx=5, pady=2)
        help_ransac = ttk.Label(params_frame, text=" (?) ", cursor="question_arrow")
        help_ransac.grid(row=4, column=2, sticky="w")
        Tooltip(help_ransac, text=help_texts["trend_ccs_thresh"])

        # --- Column 2: Run Button ---
        run_btn = ttk.Button(
            self,
            text="Run Full Analysis",
            command=self.analyze_callback,
            style="Accent.TButton",
        )
        run_btn.grid(row=0, column=2, padx=10, pady=10, sticky="e")

    def get_parameters(self):
        """Retrieves all analysis parameters from the GUI widgets."""
        try:
            params = {
                "repeating_unit": self.get_repeating_units(),
                "mass_error_ppm": self.ppm_error_var.get(),
                "min_valid_points": self.min_series_points_var.get(),
                "min_library_points": self.min_lib_points_var.get(),
                "trend_ccs_threshold_percentage": self.trend_ccs_thresh_var.get()
                / 100.0,
                # --- NEW: Get all column positions ---
                "library_name_col_pos": self.lib_name_pos_entry.get(),
                "library_mz_col_pos": self.lib_mz_pos_entry.get(),
                "library_ccs_col_pos": self.lib_ccs_pos_entry.get(),
                "library_rt_col_pos": self.lib_rt_pos_entry.get(),
                "library_id_col_pos": self.lib_id_pos_entry.get(),
                "exp_name_col_pos": self.exp_name_pos_entry.get(),
                "exp_mz_col_pos": self.exp_mz_pos_entry.get(),
                "exp_ccs_col_pos": self.exp_ccs_pos_entry.get(),
                "exp_rt_col_pos": self.exp_rt_pos_entry.get(),
                "exp_id_col_pos": self.exp_id_pos_entry.get(),
            }
            if params["repeating_unit"] is None:
                return None
            return params
        except (tk.TclError, ValueError) as e:
            messagebox.showerror(
                "Invalid Parameter",
                f"Please enter valid numbers for all parameters.\nError: {e}",
            )
            return None

    def get_repeating_units(self):
        """Gets the selected unit name and returns its {name: mass} dictionary."""
        selected_name = self.unit_selector.get()
        if not selected_name:
            messagebox.showerror("Invalid Selection", "Please select a repeating unit.")
            return None
        mass = self.config.repeating_units.get(selected_name)
        return {selected_name: mass}

    def set_exp_file_label(self, text):
        self.exp_file_label.config(text=text)

    def set_lib_file_label(self, text):
        self.lib_file_label.config(text=text)
