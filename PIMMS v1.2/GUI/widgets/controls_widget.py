import tkinter as tk
from tkinter import messagebox, ttk


class ControlsWidget(ttk.Labelframe):
    """A self-contained widget for user input controls, handling multiple file inputs."""

    def __init__(self, parent, load_exp_callback, load_lib_callback, analyze_callback):
        super().__init__(parent, text="Workflow Controls")

        # Callbacks are functions passed in from the parent (the VisualizationsTab)
        self.load_exp_callback = load_exp_callback
        self.load_lib_callback = load_lib_callback
        self.analyze_callback = analyze_callback

        self._create_widgets()

    def _create_widgets(self):
        # A frame to hold all the file loading controls for better organization
        file_frame = ttk.Frame(self)
        file_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.columnconfigure(0, weight=1)  # Allow file_frame to expand

        # --- Experimental File Widgets ---
        load_exp_btn = ttk.Button(
            file_frame, text="Load Experimental File...", command=self.load_exp_callback
        )
        load_exp_btn.grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.exp_file_label = ttk.Label(
            file_frame, text="No file loaded.", width=40, anchor="w"
        )
        self.exp_file_label.grid(row=0, column=1, sticky="w", padx=5, pady=(0, 5))

        # --- Library File Widgets ---
        load_lib_btn = ttk.Button(
            file_frame, text="Load Library File...", command=self.load_lib_callback
        )
        load_lib_btn.grid(row=1, column=0, sticky="w")

        self.lib_file_label = ttk.Label(
            file_frame, text="No file loaded.", width=40, anchor="w"
        )
        self.lib_file_label.grid(row=1, column=1, sticky="w", padx=5)

        # --- Analysis Parameter Widgets ---
        analysis_frame = ttk.Frame(self)
        analysis_frame.grid(row=0, column=1, padx=20, pady=10)

        ttk.Label(analysis_frame, text="Repeating Unit:").pack(side=tk.LEFT)
        self.unit_entry = ttk.Entry(analysis_frame, width=20)
        self.unit_entry.insert(0, "CF2:49.9968")
        self.unit_entry.pack(side=tk.LEFT, padx=5)

        # --- Run Button ---
        self.reanalyze_btn = ttk.Button(
            self, text="Run Full Analysis", command=self.analyze_callback
        )
        self.reanalyze_btn.grid(row=0, column=2, padx=10, pady=10, sticky="e")

    def get_repeating_units(self):
        """Parses the text from the entry box into a dictionary."""
        try:
            text = self.unit_entry.get()
            if not text:
                return {}
            name, mass = text.split(":")
            return {name.strip(): float(mass)}
        except Exception:
            messagebox.showerror(
                "Invalid Format", "Repeating unit must be 'Name:Mass'."
            )
            return None

    def set_exp_file_label(self, text):
        """Updates the label for the experimental file."""
        self.exp_file_label.config(text=text)

    def set_lib_file_label(self, text):
        """Updates the label for the library file."""
        self.lib_file_label.config(text=text)
