import tkinter as tk
from tkinter import messagebox, ttk


class ControlsWidget(ttk.Labelframe):
    """A self-contained widget for user input controls, using a Combobox for repeating units."""

    def __init__(
        self, parent, config, load_exp_callback, load_lib_callback, analyze_callback
    ):
        super().__init__(parent, text="Workflow Controls")

        self.config = config  # Store the configuration object
        self.load_exp_callback = load_exp_callback
        self.load_lib_callback = load_lib_callback
        self.analyze_callback = analyze_callback

        self._create_widgets()

    def _create_widgets(self):
        """Creates and arranges all the widgets inside the labelframe."""
        # Configure the grid layout for the main frame
        self.columnconfigure(0, weight=1)  # File selection area will expand
        self.columnconfigure(1, weight=0)  # Parameters area is fixed size
        self.columnconfigure(2, weight=0)  # Run button is fixed size

        # --- Column 0: File Loading ---
        file_frame = ttk.Frame(self)
        file_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        # Experimental File Widgets
        load_exp_btn = ttk.Button(
            file_frame, text="Load Experimental File...", command=self.load_exp_callback
        )
        load_exp_btn.grid(row=0, column=0, sticky="w", pady=(5, 2))
        self.exp_file_label = ttk.Label(
            file_frame, text="No file loaded.", width=40, anchor="w"
        )
        self.exp_file_label.grid(row=0, column=1, sticky="w", padx=5, pady=(5, 2))

        # Library File Widgets
        load_lib_btn = ttk.Button(
            file_frame, text="Load Library File...", command=self.load_lib_callback
        )
        load_lib_btn.grid(row=1, column=0, sticky="w", pady=(2, 5))
        self.lib_file_label = ttk.Label(
            file_frame, text="No file loaded.", width=40, anchor="w"
        )
        self.lib_file_label.grid(row=1, column=1, sticky="w", padx=5, pady=(2, 5))

        # --- Column 1: Analysis Parameters ---
        analysis_frame = ttk.Frame(self)
        analysis_frame.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="ns")

        ttk.Label(analysis_frame, text="Repeating Unit:").pack(
            side=tk.LEFT, padx=(5, 0)
        )

        # Create a Combobox (dropdown) instead of a text Entry
        self.unit_selector = ttk.Combobox(analysis_frame, state="readonly", width=15)

        # Populate the dropdown with the names (keys) from the loaded config
        unit_names = list(self.config.repeating_units.keys())
        self.unit_selector["values"] = unit_names

        if unit_names:
            self.unit_selector.current(0)  # Select the first item by default

        self.unit_selector.pack(side=tk.LEFT, padx=5)

        # --- Column 2: Run Button ---
        run_btn = ttk.Button(
            self,
            text="Run Full Analysis",
            command=self.analyze_callback,
            style="Accent.TButton",
        )
        run_btn.grid(row=0, column=2, padx=10, pady=10, sticky="e")

    def get_repeating_units(self):
        """Gets the selected unit name and returns its {name: mass} dictionary."""
        selected_name = self.unit_selector.get()
        if not selected_name:
            messagebox.showerror(
                "Invalid Selection", "Please select a repeating unit from the dropdown."
            )
            return None

        # Look up the mass from the config object
        mass = self.config.repeating_units.get(selected_name)

        return {selected_name: mass}

    def set_exp_file_label(self, text):
        """Updates the label for the experimental file."""
        self.exp_file_label.config(text=text)

    def set_lib_file_label(self, text):
        """Updates the label for the library file."""
        self.lib_file_label.config(text=text)
