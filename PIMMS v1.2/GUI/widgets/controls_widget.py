import tkinter as tk
from tkinter import messagebox, ttk


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
        """Creates and arranges all the widgets inside the labelframe."""
        self.columnconfigure(0, weight=1)  # File selection area will expand
        self.columnconfigure(1, weight=0)  # Parameters area is fixed size
        self.columnconfigure(2, weight=0)  # Run button is fixed size

        # --- Column 0: File Loading ---
        file_frame = ttk.Labelframe(self, text="Input Files")
        file_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        ttk.Button(
            file_frame, text="Load Experimental File...", command=self.load_exp_callback
        ).grid(row=0, column=0, sticky="w", pady=(5, 2), padx=5)
        self.exp_file_label = ttk.Label(
            file_frame, text="No file loaded.", width=40, anchor="w"
        )
        self.exp_file_label.grid(row=0, column=1, sticky="w", padx=5, pady=(5, 2))
        ttk.Button(
            file_frame, text="Load Library File...", command=self.load_lib_callback
        ).grid(row=1, column=0, sticky="w", pady=(2, 5), padx=5)
        self.lib_file_label = ttk.Label(
            file_frame, text="No file loaded.", width=40, anchor="w"
        )
        self.lib_file_label.grid(row=1, column=1, sticky="w", padx=5, pady=(2, 5))

        # --- Column 1: Analysis Parameters ---
        params_frame = ttk.Labelframe(self, text="Analysis Parameters")
        params_frame.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="ns")

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

        # PPM Error
        ttk.Label(params_frame, text="PPM Error:").grid(
            row=1, column=0, sticky="w", padx=5, pady=2
        )
        self.ppm_error_var = tk.IntVar(value=10)
        ttk.Spinbox(
            params_frame, from_=1, to=100, textvariable=self.ppm_error_var, width=5
        ).grid(row=1, column=1, sticky="w", padx=5, pady=2)

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

        # Min Library Points
        ttk.Label(params_frame, text="Min. Library Points:").grid(
            row=3, column=0, sticky="w", padx=5, pady=2
        )
        self.min_lib_points_var = tk.IntVar(value=0)
        ttk.Spinbox(
            params_frame, from_=0, to=100, textvariable=self.min_lib_points_var, width=5
        ).grid(row=3, column=1, sticky="w", padx=5, pady=2)

        # RANSAC Threshold
        ttk.Label(params_frame, text="RANSAC Threshold (%):").grid(
            row=4, column=0, sticky="w", padx=5, pady=2
        )
        self.ransac_thresh_var = tk.DoubleVar(value=2.0)
        ttk.Spinbox(
            params_frame,
            from_=0.1,
            to=10.0,
            increment=0.1,
            textvariable=self.ransac_thresh_var,
            width=5,
        ).grid(row=4, column=1, sticky="w", padx=5, pady=2)

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
                "ransac_threshold_percentage": self.ransac_thresh_var.get()
                / 100.0,  # Convert % to decimal
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
