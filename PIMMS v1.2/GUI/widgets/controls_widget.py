import tkinter as tk
from tkinter import messagebox, ttk


class ControlsWidget(ttk.Frame):
    """A self-contained widget for user input, including file loading and analysis triggers."""

    def __init__(self, parent, load_exp_callback, load_lib_callback, analyze_callback):
        super().__init__(parent)

        self.load_exp_callback = load_exp_callback
        self.load_lib_callback = load_lib_callback
        self.analyze_callback = analyze_callback

        self._create_widgets()

    def _create_widgets(self):
        # Frame for file loading controls
        self.file_frame = ttk.Labelframe(self, text="Input Files")
        self.file_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)

        load_exp_btn = ttk.Button(
            self.file_frame,
            text="Load Experimental File...",
            command=self.load_exp_callback,
        )
        load_exp_btn.grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.exp_file_label = ttk.Label(
            self.file_frame, text="No file loaded.", width=40, anchor="w"
        )
        self.exp_file_label.grid(row=0, column=1, sticky="w", padx=5)

        load_lib_btn = ttk.Button(
            self.file_frame, text="Load Library File...", command=self.load_lib_callback
        )
        load_lib_btn.grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.lib_file_label = ttk.Label(
            self.file_frame, text="No file loaded.", width=40, anchor="w"
        )
        self.lib_file_label.grid(row=1, column=1, sticky="w", padx=5)

        # Frame for analysis parameters
        analysis_frame = ttk.Labelframe(self, text="Analysis Parameters")
        analysis_frame.pack(side=tk.LEFT, padx=10, pady=10)

        ttk.Label(analysis_frame, text="Repeating Unit:").pack(side=tk.LEFT, padx=5)
        self.unit_entry = ttk.Entry(analysis_frame, width=20)
        self.unit_entry.insert(0, "CF2:49.9968")
        self.unit_entry.pack(side=tk.LEFT, padx=5)

        # Run Button
        run_btn = ttk.Button(
            self,
            text="Run Full Analysis",
            command=self.analyze_callback,
            style="Accent.TButton",
        )
        run_btn.pack(side=tk.RIGHT, padx=10, pady=10)

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
        self.exp_file_label.config(text=text)

    def set_lib_file_label(self, text):
        self.lib_file_label.config(text=text)
