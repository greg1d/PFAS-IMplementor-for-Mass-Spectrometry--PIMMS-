# gui/tabs/params_tab.py

import tkinter as tk
from tkinter import ttk

# --- Import the Tooltip class ---
from ..widgets.tooltip import Tooltip


class ParamsTab(ttk.Frame):
    def __init__(self, parent, config, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.config = config
        self.param_entries = {}
        self._create_widgets()

    def _create_widgets(self):
        """Creates all widgets for the parameters tab."""

        # --- Define all help texts for this tab ---
        help_texts = {
            "tolerances": {
                "mass_error_ppm": "Maximum allowed mass error in parts-per-million (ppm) between a measured feature and a library compound for a potential match.",
                "ccs_tolerance": "Maximum allowed percentage difference (%) between a feature's Collisional Cross-Section (CCS) and a library value.",
                "rt_tolerance": "Maximum allowed absolute difference in minutes for retention time (RT) for a match.",
                "min_intensity": "The absolute intensity threshold. Any feature with an intensity below this value will be excluded from the analysis. \nN.B. feature extraction softwares often report lower intensities than those observed in spectral data viewers such as Skyline and IMBrowser.",
                "rt_min": "The minimum retention time to consider for feature analysis. Features appearing before this time will be excluded from analysis.",
                "rt_max": "The maximum retention time to consider for feature analysis. Features appearing after this time will be excluded from analysis.",
                "frequency_threshold": "The minimum percentage (%) of experimental samples a feature must be detected in to be kept. For example, 15.0 means a feature is removed if it appears in less than 15% of samples.",
                "mz_min": "The minimum m/z to consider for feature analysis. Features with m/z below this value will be excluded.",
                "mz_max": "The maximum m/z to consider for feature analysis. Features with m/z above this value will be excluded.",
            },
            "mass_defect": {
                "lower_bound": "The lower bound for the mass defect filter. Auto-set by presets, or manually editable in Custom mode.",
                "upper_bound": "The upper bound for the mass defect filter. Auto-set by presets, or manually editable in Custom mode.",
            },
            "blank_subtraction": {
                "method": "Method 1: Experimental samples are subtracted by the highest intensity seen in the control sample range. \nMethod 2: Experimental samples are subtracted by the average intensity in the control sample range plus a number of standard deviations (see below).",
                "std_dev": "For Method 2 only. A feature's intensity must be this many standard deviations above the blank's average intensity to be kept.",
            },
            "regression": {
                "rt_filter": "If checked, applies a regression model built from the Level 2 library provided. The model creates 5th - 95th percentile bounds for retention time with respect to m/z excluding any features that fall outside these bounds.",
                "ccs_filter": "If checked, applies a regression model built from the Level 2 library provided. The model creates 5th - 95th percentile bounds for Collisional Cross-Section (CCS) with respect to m/z excluding any features that fall outside these bounds.",
            },
            "scoring": {
                "rt_scoring": "If checked, Retention Time (RT) will be used as a factor in the Level 2 library matching score. This can improve accuracy if your chromatography is consistent."
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
            "Detection Frequency (%)": "frequency_threshold",
            "Minimum m/z": "mz_min",
            "Maximum m/z": "mz_max",
        }
        for i, (text, key) in enumerate(params.items()):
            ttk.Label(params_frame, text=text + ":").grid(
                row=i, column=0, padx=5, pady=2, sticky="w"
            )
            entry = ttk.Entry(params_frame)
            entry.insert(0, str(getattr(self.config, key)))
            entry.grid(row=i, column=1, padx=5, pady=2, sticky="ew")
            self.param_entries[key] = entry

            # --- Add help icon ---
            help_label = ttk.Label(params_frame, text=" (?) ", cursor="question_arrow")
            help_label.grid(row=i, column=2, padx=(0, 5), pady=2, sticky="w")
            Tooltip(help_label, text=help_texts["tolerances"].get(key, "No details."))

        params_frame.grid_columnconfigure(1, weight=1)

        # --- Mass Defect Filter Frame ---
        mdf_frame = ttk.LabelFrame(self, text="Mass Defect Filter", padding=(10, 5))
        mdf_frame.pack(fill="x", padx=10, pady=5)

        # Get current values to determine initial radio button state
        curr_lower = getattr(self.config, "mass_defect_lower_bound", -0.194)
        curr_upper = getattr(self.config, "mass_defect_upper_bound", 0.09)

        # Determine initial mode based on values
        if abs(curr_lower - (-0.09)) < 0.001 and abs(curr_upper - 0.10) < 0.001:
            init_mode = "pfas"
        elif abs(curr_lower - (-0.12)) < 0.001 and abs(curr_upper - 0.09) < 0.001:
            init_mode = "halogen"
        else:
            init_mode = "custom"

        self.mdf_mode_var = tk.StringVar(value=init_mode)

        # Radio Options
        ttk.Radiobutton(
            mdf_frame,
            text="PFAS Only (-0.075 to 0.102)",
            variable=self.mdf_mode_var,
            value="pfas",
            command=self._update_mdf_entries,
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=5)

        ttk.Radiobutton(
            mdf_frame,
            text="PFAS + Halogenoalkane (-0.194 to 0.09)",
            variable=self.mdf_mode_var,
            value="halogen",
            command=self._update_mdf_entries,
        ).grid(row=1, column=0, columnspan=3, sticky="w", padx=5)

        ttk.Radiobutton(
            mdf_frame,
            text="Custom Range",
            variable=self.mdf_mode_var,
            value="custom",
            command=self._update_mdf_entries,
        ).grid(row=2, column=0, columnspan=3, sticky="w", padx=5)

        # Custom Entry Fields (Indented)
        ttk.Label(mdf_frame, text="Lower Bound:").grid(
            row=3, column=0, padx=(25, 5), pady=2, sticky="w"
        )
        mdf_lower = ttk.Entry(mdf_frame, width=15)
        mdf_lower.insert(0, str(curr_lower))
        mdf_lower.grid(row=3, column=1, padx=5, pady=2, sticky="w")
        self.param_entries["mass_defect_lower_bound"] = mdf_lower

        help_lower = ttk.Label(mdf_frame, text=" (?) ", cursor="question_arrow")
        help_lower.grid(row=3, column=2, padx=(0, 5), pady=2, sticky="w")
        Tooltip(help_lower, text=help_texts["mass_defect"]["lower_bound"])

        ttk.Label(mdf_frame, text="Upper Bound:").grid(
            row=4, column=0, padx=(25, 5), pady=2, sticky="w"
        )
        mdf_upper = ttk.Entry(mdf_frame, width=15)
        mdf_upper.insert(0, str(curr_upper))
        mdf_upper.grid(row=4, column=1, padx=5, pady=2, sticky="w")
        self.param_entries["mass_defect_upper_bound"] = mdf_upper

        help_upper = ttk.Label(mdf_frame, text=" (?) ", cursor="question_arrow")
        help_upper.grid(row=4, column=2, padx=(0, 5), pady=2, sticky="w")
        Tooltip(help_upper, text=help_texts["mass_defect"]["upper_bound"])

        # Trigger update to set initial state (disable/enable entries)
        self._update_mdf_entries()

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

        help_std = ttk.Label(bs_frame, text=" (?) ", cursor="question_arrow")
        help_std.grid(row=1, column=2, padx=(0, 5), pady=2, sticky="w")
        Tooltip(help_std, text=help_texts["blank_subtraction"]["std_dev"])

        bs_combo.bind("<<ComboboxSelected>>", self._toggle_std_dev_entry)
        self._toggle_std_dev_entry()

        # --- Regression Analysis Frame ---
        reg_frame = ttk.LabelFrame(self, text="Regression Analysis", padding=(10, 5))
        reg_frame.pack(fill="x", padx=10, pady=5)

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

        # --- Scoring Options Frame ---
        scoring_frame = ttk.LabelFrame(self, text="Scoring Options", padding=(10, 5))
        scoring_frame.pack(fill="x", padx=10, pady=5)

        rt_scoring_line = ttk.Frame(scoring_frame)
        rt_scoring_line.pack(fill="x", anchor="w", padx=5)

        self.rt_scoring_var = tk.BooleanVar(
            value=getattr(self.config, "include_rt_scoring", False)
        )
        ttk.Checkbutton(
            rt_scoring_line,
            text="Include Retention Time in Scoring",
            variable=self.rt_scoring_var,
        ).pack(side="left")
        help_rt_scoring = ttk.Label(
            rt_scoring_line, text=" (?) ", cursor="question_arrow"
        )
        help_rt_scoring.pack(side="left")
        Tooltip(help_rt_scoring, text=help_texts["scoring"]["rt_scoring"])

    def _update_mdf_entries(self, initial_setup=False):
        """Updates the Mass Defect entries based on the selected Radiobutton mode."""
        mode = self.mdf_mode_var.get()
        entry_lower = self.param_entries["mass_defect_lower_bound"]
        entry_upper = self.param_entries["mass_defect_upper_bound"]

        # Temporarily enable to allow updating the text
        entry_lower.config(state="normal")
        entry_upper.config(state="normal")

        if mode == "custom":
            # If switching to Custom (and not just initializing), apply requested defaults
            # This ensures the user starts with -0.12/0.11 if they switch to Custom
            if not initial_setup:
                entry_lower.delete(0, tk.END)
                entry_lower.insert(0, "-0.12")
                entry_upper.delete(0, tk.END)
                entry_upper.insert(0, "0.11")
            # Leave enabled for editing

        else:
            # If a preset is selected, we show the Custom Defaults as placeholders
            # (per your request to show -0.12/0.11 instead of the preset values)
            entry_lower.delete(0, tk.END)
            entry_lower.insert(0, "-0.12")
            entry_upper.delete(0, tk.END)
            entry_upper.insert(0, "0.11")

            # Disable user editing
            entry_lower.config(state="disabled")
            entry_upper.config(state="disabled")

    def _toggle_std_dev_entry(self, event=None):
        """Enables or disables the Std Dev entry based on the combobox."""
        if self.bs_method_var.get() == "2":
            self.std_dev_entry.config(state="normal")
        else:
            self.std_dev_entry.config(state="disabled")

    def update_config(self, config_obj):
        """Updates the main config object with values from this tab."""
        # 1. Update standard parameters
        for key, entry in self.param_entries.items():
            # Skip Mass Defect keys here; they are handled separately below
            if key in ["mass_defect_lower_bound", "mass_defect_upper_bound"]:
                continue
            setattr(config_obj, key, float(entry.get()))

        # 2. Update Mass Defect parameters based on Radio Button logic
        # We must use hardcoded values for presets because the UI boxes
        # now display the placeholder values (-0.12/0.11) instead of real data.
        mode = self.mdf_mode_var.get()

        if mode == "pfas":
            config_obj.mass_defect_lower_bound = -0.075
            config_obj.mass_defect_upper_bound = 0.102
        elif mode == "halogen":
            config_obj.mass_defect_lower_bound = -0.194
            config_obj.mass_defect_upper_bound = 0.090
        else:
            # Custom mode: We trust the values in the text boxes
            config_obj.mass_defect_lower_bound = float(
                self.param_entries["mass_defect_lower_bound"].get()
            )
            config_obj.mass_defect_upper_bound = float(
                self.param_entries["mass_defect_upper_bound"].get()
            )

        # 3. Update boolean/choice parameters
        config_obj.blank_subtraction_method = self.bs_method_var.get()
        config_obj.rt_regression_filter = self.rt_reg_var.get()
        config_obj.ccs_regression_filter = self.ccs_reg_var.get()
        config_obj.include_rt_scoring = self.rt_scoring_var.get()
