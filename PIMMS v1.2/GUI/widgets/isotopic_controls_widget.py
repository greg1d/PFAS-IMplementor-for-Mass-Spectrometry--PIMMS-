# In GUI/widgets/isotopic_controls_widget.py

import tkinter as tk
from tkinter import ttk, messagebox


class IsotopicControlsWidget(ttk.Labelframe):
    """
    A dedicated widget for handling all user inputs for the Isotopic Analysis workflow.
    """

    def __init__(
        self, parent, load_pimms_callback, load_cef_callback, analyze_callback
    ):
        super().__init__(parent, text="Configuration", padding="10")

        # Store callbacks provided by the parent tab
        self.load_pimms_callback = load_pimms_callback
        self.load_cef_callback = load_cef_callback
        self.analyze_callback = analyze_callback

        # --- Create StringVars to hold widget states ---
        self.smoothing_sigma = tk.StringVar(value="2.0")
        self.mask_dilation = tk.StringVar(value="5")
        self.contour_levels = tk.StringVar(value="0.8, 1.0, 1.5, 2.0, 2.5, 3.0")

        self._create_widgets()

    def _create_widgets(self):
        # --- File Input Section ---
        file_frame = ttk.Frame(self)
        file_frame.pack(fill=tk.X, expand=True, pady=(0, 10))

        pimms_button = ttk.Button(
            file_frame, text="Load PIMMS File...", command=self.load_pimms_callback
        )
        pimms_button.grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.pimms_label = ttk.Label(
            file_frame, text="No PIMMS file selected.", style="Italic.TLabel"
        )
        self.pimms_label.grid(row=0, column=1, sticky="w")

        cef_button = ttk.Button(
            file_frame, text="Load CEF Folder...", command=self.load_cef_callback
        )
        cef_button.grid(row=1, column=0, pady=(5, 0), padx=(0, 5), sticky="w")
        self.cef_label = ttk.Label(
            file_frame, text="No CEF folder selected.", style="Italic.TLabel"
        )
        self.cef_label.grid(row=1, column=1, pady=(5, 0), sticky="w")

        # --- Parameters Section ---
        params_frame = ttk.Frame(self)
        params_frame.pack(fill=tk.X, expand=True, pady=5)
        params_frame.columnconfigure(1, weight=1)

        ttk.Label(params_frame, text="Smoothing Sigma:").grid(
            row=0, column=0, sticky="w", padx=(0, 5)
        )
        ttk.Entry(params_frame, textvariable=self.smoothing_sigma).grid(
            row=0, column=1, sticky="ew"
        )

        ttk.Label(params_frame, text="Mask Dilation:").grid(
            row=1, column=0, sticky="w", padx=(0, 5), pady=2
        )
        ttk.Entry(params_frame, textvariable=self.mask_dilation).grid(
            row=1, column=1, sticky="ew"
        )

        ttk.Label(params_frame, text="Contour Levels (csv):").grid(
            row=2, column=0, sticky="w", padx=(0, 5), pady=2
        )
        ttk.Entry(params_frame, textvariable=self.contour_levels).grid(
            row=2, column=1, sticky="ew"
        )

        # --- Action Button ---
        self.run_button = ttk.Button(
            self,
            text="Run Full Analysis Pipeline",
            command=self.analyze_callback,
            state="disabled",
        )
        self.run_button.pack(pady=10)

    def get_parameters(self):
        """
        Retrieves and validates all parameters from the widgets.
        Returns a dictionary of parameters or None if validation fails.
        """
        try:
            params = {
                "smoothing_sigma": float(self.smoothing_sigma.get()),
                "mask_dilation": int(self.mask_dilation.get()),
                "contour_levels": [
                    float(x.strip()) for x in self.contour_levels.get().split(",")
                ],
            }
            if not params["contour_levels"]:
                raise ValueError("Contour Levels cannot be empty.")
            return params
        except ValueError as e:
            messagebox.showerror(
                "Invalid Parameter", f"Please check your input parameters.\nError: {e}"
            )
            return None

    # --- Public methods for the parent tab to update labels ---
    def set_pimms_file_label(self, filename):
        self.pimms_label.config(text=filename)

    def set_cef_folder_label(self, foldername):
        self.cef_label.config(text=foldername)

    def set_run_button_state(self, state):
        self.run_button.config(state=state)
