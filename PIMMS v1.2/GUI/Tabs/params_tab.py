# gui/tabs/params_tab.py

import tkinter as tk
from tkinter import ttk


class ParamsTab(ttk.Frame):
    def __init__(self, parent, config, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.config = config
        self.param_entries = {}
        self._create_widgets()

    def _create_widgets(self):
        """Creates all widgets for the parameters tab."""
        # --- Tolerances and Filters Frame ---
        params_frame = ttk.LabelFrame(
            self, text="Tolerances and Filters", padding=(10, 5)
        )
        params_frame.pack(fill="x", padx=10, pady=5)
        params = {
            "Mass Error (ppm)": "mass_error_ppm",
            "CCS Tolerance (%)": "ccs_tolerance",
            "RT Tolerance": "rt_tolerance",
            "Min Intensity": "min_intensity",
            "Min RT": "rt_min",
            "Max RT": "rt_max",
        }
        for i, (text, key) in enumerate(params.items()):
            ttk.Label(params_frame, text=text + ":").grid(
                row=i, column=0, padx=5, pady=2, sticky="w"
            )
            entry = ttk.Entry(params_frame)
            entry.insert(0, str(getattr(self.config, key)))
            entry.grid(row=i, column=1, padx=5, pady=2, sticky="ew")
            self.param_entries[key] = entry
        params_frame.grid_columnconfigure(1, weight=1)

        # --- Mass Defect Filter Frame ---
        mdf_frame = ttk.LabelFrame(self, text="Mass Defect Filter", padding=(10, 5))
        mdf_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(mdf_frame, text="Lower Bound:").grid(
            row=0, column=0, padx=5, pady=2, sticky="w"
        )
        mdf_lower = ttk.Entry(mdf_frame)
        mdf_lower.insert(0, str(getattr(self.config, "mass_defect_lower_bound", -0.11)))
        mdf_lower.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        self.param_entries["mass_defect_lower_bound"] = mdf_lower
        ttk.Label(mdf_frame, text="Upper Bound:").grid(
            row=1, column=0, padx=5, pady=2, sticky="w"
        )
        mdf_upper = ttk.Entry(mdf_frame)
        mdf_upper.insert(0, str(getattr(self.config, "mass_defect_upper_bound", 0.12)))
        mdf_upper.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        self.param_entries["mass_defect_upper_bound"] = mdf_upper

        # --- Blank Subtraction Frame ---
        bs_frame = ttk.LabelFrame(self, text="Blank Subtraction", padding=(10, 5))
        bs_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(bs_frame, text="Method:").grid(
            row=0, column=0, padx=5, pady=2, sticky="w"
        )
        self.bs_method_var = tk.StringVar(value=self.config.blank_subtraction_method)
        bs_combo = ttk.Combobox(
            bs_frame,
            textvariable=self.bs_method_var,
            values=["1", "2"],
            state="readonly",
        )
        bs_combo.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        ttk.Label(bs_frame, text="Std Deviations (for Method 2):").grid(
            row=1, column=0, padx=5, pady=2, sticky="w"
        )
        self.std_dev_entry = ttk.Entry(bs_frame)
        self.std_dev_entry.insert(
            0, str(getattr(self.config, "blank_subtraction_std_dev", 3.0))
        )
        self.std_dev_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        self.param_entries["blank_subtraction_std_dev"] = self.std_dev_entry
        bs_combo.bind("<<ComboboxSelected>>", self._toggle_std_dev_entry)
        self._toggle_std_dev_entry()  # Initial state check

        # --- Regression Analysis Frame ---
        reg_frame = ttk.LabelFrame(self, text="Regression Analysis", padding=(10, 5))
        reg_frame.pack(fill="x", padx=10, pady=5)
        self.rt_reg_var = tk.BooleanVar(
            value=getattr(self.config, "rt_regression_filter", False)
        )
        ttk.Checkbutton(
            reg_frame, text="Apply RT Regression Filter", variable=self.rt_reg_var
        ).pack(anchor="w", padx=5)
        self.ccs_reg_var = tk.BooleanVar(
            value=getattr(self.config, "ccs_regression_filter", True)
        )
        ttk.Checkbutton(
            reg_frame, text="Apply CCS Regression Filter", variable=self.ccs_reg_var
        ).pack(anchor="w", padx=5)

    def _toggle_std_dev_entry(self, event=None):
        """Enables or disables the Std Dev entry based on the combobox."""
        if self.bs_method_var.get() == "2":
            self.std_dev_entry.config(state="normal")
        else:
            self.std_dev_entry.config(state="disabled")

    def update_config(self, config_obj):
        """Updates the main config object with values from this tab."""
        for key, entry in self.param_entries.items():
            setattr(config_obj, key, float(entry.get()))

        config_obj.blank_subtraction_method = self.bs_method_var.get()
        config_obj.rt_regression_filter = self.rt_reg_var.get()
        config_obj.ccs_regression_filter = self.ccs_reg_var.get()
