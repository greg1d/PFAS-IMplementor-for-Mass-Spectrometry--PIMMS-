# gui/tabs/params_tab.py

import tkinter as tk
from tkinter import ttk

# --- NEW: Import the Tooltip class ---
from ..widgets.tooltip import Tooltip


class ParamsTab(ttk.Frame):
    def __init__(self, parent, config, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.config = config
        self.param_entries = {}
        self._create_widgets()

    def _create_widgets(self):
        """Creates all widgets for the parameters tab."""

        # --- NEW: Define all help texts for this tab ---
        help_texts = {
            "tolerances": {
                "mass_error_ppm": "Maximum allowed mass error in parts-per-million (ppm) between a measured feature and a library compound for a potential match.",
                "ccs_tolerance": "Maximum allowed percentage difference (%) between a feature's Collisional Cross-Section (CCS) and a library value.",
                "rt_tolerance": "Maximum allowed absolute difference in minutes for retention time (RT) for a match.",
                "min_intensity": "The absolute intensity threshold. Any feature with an intensity below this value will be excluded from the analysis. \nN.B. feature extraction softwares often report lower intensities than those observed in spectral data viewers such as Skyline and IMBrowser.",
                "rt_min": "The minimum retention time to consider for feature analysis. Features appearing before this time will be excluded from analysis.",
                "rt_max": "The maximum retention time to consider for feature analysis. Features appearing after this time will be excluded from analysis.",
            },
            "mass_defect": {
                "lower_bound": "The lower bound for the mass defect filter.",
                "upper_bound": "The upper bound for the mass defect filter.",
            },
            "blank_subtraction": {
                "method": "Method 1: Experimental samples are subtracted by the highest intensity seen in the control sample range. \nMethod 2: Experimental samples are subtracted by the average intensity in the control sample range plus a number of standard deviations (see below).",
                "std_dev": "For Method 2 only. A feature's intensity must be this many standard deviations above the blank's average intensity to be kept.",
            },
            "regression": {
                "rt_filter": "If checked, applies a regression model built from the Level 2 library provided. The model creates 5th - 95th percentile bounds for retention time with respect to m/z excluding any features that fall outside these bounds.",
                "ccs_filter": "If checked, applies a regression model built from the Level 2 library provided. The model creates 5th - 95th percentile bounds for Collisional Cross-Section (CCS) with respect to m/z excluding any features that fall outside these bounds.",
            },
        }

        # --- Tolerances and Filters Frame ---
        params_frame = ttk.LabelFrame(
            self, text="Tolerances and Filters", padding=(10, 5)
        )
        params_frame.pack(fill="x", padx=10, pady=5)
        params = {
            "Mass Error (ppm)": "mass_error_ppm",
            "CCS Tolerance (%)": "ccs_tolerance",
            "RT Tolerance (min)": "rt_tolerance",
            "Minimum Intensity": "min_intensity",
            "Minimum RT": "rt_min",
            "Maximum RT": "rt_max",
        }
        for i, (text, key) in enumerate(params.items()):
            ttk.Label(params_frame, text=text + ":").grid(
                row=i, column=0, padx=5, pady=2, sticky="w"
            )
            entry = ttk.Entry(params_frame)
            entry.insert(0, str(getattr(self.config, key)))
            entry.grid(row=i, column=1, padx=5, pady=2, sticky="ew")
            self.param_entries[key] = entry

            # --- NEW: Add help icon ---
            help_label = ttk.Label(params_frame, text=" (?) ", cursor="question_arrow")
            help_label.grid(row=i, column=2, padx=(0, 5), pady=2, sticky="w")
            Tooltip(help_label, text=help_texts["tolerances"].get(key, "No details."))

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
        # --- NEW: Add help icon ---
        help_lower = ttk.Label(mdf_frame, text=" (?) ", cursor="question_arrow")
        help_lower.grid(row=0, column=2, padx=(0, 5), pady=2, sticky="w")
        Tooltip(help_lower, text=help_texts["mass_defect"]["lower_bound"])

        ttk.Label(mdf_frame, text="Upper Bound:").grid(
            row=1, column=0, padx=5, pady=2, sticky="w"
        )
        mdf_upper = ttk.Entry(mdf_frame)
        mdf_upper.insert(0, str(getattr(self.config, "mass_defect_upper_bound", 0.12)))
        mdf_upper.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        self.param_entries["mass_defect_upper_bound"] = mdf_upper
        # --- NEW: Add help icon ---
        help_upper = ttk.Label(mdf_frame, text=" (?) ", cursor="question_arrow")
        help_upper.grid(row=1, column=2, padx=(0, 5), pady=2, sticky="w")
        Tooltip(help_upper, text=help_texts["mass_defect"]["upper_bound"])

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
        # --- NEW: Add help icon ---
        help_method = ttk.Label(bs_frame, text=" (?) ", cursor="question_arrow")
        help_method.grid(row=0, column=2, padx=(0, 5), pady=2, sticky="w")
        Tooltip(help_method, text=help_texts["blank_subtraction"]["method"])

        ttk.Label(bs_frame, text="Std Deviations (for Method 2):").grid(
            row=1, column=0, padx=5, pady=2, sticky="w"
        )
        self.std_dev_entry = ttk.Entry(bs_frame)
        self.std_dev_entry.insert(
            0, str(getattr(self.config, "blank_subtraction_std_dev", 3.0))
        )
        self.std_dev_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        self.param_entries["blank_subtraction_std_dev"] = self.std_dev_entry
        # --- NEW: Add help icon ---
        help_std = ttk.Label(bs_frame, text=" (?) ", cursor="question_arrow")
        help_std.grid(row=1, column=2, padx=(0, 5), pady=2, sticky="w")
        Tooltip(help_std, text=help_texts["blank_subtraction"]["std_dev"])

        bs_combo.bind("<<ComboboxSelected>>", self._toggle_std_dev_entry)
        self._toggle_std_dev_entry()

        # --- Regression Analysis Frame ---
        reg_frame = ttk.LabelFrame(self, text="Regression Analysis", padding=(10, 5))
        reg_frame.pack(fill="x", padx=10, pady=5)

        # --- MODIFIED: Create sub-frames for layout ---
        rt_reg_line = ttk.Frame(reg_frame)
        rt_reg_line.pack(fill="x", anchor="w", padx=5)

        self.rt_reg_var = tk.BooleanVar(
            value=getattr(self.config, "rt_regression_filter", False)
        )
        ttk.Checkbutton(
            rt_reg_line, text="Apply RT Regression Filter", variable=self.rt_reg_var
        ).pack(side="left")
        help_rt_reg = ttk.Label(rt_reg_line, text=" (?) ", cursor="question_arrow")
        help_rt_reg.pack(side="left")
        Tooltip(help_rt_reg, text=help_texts["regression"]["rt_filter"])

        ccs_reg_line = ttk.Frame(reg_frame)
        ccs_reg_line.pack(fill="x", anchor="w", padx=5)

        self.ccs_reg_var = tk.BooleanVar(
            value=getattr(self.config, "ccs_regression_filter", True)
        )
        ttk.Checkbutton(
            ccs_reg_line, text="Apply CCS Regression Filter", variable=self.ccs_reg_var
        ).pack(side="left")
        help_ccs_reg = ttk.Label(ccs_reg_line, text=" (?) ", cursor="question_arrow")
        help_ccs_reg.pack(side="left")
        Tooltip(help_ccs_reg, text=help_texts["regression"]["ccs_filter"])

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
